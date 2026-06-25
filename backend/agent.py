import asyncio
import json
import logging
from typing import Optional

import httpx
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    ConversationItemAddedEvent,
    JobContext,
    UserInputTranscribedEvent,
    WorkerOptions,
    cli,
    function_tool,
    llm,
)
from livekit.plugins import deepgram, openai

from config import settings

logger = logging.getLogger("mykare-agent")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

SYSTEM_PROMPT = """You are Maya, a professional and empathetic AI voice receptionist for Mykare Healthcare.
Your role is to help patients book, manage, and cancel medical appointments over the phone.

PERSONALITY:
- Warm, professional, and reassuring
- Speak clearly and concisely - keep each response to 1-2 sentences
- Always confirm details back to the patient (date, time, doctor name)
- Be proactive in offering available time slots

AVAILABLE TOOLS - use them in this exact order for bookings:
1. identify_user - ALWAYS call this first with the patient's phone number
2. fetch_slots - check available times BEFORE booking
3. book_appointment - book only after patient confirms date + time
4. retrieve_appointments - show existing bookings on request
5. cancel_appointment - cancel by appointment ID
6. modify_appointment - reschedule by appointment ID
7. end_conversation - end the call and generate a summary

STRICT BOOKING WORKFLOW:
Step 1: Greet the patient.
Step 2: Ask for their 10-digit phone number.
Step 3: Call identify_user immediately with the number.
Step 4: Ask what they need (book / view / cancel / reschedule).
Step 5: For bookings - call fetch_slots for the requested date, read available slots aloud.
Step 6: Patient picks a slot - call book_appointment.
Step 7: Confirm aloud: "Your appointment is confirmed for [date] at [time] with [doctor]."
Step 8: Ask if there is anything else you can help with.
Step 9: Call end_conversation before saying goodbye.

DATE HANDLING:
- "tomorrow" = the next calendar day. Convert to YYYY-MM-DD before tool calls.
- "next Monday" etc. - compute the actual date before calling tools.

RULES:
- NEVER perform any appointment action before calling identify_user
- NEVER book without first calling fetch_slots for that date
- If a slot is taken, immediately offer 2-3 alternatives from the available list
- Keep spoken responses short and conversational - this is a phone call"""


class HealthcareVoiceAgent(Agent):
    def __init__(self, room: rtc.Room) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self._room = room
        self._client = httpx.AsyncClient(timeout=15.0)
        self._backend = "http://localhost:8000/api/tools"

    async def on_exit(self) -> None:
        await self._client.aclose()

    async def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            resp = await self._client.post(f"{self._backend}/{endpoint}", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error("Backend call /%s failed: %s", endpoint, exc)
            return {"success": False, "error": str(exc)}

    async def _notify_ui(self, tool_name: str, status: str, data: dict) -> None:
        try:
            msg_type = "tool_call" if status == "running" else "tool_result"
            payload = {
                "type": msg_type,
                "tool_name": tool_name,
                "status": status,
            }
            if status == "running":
                payload["args"] = data
            else:
                payload["result"] = data

            # Backward-compatible payload key used by existing UI utilities.
            payload["data"] = data

            await self._room.local_participant.publish_data(
                json.dumps(payload).encode(),
                reliable=True,
            )
        except Exception as exc:
            logger.warning("_notify_ui failed for %s: %s", tool_name, exc)

    @function_tool(
        description=(
            "Identify or create a patient account by their 10-digit phone number. "
            "MUST be called before any appointment action."
        )
    )
    async def identify_user(self, phone_number: str, name: Optional[str] = None) -> str:
        await self._notify_ui("identify_user", "running", {"phone_number": phone_number})
        payload: dict = {"phone_number": phone_number}
        if name:
            payload["name"] = name
        result = await self._post("identify_user", payload)
        status = "completed" if result.get("success") else "error"
        await self._notify_ui("identify_user", status, result)
        return json.dumps(result)

    @function_tool(
        description=(
            "Fetch available appointment time slots for a given date. "
            "Always call this BEFORE booking."
        )
    )
    async def fetch_slots(self, date: str, doctor_name: Optional[str] = None) -> str:
        await self._notify_ui("fetch_slots", "running", {"date": date})
        payload: dict = {"date": date}
        if doctor_name:
            payload["doctor_name"] = doctor_name
        result = await self._post("fetch_slots", payload)
        status = "completed" if result.get("success") else "error"
        await self._notify_ui("fetch_slots", status, result)
        return json.dumps(result)

    @function_tool(
        description=(
            "Book an appointment for the identified patient. "
            "Requires user_id from identify_user and a slot confirmed with the patient."
        )
    )
    async def book_appointment(
        self,
        user_id: int,
        appointment_date: str,
        appointment_time: str,
        doctor_name: str = "Dr. Sarah Johnson",
        department: str = "General",
        reason: Optional[str] = None,
    ) -> str:
        await self._notify_ui(
            "book_appointment",
            "running",
            {
                "date": appointment_date,
                "time": appointment_time,
                "doctor": doctor_name,
            },
        )
        result = await self._post(
            "book_appointment",
            {
                "user_id": user_id,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "doctor_name": doctor_name,
                "department": department,
                "reason": reason,
            },
        )
        status = "completed" if result.get("success") else "error"
        await self._notify_ui("book_appointment", status, result)
        return json.dumps(result)

    @function_tool(description="Retrieve all appointments (upcoming and past) for the patient.")
    async def retrieve_appointments(self, user_id: int) -> str:
        await self._notify_ui("retrieve_appointments", "running", {"user_id": user_id})
        result = await self._post("retrieve_appointments", {"user_id": user_id})
        status = "completed" if result.get("success") else "error"
        await self._notify_ui("retrieve_appointments", status, result)
        return json.dumps(result)

    @function_tool(description="Cancel an existing appointment by its ID.")
    async def cancel_appointment(self, appointment_id: int, user_id: int) -> str:
        await self._notify_ui(
            "cancel_appointment",
            "running",
            {"appointment_id": appointment_id},
        )
        result = await self._post(
            "cancel_appointment",
            {"appointment_id": appointment_id, "user_id": user_id},
        )
        status = "completed" if result.get("success") else "error"
        await self._notify_ui("cancel_appointment", status, result)
        return json.dumps(result)

    @function_tool(description="Reschedule or modify an existing confirmed appointment.")
    async def modify_appointment(
        self,
        appointment_id: int,
        user_id: int,
        new_date: Optional[str] = None,
        new_time: Optional[str] = None,
        new_doctor: Optional[str] = None,
        new_reason: Optional[str] = None,
    ) -> str:
        await self._notify_ui(
            "modify_appointment",
            "running",
            {"appointment_id": appointment_id},
        )
        result = await self._post(
            "modify_appointment",
            {
                "appointment_id": appointment_id,
                "user_id": user_id,
                "new_date": new_date,
                "new_time": new_time,
                "new_doctor": new_doctor,
                "new_reason": new_reason,
            },
        )
        status = "completed" if result.get("success") else "error"
        await self._notify_ui("modify_appointment", status, result)
        return json.dumps(result)

    @function_tool(description="End the call, store a summary, and say goodbye.")
    async def end_conversation(self, summary: str, user_id: Optional[int] = None) -> str:
        await self._notify_ui("end_conversation", "running", {})
        result = await self._post(
            "end_conversation",
            {"summary": summary, "user_id": user_id},
        )
        await self._notify_ui("end_conversation", "completed", result)
        return json.dumps(result)


async def _publish_transcript(room: rtc.Room, role: str, content: str) -> None:
    if not content:
        return
    try:
        payload = json.dumps(
            {
                "type": "transcript",
                "role": role,
                "content": content,
            }
        ).encode()
        await room.local_participant.publish_data(payload, reliable=True)
    except Exception as exc:
        logger.warning("Transcript publish failed: %s", exc)


async def entrypoint(ctx: JobContext) -> None:
    logger.info("Agent connecting to room: %s", ctx.room.name)

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info("Patient participant joined: %s", participant.identity)

    session = AgentSession(
        stt=deepgram.STT(
            api_key=settings.deepgram_api_key,
            model=settings.deepgram_stt_model,
            language="en-US",
            punctuate=True,
        ),
        llm=openai.LLM(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        ),
        tts=deepgram.TTS(
            api_key=settings.deepgram_api_key,
            model=settings.deepgram_tts_model,
        ),
        turn_handling={
            "endpointing": {"min_delay": 0.4, "max_delay": 5.0},
            "interruption": {"enabled": True, "min_duration": 0.6},
        },
    )

    agent = HealthcareVoiceAgent(room=ctx.room)

    def on_user_input_transcribed(ev: UserInputTranscribedEvent) -> None:
        if ev.is_final and ev.transcript:
            asyncio.create_task(_publish_transcript(ctx.room, "user", ev.transcript))

    def on_conversation_item_added(ev: ConversationItemAddedEvent) -> None:
        item = ev.item
        if isinstance(item, llm.ChatMessage) and item.role == "assistant":
            text = item.text_content or ""
            if text:
                asyncio.create_task(_publish_transcript(ctx.room, "assistant", text))

    session.on("user_input_transcribed", on_user_input_transcribed)
    session.on("conversation_item_added", on_conversation_item_added)

    await session.start(agent=agent, room=ctx.room)

    await session.say(
        "Hello, thank you for calling Mykare Healthcare. I'm Maya, your AI assistant. "
        "How can I help you today?",
        allow_interruptions=True,
    )

    await asyncio.sleep(float("inf"))


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
            ws_url=settings.livekit_url,
        )
    )
