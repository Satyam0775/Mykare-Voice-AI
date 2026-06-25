import httpx
import json
import logging
from typing import List, Dict, Optional, Any
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional and empathetic AI voice receptionist for Mykare Healthcare.
Your role is to help patients book, manage, and cancel medical appointments.

PERSONALITY:
- Warm, professional, and reassuring
- Speak clearly and concisely (responses under 2 sentences when possible)
- Always confirm details back to the patient
- Be proactive in offering available slots

CAPABILITIES:
- identify_user: Identify patient by phone number
- fetch_slots: Check available appointment slots
- book_appointment: Book a new appointment
- retrieve_appointments: Show patient's appointments
- cancel_appointment: Cancel an appointment
- modify_appointment: Reschedule or update an appointment
- end_conversation: End the call with a summary

WORKFLOW:
1. Greet the patient warmly
2. Ask for their phone number to identify them
3. Understand what they need
4. Call appropriate tools to fulfill the request
5. Confirm all actions clearly
6. Offer to help with anything else
7. End the conversation graciously

IMPORTANT:
- Always verify phone number before any appointment action
- Never double-book a slot
- State appointment details clearly: date, time, doctor name
- If a slot is taken, immediately suggest alternatives
- Keep conversation natural and flowing"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "identify_user",
            "description": "Identify or create a user by phone number. Call this first before any appointment actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {"type": "string", "description": "Patient's 10-digit phone number"},
                    "name": {"type": "string", "description": "Patient's name if provided"},
                },
                "required": ["phone_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_slots",
            "description": "Fetch available appointment slots for a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "doctor_name": {"type": "string", "description": "Optional doctor name to filter by"},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book an appointment for the identified user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID from identify_user"},
                    "appointment_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "appointment_time": {"type": "string", "description": "Time in HH:MM format (24h)"},
                    "doctor_name": {"type": "string", "description": "Doctor's name"},
                    "department": {"type": "string", "description": "Medical department"},
                    "reason": {"type": "string", "description": "Reason for the appointment"},
                },
                "required": ["user_id", "appointment_date", "appointment_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_appointments",
            "description": "Retrieve all appointments for the identified user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID from identify_user"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID to cancel"},
                    "user_id": {"type": "integer", "description": "User ID for verification"},
                },
                "required": ["appointment_id", "user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "modify_appointment",
            "description": "Modify or reschedule an existing appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "integer", "description": "Appointment ID to modify"},
                    "user_id": {"type": "integer", "description": "User ID for verification"},
                    "new_date": {"type": "string", "description": "New date in YYYY-MM-DD format"},
                    "new_time": {"type": "string", "description": "New time in HH:MM format"},
                    "new_doctor": {"type": "string", "description": "New doctor name"},
                    "new_reason": {"type": "string", "description": "Updated reason"},
                },
                "required": ["appointment_id", "user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "End the conversation and provide a summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID"},
                    "summary": {"type": "string", "description": "Brief summary of the conversation"},
                },
                "required": ["summary"],
            },
        },
    },
]


class LLMService:
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mykare.ai",
            "X-Title": "Mykare Voice AI",
        }

    async def chat(
        self,
        messages: List[Dict],
        tools: bool = True,
        temperature: float = 0.7,
    ) -> Dict:
        """Send a chat request to OpenRouter."""
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "temperature": temperature,
            "max_tokens": 512,
        }
        if tools:
            payload["tools"] = TOOLS_SCHEMA
            payload["tool_choice"] = "auto"

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise

    async def generate_summary(self, conversation: List[Dict], appointments: List[Dict]) -> str:
        """Generate a call summary from the conversation history."""
        conversation_text = "\n".join(
            [f"{m['role'].upper()}: {m.get('content', '')}" for m in conversation if m.get("content")]
        )
        appointments_text = json.dumps(appointments, indent=2) if appointments else "None"

        summary_prompt = f"""Generate a concise call summary for this healthcare conversation.

CONVERSATION:
{conversation_text}

APPOINTMENTS MADE/MODIFIED:
{appointments_text}

Provide a JSON summary with:
- summary: 2-3 sentence overview
- appointments: list of appointment details
- user_preferences: any preferences mentioned
- timestamp: current ISO timestamp
- key_points: bullet list of key actions taken

Return ONLY valid JSON."""

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json={
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": summary_prompt}],
                    "temperature": 0.3,
                    "max_tokens": 600,
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return content
        except Exception as e:
            logger.error(f"Summary generation error: {e}")
            return json.dumps({
                "summary": "Call completed. Appointment actions were taken as requested.",
                "appointments": appointments,
                "user_preferences": [],
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                "key_points": ["Voice call completed"],
            })

    async def close(self):
        await self.client.aclose()
