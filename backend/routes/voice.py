from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.helpers import generate_livekit_token, generate_room_name
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


class TokenRequest(BaseModel):
    participant_name: str = "patient"
    room_name: str = None


class TokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str


@router.post("/token", response_model=TokenResponse)
async def get_livekit_token(request: TokenRequest):
    """Generate a LiveKit token for a participant to join a voice room."""
    try:
        room = request.room_name or generate_room_name()
        token = generate_livekit_token(
            room_name=room,
            participant_name=request.participant_name,
        )
        return TokenResponse(
            token=token,
            room_name=room,
            livekit_url=settings.livekit_url,
        )
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")


@router.get("/health")
async def voice_health():
    return {
        "status": "ok",
        "livekit_url": settings.livekit_url,
        "deepgram_model": settings.deepgram_stt_model,
        "tts_model": settings.deepgram_tts_model,
        "llm_model": settings.llm_model,
    }
