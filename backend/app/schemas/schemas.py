"""
Pydantic v2 schemas for request validation and response serialisation.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

class TokenRequest(BaseModel):
    room_name: str = Field(..., min_length=1, max_length=100)
    participant_name: Optional[str] = None


class TokenResponse(BaseModel):
    token: str
    url: str
    room_name: str
    participant_identity: str
    session_id: Optional[str] = None


class StartCallRequest(BaseModel):
    room_name: Optional[str] = None
    user_phone: Optional[str] = None


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    name: str
    phone: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: Optional[str]
    phone: str
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    user_phone: str
    date: str    # YYYY-MM-DD
    time: str    # HH:MM AM/PM


class AppointmentModify(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_phone: str
    date: str
    time: str
    status: str
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Session / Summary
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    room_name: str
    session_id: str


class SummaryResponse(BaseModel):
    session_id: str
    user_name: Optional[str]
    user_phone: Optional[str]
    summary: Optional[str]
    appointments: List[AppointmentResponse]
    tools_used: List[str]
    preferences: Optional[str]
    timestamp: str


# ---------------------------------------------------------------------------
# Tool event (for REST polling fallback)
# ---------------------------------------------------------------------------

class ToolEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    session_id: str
    tool_name: str
    status: str
    message: Optional[str]
    created_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------

class SlotsResponse(BaseModel):
    slots: Dict[str, List[str]]
    formatted: str
