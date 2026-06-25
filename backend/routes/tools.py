from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from tools.appointment_tools import AppointmentTools
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


class IdentifyUserRequest(BaseModel):
    phone_number: str
    name: Optional[str] = None


class FetchSlotsRequest(BaseModel):
    date: str
    doctor_name: Optional[str] = None


class BookAppointmentRequest(BaseModel):
    user_id: int
    appointment_date: str
    appointment_time: str
    doctor_name: str = "Dr. Sarah Johnson"
    department: str = "General"
    reason: Optional[str] = None


class RetrieveAppointmentsRequest(BaseModel):
    user_id: int


class CancelAppointmentRequest(BaseModel):
    appointment_id: int
    user_id: int


class ModifyAppointmentRequest(BaseModel):
    appointment_id: int
    user_id: int
    new_date: Optional[str] = None
    new_time: Optional[str] = None
    new_doctor: Optional[str] = None
    new_reason: Optional[str] = None


class EndConversationRequest(BaseModel):
    user_id: Optional[int] = None
    summary: str


@router.post("/identify_user")
async def identify_user(request: IdentifyUserRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.identify_user(
        phone_number=request.phone_number, name=request.name, db=db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/fetch_slots")
async def fetch_slots(request: FetchSlotsRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.fetch_slots(
        date=request.date, doctor_name=request.doctor_name, db=db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/book_appointment")
async def book_appointment(request: BookAppointmentRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.book_appointment(
        user_id=request.user_id,
        appointment_date=request.appointment_date,
        appointment_time=request.appointment_time,
        doctor_name=request.doctor_name,
        department=request.department,
        reason=request.reason,
        db=db,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", result.get("message")))
    return result


@router.post("/retrieve_appointments")
async def retrieve_appointments(request: RetrieveAppointmentsRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.retrieve_appointments(user_id=request.user_id, db=db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/cancel_appointment")
async def cancel_appointment(request: CancelAppointmentRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.cancel_appointment(
        appointment_id=request.appointment_id, user_id=request.user_id, db=db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/modify_appointment")
async def modify_appointment(request: ModifyAppointmentRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.modify_appointment(
        appointment_id=request.appointment_id,
        user_id=request.user_id,
        new_date=request.new_date,
        new_time=request.new_time,
        new_doctor=request.new_doctor,
        new_reason=request.new_reason,
        db=db,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/end_conversation")
async def end_conversation(request: EndConversationRequest, db: AsyncSession = Depends(get_db)):
    result = await AppointmentTools.end_conversation(
        user_id=request.user_id, summary=request.summary, db=db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
