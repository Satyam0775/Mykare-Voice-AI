"""
Healthcare appointment tools — all 7 required actions.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Annotated, Optional

from livekit.agents import function_tool
from sqlalchemy import and_, select

from app.db.database import AsyncSessionLocal
from app.db.models import Appointment, Session, ToolEvent, User
from app.utils.logger import get_logger

logger = get_logger(__name__)

AVAILABLE_SLOTS: dict[str, list[str]] = {
    "2025-01-20": ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM", "04:00 PM"],
    "2025-01-21": ["09:30 AM", "10:30 AM", "01:00 PM", "02:30 PM", "04:30 PM"],
    "2025-01-22": ["09:00 AM", "11:30 AM", "01:30 PM", "03:00 PM", "04:00 PM"],
    "2025-01-23": ["10:00 AM", "11:00 AM", "02:00 PM", "03:30 PM"],
    "2025-01-24": ["09:00 AM", "10:30 AM", "01:00 PM", "02:00 PM", "04:00 PM"],
    "2025-01-27": ["09:30 AM", "10:30 AM", "11:30 AM", "02:30 PM", "04:30 PM"],
    "2025-01-28": ["09:00 AM", "10:00 AM", "01:00 PM", "03:00 PM", "04:00 PM"],
}

# ── Phone number normalizer ──────────────────────────────────────────────────
_WORD_TO_DIGIT = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "oh": "0", "o": "0",
}

def normalize_phone(raw: str) -> str:
    """
    Convert spoken phone numbers to digit strings.
    'seven three one nine nine seven one four two six' -> '7319971426'
    '731 997 1426' -> '7319971426'
    """
    # Replace word numbers with digits
    tokens = raw.lower().strip().split()
    digits = []
    for token in tokens:
        # Remove punctuation from token
        clean = re.sub(r"[^a-z0-9]", "", token)
        if clean in _WORD_TO_DIGIT:
            digits.append(_WORD_TO_DIGIT[clean])
        elif clean.isdigit():
            digits.extend(list(clean))
    result = "".join(digits)
    # If nothing was converted, just strip non-digits from original
    if not result:
        result = re.sub(r"\D", "", raw)
    return result


class HealthcareTools:

    def __init__(self, session_id: str, room=None) -> None:
        self.session_id = session_id
        self.room = room
        self.user_phone: Optional[str] = None
        self.user_name: Optional[str] = None

    async def _broadcast(self, tool_name: str, status: str, message: str) -> None:
        event_payload = {
            "type": "tool_event",
            "tool_name": tool_name,
            "status": status,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            async with AsyncSessionLocal() as db:
                db.add(ToolEvent(
                    session_id=self.session_id,
                    tool_name=tool_name,
                    status=status,
                    message=message,
                ))
                await db.commit()
        except Exception as exc:
            logger.error("tool_event db persist failed", error=str(exc))

        if self.room:
            try:
                await self.room.local_participant.publish_data(
                    json.dumps(event_payload).encode(),
                    reliable=True,
                    topic="tool-events",
                )
            except Exception as exc:
                logger.error("LiveKit publish_data failed", error=str(exc))

        logger.info("tool_event", tool=tool_name, status=status, msg=message)

    async def _sync_session(self) -> None:
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(Session).where(Session.id == self.session_id))
                sess = res.scalar_one_or_none()
                if sess:
                    sess.user_phone = self.user_phone
                    sess.user_name = self.user_name
                    await db.commit()
        except Exception as exc:
            logger.error("session sync failed", error=str(exc))

    async def _push_appointment_event(self, action: str, appt: Appointment) -> None:
        if not self.room:
            return
        try:
            await self.room.local_participant.publish_data(
                json.dumps({
                    "type": "appointment_update",
                    "action": action,
                    "appointment": {
                        "id": appt.id,
                        "user_phone": appt.user_phone,
                        "date": appt.date,
                        "time": appt.time,
                        "status": appt.status,
                    },
                }).encode(),
                reliable=True,
                topic="appointments",
            )
        except Exception as exc:
            logger.error("appointment push failed", error=str(exc))

    @function_tool
    async def identify_user(
        self,
        phone_number: Annotated[str, "Patient's phone number — digits or spoken words like 'seven three one...'"],
    ) -> str:
        """Identify a patient by their phone number. ALWAYS call this first before any appointment operation."""

        # ── KEY FIX: normalize spoken words to digits ──────────────────
        phone_number = normalize_phone(phone_number)
        logger.info("identify_user called", raw_input=phone_number)
        # ───────────────────────────────────────────────────────────────

        await self._broadcast("identify_user", "calling", f"Identifying patient {phone_number}…")

        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(User).where(User.phone == phone_number))
                user = res.scalar_one_or_none()

            if user:
                self.user_phone = user.phone
                self.user_name = user.name
                await self._sync_session()
                await self._broadcast("identify_user", "success", f"Patient identified: {user.name}")
                return json.dumps({
                    "found": True,
                    "name": user.name,
                    "phone": user.phone,
                    "message": f"Welcome back, {user.name}!",
                })
            else:
                self.user_phone = phone_number
                await self._sync_session()
                await self._broadcast("identify_user", "new_user", f"New patient: {phone_number}")
                return json.dumps({
                    "found": False,
                    "phone": phone_number,
                    "message": (
                        "New patient detected. Please ask for their full name "
                        "and then call register_patient to create their record."
                    ),
                })
        except Exception as exc:
            logger.error("identify_user error", error=str(exc))
            await self._broadcast("identify_user", "error", str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def register_patient(
        self,
        name: Annotated[str, "Patient's full name"],
        phone_number: Annotated[str, "Patient's phone number"],
    ) -> str:
        """Register a new patient. Call right after identify_user returns found=false."""
        phone_number = normalize_phone(phone_number)
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(User).where(User.phone == phone_number))
                existing = res.scalar_one_or_none()
                if existing:
                    existing.name = name
                else:
                    db.add(User(name=name, phone=phone_number))
                await db.commit()

            self.user_phone = phone_number
            self.user_name = name
            await self._sync_session()
            logger.info("Patient registered", name=name, phone=phone_number)
            return json.dumps({
                "success": True,
                "name": name,
                "phone": phone_number,
                "message": f"Welcome, {name}! You are now registered with Mykare Health.",
            })
        except Exception as exc:
            logger.error("register_patient error", error=str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def fetch_slots(
        self,
        date: Annotated[str, "Optional date YYYY-MM-DD. Leave empty for all dates."] = "",
    ) -> str:
        """Fetch available appointment slots."""
        await self._broadcast("fetch_slots", "calling", "Fetching available slots…")
        try:
            async with AsyncSessionLocal() as db:
                available: dict[str, list[str]] = {}
                for slot_date, times in AVAILABLE_SLOTS.items():
                    booked_res = await db.execute(
                        select(Appointment.time).where(
                            and_(Appointment.date == slot_date, Appointment.status == "scheduled")
                        )
                    )
                    booked = {r[0] for r in booked_res.fetchall()}
                    available[slot_date] = [t for t in times if t not in booked]

            filtered = {k: v for k, v in available.items() if k == date} if date else available
            lines = [f"{d}: {', '.join(ts)}" for d, ts in filtered.items() if ts]
            await self._broadcast("fetch_slots", "success", f"Slots on {len(lines)} date(s)")
            return json.dumps({
                "success": True,
                "slots": filtered,
                "message": "Available slots:\n" + "\n".join(lines) if lines else "No slots available.",
            })
        except Exception as exc:
            logger.error("fetch_slots error", error=str(exc))
            await self._broadcast("fetch_slots", "error", str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def book_appointment(
        self,
        date: Annotated[str, "Appointment date YYYY-MM-DD"],
        time: Annotated[str, "Appointment time e.g. '09:00 AM'"],
    ) -> str:
        """Book an appointment for the identified patient."""
        await self._broadcast("book_appointment", "calling", f"Booking {date} at {time}…")
        if not self.user_phone:
            return json.dumps({"error": "Patient not identified. Call identify_user first."})
        try:
            async with AsyncSessionLocal() as db:
                conflict = await db.execute(
                    select(Appointment).where(
                        and_(Appointment.date == date, Appointment.time == time, Appointment.status == "scheduled")
                    )
                )
                if conflict.scalar_one_or_none():
                    await self._broadcast("book_appointment", "conflict", "Slot already taken")
                    return json.dumps({"success": False, "message": f"Slot {date} at {time} is already booked."})

                appt = Appointment(user_phone=self.user_phone, date=date, time=time, status="scheduled")
                db.add(appt)
                await db.commit()
                await db.refresh(appt)

            await self._push_appointment_event("booked", appt)
            await self._broadcast("book_appointment", "success", f"Appointment #{appt.id} confirmed")
            return json.dumps({
                "success": True,
                "appointment_id": appt.id,
                "date": date,
                "time": time,
                "message": f"Appointment confirmed! Date: {date}, Time: {time}. Booking ID: #{appt.id}.",
            })
        except Exception as exc:
            logger.error("book_appointment error", error=str(exc))
            await self._broadcast("book_appointment", "error", str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def retrieve_appointments(self) -> str:
        """Retrieve all appointments for the current patient."""
        await self._broadcast("retrieve_appointments", "calling", "Retrieving appointments…")
        if not self.user_phone:
            return json.dumps({"error": "Patient not identified. Call identify_user first."})
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Appointment)
                    .where(Appointment.user_phone == self.user_phone)
                    .order_by(Appointment.date, Appointment.time)
                )
                appts = res.scalars().all()

            appt_list = [{"id": a.id, "date": a.date, "time": a.time, "status": a.status} for a in appts]
            await self._broadcast("retrieve_appointments", "success", f"Found {len(appt_list)} appointment(s)")
            return json.dumps({"success": True, "appointments": appt_list,
                               "message": f"Found {len(appt_list)} appointment(s)."})
        except Exception as exc:
            logger.error("retrieve_appointments error", error=str(exc))
            await self._broadcast("retrieve_appointments", "error", str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def modify_appointment(
        self,
        appointment_id: Annotated[int, "ID of the appointment to reschedule"],
        new_date: Annotated[str, "New date YYYY-MM-DD"],
        new_time: Annotated[str, "New time e.g. '10:00 AM'"],
    ) -> str:
        """Reschedule an existing appointment."""
        await self._broadcast("modify_appointment", "calling", f"Rescheduling #{appointment_id}…")
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Appointment).where(
                        and_(Appointment.id == appointment_id,
                             Appointment.user_phone == self.user_phone,
                             Appointment.status == "scheduled")
                    )
                )
                appt = res.scalar_one_or_none()
                if not appt:
                    return json.dumps({"success": False, "message": "Appointment not found."})

                conflict = await db.execute(
                    select(Appointment).where(
                        and_(Appointment.date == new_date, Appointment.time == new_time,
                             Appointment.status == "scheduled", Appointment.id != appointment_id)
                    )
                )
                if conflict.scalar_one_or_none():
                    return json.dumps({"success": False, "message": f"Slot {new_date} at {new_time} not available."})

                old_date, old_time = appt.date, appt.time
                appt.date = new_date
                appt.time = new_time
                await db.commit()
                await db.refresh(appt)

            await self._push_appointment_event("modified", appt)
            await self._broadcast("modify_appointment", "success", f"Rescheduled to {new_date} at {new_time}")
            return json.dumps({"success": True, "message": f"Rescheduled from {old_date} {old_time} to {new_date} {new_time}."})
        except Exception as exc:
            logger.error("modify_appointment error", error=str(exc))
            await self._broadcast("modify_appointment", "error", str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def cancel_appointment(
        self,
        appointment_id: Annotated[int, "ID of the appointment to cancel"],
    ) -> str:
        """Cancel an existing scheduled appointment."""
        await self._broadcast("cancel_appointment", "calling", f"Cancelling #{appointment_id}…")
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Appointment).where(
                        and_(Appointment.id == appointment_id,
                             Appointment.user_phone == self.user_phone,
                             Appointment.status == "scheduled")
                    )
                )
                appt = res.scalar_one_or_none()
                if not appt:
                    return json.dumps({"success": False, "message": "Appointment not found."})

                saved_date, saved_time = appt.date, appt.time
                appt.status = "cancelled"
                await db.commit()
                await db.refresh(appt)

            await self._push_appointment_event("cancelled", appt)
            await self._broadcast("cancel_appointment", "success", f"Appointment #{appointment_id} cancelled")
            return json.dumps({"success": True, "message": f"Appointment #{appointment_id} on {saved_date} at {saved_time} cancelled."})
        except Exception as exc:
            logger.error("cancel_appointment error", error=str(exc))
            await self._broadcast("cancel_appointment", "error", str(exc))
            return json.dumps({"error": str(exc)})

    @function_tool
    async def end_conversation(
        self,
        user_preferences: Annotated[str, "Any notes or preferences the patient mentioned."] = "",
    ) -> str:
        """End the call and generate a full conversation summary."""
        await self._broadcast("end_conversation", "calling", "Generating summary…")
        try:
            async with AsyncSessionLocal() as db:
                appts_res = await db.execute(
                    select(Appointment).where(Appointment.user_phone == self.user_phone)
                ) if self.user_phone else None
                appointments = []
                if appts_res:
                    appointments = [{"id": a.id, "date": a.date, "time": a.time, "status": a.status}
                                    for a in appts_res.scalars().all()]

                tevents_res = await db.execute(select(ToolEvent).where(ToolEvent.session_id == self.session_id))
                tools_used = list({e.tool_name for e in tevents_res.scalars().all()})

                summary = {
                    "session_id": self.session_id,
                    "user_name": self.user_name,
                    "user_phone": self.user_phone,
                    "appointments": appointments,
                    "tools_used": tools_used,
                    "preferences": user_preferences,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                sess_res = await db.execute(select(Session).where(Session.id == self.session_id))
                sess = sess_res.scalar_one_or_none()
                if sess:
                    sess.summary_json = json.dumps(summary)
                    await db.commit()

            if self.room:
                await self.room.local_participant.publish_data(
                    json.dumps({"type": "summary", "summary": summary}).encode(),
                    reliable=True, topic="summary",
                )

            await self._broadcast("end_conversation", "success", "Summary generated")
            return json.dumps({"success": True, "summary": summary,
                               "message": "Thank you for calling Mykare Health. Have a wonderful day!"})
        except Exception as exc:
            logger.error("end_conversation error", error=str(exc))
            await self._broadcast("end_conversation", "error", str(exc))
            return json.dumps({"error": str(exc)})