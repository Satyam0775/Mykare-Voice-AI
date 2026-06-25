"""
FastAPI REST endpoints:
  POST /api/calls/token          — generate LiveKit JWT
  POST /api/calls/start          — create room + return token
  GET  /api/appointments/{phone} — list appointments
  POST /api/appointments         — create appointment
  PUT  /api/appointments/{id}    — update appointment
  DELETE /api/appointments/{id}  — cancel appointment
  GET  /api/users/{phone}        — get user
  POST /api/users                — create / upsert user
  GET  /api/sessions/{id}/summary  — get call summary
  GET  /api/sessions/{id}/events   — poll tool events
  GET  /api/slots                — available slots
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.db.models import Appointment, Session as DBSession, ToolEvent, User
from app.schemas.schemas import (
    AppointmentCreate,
    AppointmentModify,
    AppointmentResponse,
    SessionCreate,
    SlotsResponse,
    SummaryResponse,
    ToolEventResponse,
    TokenRequest,
    TokenResponse,
    StartCallRequest,
    UserCreate,
    UserResponse,
)
from app.tools.appointment_tools import AVAILABLE_SLOTS
from app.utils.logger import get_logger
from app.utils.token import generate_livekit_token

router = APIRouter(prefix="/api")
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# LiveKit tokens / room management
# ---------------------------------------------------------------------------

@router.post("/calls/token", response_model=TokenResponse)
async def get_livekit_token(req: TokenRequest):
    """Generate a LiveKit JWT for the browser participant."""
    identity = f"user-{uuid.uuid4().hex[:8]}"
    token = generate_livekit_token(
        room_name=req.room_name,
        participant_identity=identity,
        participant_name=req.participant_name or identity,
    )
    logger.info("Token issued", room=req.room_name, identity=identity)
    return TokenResponse(
        token=token,
        url=settings.LIVEKIT_URL,
        room_name=req.room_name,
        participant_identity=identity,
    )


@router.post("/calls/start", response_model=TokenResponse)
async def start_call(req: StartCallRequest, db: AsyncSession = Depends(get_db)):
    """Accept the browser-generated room_name, persist a session record, return a token + session_id."""
    room_name = req.room_name or f"mykare-{uuid.uuid4().hex[:12]}"
    identity = f"user-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())

    db.add(DBSession(id=session_id, room_name=room_name))
    await db.commit()

    token = generate_livekit_token(
        room_name=room_name,
        participant_identity=identity,
        participant_name="Patient",
    )
    logger.info("Call started", room=room_name, session_id=session_id)
    return TokenResponse(
        token=token,
        url=settings.LIVEKIT_URL,
        room_name=room_name,
        participant_identity=identity,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users/{phone}", response_model=UserResponse)
async def get_user(phone: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.phone == phone))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse)
async def create_or_update_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.phone == payload.phone))
    user = res.scalar_one_or_none()
    if user:
        user.name = payload.name
    else:
        user = User(name=payload.name, phone=payload.phone)
        db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("User upserted", phone=payload.phone, name=payload.name)
    return user


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

@router.get("/appointments/{phone}", response_model=List[AppointmentResponse])
async def list_appointments(phone: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Appointment)
        .where(Appointment.user_phone == phone)
        .order_by(Appointment.date, Appointment.time)
    )
    return res.scalars().all()


@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(payload: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    # Double-booking guard
    conflict = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.date == payload.date,
                Appointment.time == payload.time,
                Appointment.status == "scheduled",
            )
        )
    )
    if conflict.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slot already booked")

    appt = Appointment(
        user_phone=payload.user_phone,
        date=payload.date,
        time=payload.time,
        status="scheduled",
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    logger.info("Appointment created (REST)", phone=payload.user_phone, date=payload.date)
    return appt


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    payload: AppointmentModify,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.id == appointment_id,
                Appointment.status == "scheduled",
            )
        )
    )
    appt = res.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if payload.date:
        appt.date = payload.date
    if payload.time:
        appt.time = payload.time
    await db.commit()
    await db.refresh(appt)
    return appt


@router.delete("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def cancel_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Appointment).where(
            and_(
                Appointment.id == appointment_id,
                Appointment.status == "scheduled",
            )
        )
    )
    appt = res.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt.status = "cancelled"
    await db.commit()
    await db.refresh(appt)
    logger.info("Appointment cancelled (REST)", appt_id=appointment_id)
    return appt


# ---------------------------------------------------------------------------
# Sessions / Summary
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}/summary", response_model=SummaryResponse)
async def get_summary(session_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DBSession).where(DBSession.id == session_id))
    sess = res.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    appointments = []
    if sess.user_phone:
        appts_res = await db.execute(
            select(Appointment).where(Appointment.user_phone == sess.user_phone)
        )
        appointments = appts_res.scalars().all()

    tevents_res = await db.execute(
        select(ToolEvent).where(ToolEvent.session_id == session_id)
    )
    tools_used = list({e.tool_name for e in tevents_res.scalars().all()})

    summary_data = {}
    preferences = ""
    if sess.summary_json:
        try:
            summary_data = json.loads(sess.summary_json)
            preferences = summary_data.get("preferences", "")
        except json.JSONDecodeError:
            pass

    return SummaryResponse(
        session_id=session_id,
        user_name=sess.user_name,
        user_phone=sess.user_phone,
        summary=sess.summary_json,
        appointments=appointments,
        tools_used=tools_used,
        preferences=preferences,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/sessions/{session_id}/events", response_model=List[ToolEventResponse])
async def get_tool_events(
    session_id: str,
    since_id: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """REST polling fallback for tool events."""
    res = await db.execute(
        select(ToolEvent)
        .where(
            and_(
                ToolEvent.session_id == session_id,
                ToolEvent.id > since_id,
            )
        )
        .order_by(ToolEvent.id)
    )
    return res.scalars().all()


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------

@router.get("/slots", response_model=SlotsResponse)
async def get_slots(date: str = "", db: AsyncSession = Depends(get_db)):
    """Return available (unbooked) appointment slots."""
    available: dict[str, list[str]] = {}

    for slot_date, times in AVAILABLE_SLOTS.items():
        booked_res = await db.execute(
            select(Appointment.time).where(
                and_(
                    Appointment.date == slot_date,
                    Appointment.status == "scheduled",
                )
            )
        )
        booked = {r[0] for r in booked_res.fetchall()}
        available[slot_date] = [t for t in times if t not in booked]

    if date:
        available = {k: v for k, v in available.items() if k == date}

    lines = [f"{d}: {', '.join(ts)}" for d, ts in available.items() if ts]
    return SlotsResponse(slots=available, formatted="\n".join(lines))


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "ok", "service": "mykare-voice-ai", "timestamp": datetime.utcnow().isoformat()}
