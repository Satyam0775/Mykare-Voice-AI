import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)


class STTService:
    """Deepgram Speech-to-Text service for REST API calls."""

    BASE_URL = "https://api.deepgram.com/v1"

    def __init__(self):
        self.headers = {
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": "audio/wav",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

    async def transcribe_audio(self, audio_bytes: bytes, mimetype: str = "audio/wav") -> dict:
        """Transcribe audio bytes using Deepgram."""
        try:
            params = {
                "model": settings.deepgram_stt_model,
                "language": "en-US",
                "punctuate": "true",
                "utterances": "false",
                "numerals": "true",
            }

            response = await self.client.post(
                f"{self.BASE_URL}/listen",
                headers={
                    "Authorization": f"Token {settings.deepgram_api_key}",
                    "Content-Type": mimetype,
                },
                content=audio_bytes,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            transcript = (
                data.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
                .get("transcript", "")
            )
            confidence = (
                data.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
                .get("confidence", 0.0)
            )

            return {
                "success": True,
                "transcript": transcript,
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"STT transcription error: {e}")
            return {"success": False, "error": str(e), "transcript": ""}

    async def close(self):
        await self.client.aclose()
