"""
Mykare Health voice agent — LiveKit Agents 1.5.x
Fixes:
  1. SYSTEM_PROMPT wrapped in Instructions() to prevent chat_context serializer crash
  2. Transcript events broadcast to frontend via LiveKit data channel (topic="transcript")
"""
from __future__ import annotations

import inspect
import json
import uuid
from datetime import datetime

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli
from livekit.agents import llm as lk_llm
from livekit.agents.llm.chat_context import Instructions
from livekit.plugins import silero
from sqlalchemy import select

from app.config import settings
from app.db.database import AsyncSessionLocal, init_db
from app.db.models import Session as DBSession
from app.services.llm_service import create_llm
from app.services.stt_service import create_stt
from app.services.tts_service import create_tts
from app.tools.appointment_tools import HealthcareTools
from app.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


SYSTEM_PROMPT = Instructions("""You are Aria, a warm, professional healthcare front-desk AI assistant for Mykare Health.

YOUR RESPONSIBILITIES:
1. Greet patients and identify them using their phone number (ALWAYS do this first)
2. If the patient is new (identify_user returns found=false), ask for their name and call register_patient
3. Help patients book, view, modify, or cancel appointments
4. Answer questions about available appointment slots (call fetch_slots)
5. Confirm all details before taking action
6. When the patient is done, call end_conversation to generate the summary

BEHAVIOUR RULES:
- Keep responses concise (2-3 sentences max)
- Always confirm appointment date and time before booking
- Never book without patient identity confirmed
- Be empathetic, professional, and patient-focused
- If a patient is confused, gently guide them

CONVERSATION FLOW:
1. Greet -> 2. Identify (phone) -> 3. Register if new -> 4. Handle request -> 5. Confirm -> 6. End
""")

GREETING = (
    "Hello! Welcome to Mykare Health. I'm Aria, your virtual front-desk assistant. "
    "Could I please have your 10-digit phone number to get started?"
)


async def _broadcast(room, role: str, text: str) -> None:
    """Send a transcript line to the frontend via LiveKit data channel."""
    if not room or not text.strip():
        return
    try:
        payload = json.dumps({
            "type": "transcript",
            "role": role,
            "text": text.strip(),
            "ts": datetime.utcnow().isoformat(),
        }).encode()
        await room.local_participant.publish_data(
            payload, reliable=True, topic="transcript"
        )
    except Exception as exc:
        logger.warning("transcript_broadcast_failed", error=str(exc))


class MykareVoiceAgent(Agent):
    def __init__(self, tools: list[lk_llm.Tool], room) -> None:
        super().__init__(instructions=SYSTEM_PROMPT, tools=tools)
        self._room = room

    async def on_enter(self) -> None:
        await self.session.say(
            GREETING,
            allow_interruptions=True,
            add_to_chat_ctx=False,
        )
        # Broadcast greeting to transcript panel
        await _broadcast(self._room, "assistant", GREETING)

    async def on_user_turn_completed(self, turn_ctx, new_message) -> None:
        """Called when the user finishes speaking — broadcast their transcript."""
        try:
            text = new_message.text_content or ""
            if text:
                await _broadcast(self._room, "user", text)
        except Exception as exc:
            logger.warning("user_transcript_broadcast_failed", error=str(exc))

    async def on_agent_turn_completed(self, turn_ctx, new_message) -> None:
        """Called when the agent finishes responding — broadcast agent transcript."""
        try:
            text = new_message.text_content or ""
            if text:
                await _broadcast(self._room, "assistant", text)
        except Exception as exc:
            logger.warning("agent_transcript_broadcast_failed", error=str(exc))


def _collect_function_tools(tools_obj: object) -> list[lk_llm.Tool]:
    collected: list[lk_llm.Tool] = []
    for _, member in inspect.getmembers(tools_obj):
        if isinstance(member, (lk_llm.FunctionTool, lk_llm.RawFunctionTool)):
            collected.append(member)
    collected.sort(key=lambda t: t.info.name)
    return collected


async def _get_or_create_session_id(room_name: str) -> str:
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(DBSession).where(DBSession.room_name == room_name)
        )
        existing = res.scalar_one_or_none()
        if existing:
            return existing.id
        session_id = str(uuid.uuid4())
        db.add(DBSession(id=session_id, room_name=room_name))
        await db.commit()
        return session_id


async def entrypoint(ctx: JobContext) -> None:
    await init_db()
    room_name  = ctx.room.name if ctx.room else "unknown"
    session_id = await _get_or_create_session_id(room_name)
    logger.info("starting_voice_agent", room=room_name, session_id=session_id)

    await ctx.connect()
    participant = await ctx.wait_for_participant()
    logger.info("participant_joined", participant_identity=participant.identity)

    healthcare_tools = HealthcareTools(session_id=session_id, room=ctx.room)
    function_tools   = _collect_function_tools(healthcare_tools)
    logger.info(
        "healthcare_tools_registered",
        tool_count=len(function_tools),
        tools=[t.info.name for t in function_tools],
    )

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=create_stt(),
        llm=create_llm(),
        tts=create_tts(),
    )

    agent = MykareVoiceAgent(tools=function_tools, room=ctx.room)
    await session.start(agent=agent, room=ctx.room)
    logger.info("agent_session_started", room=room_name, session_id=session_id)


def get_worker_options() -> WorkerOptions:
    return WorkerOptions(
        entrypoint_fnc=entrypoint,
        ws_url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )


if __name__ == "__main__":
    setup_logging(settings.LOG_LEVEL)
    cli.run_app(get_worker_options())