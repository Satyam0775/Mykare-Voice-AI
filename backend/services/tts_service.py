import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Deepgram Text-to-Speech service."""

    BASE_URL = "https://api.deepgram.com/v1/speak"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to speech using Deepgram."""
        try:
            params = {"model": settings.deepgram_tts_model}
            headers = {
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": "application/json",
            }
            payload = {"text": text}

            response = await self.client.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                params=params,
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise

    async def close(self):
        await self.client.aclose()
