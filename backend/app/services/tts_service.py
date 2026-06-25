"""
Text-to-speech service: Cartesia Sonic-2 via livekit-plugins-cartesia.
"""
from livekit.plugins import cartesia

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_tts() -> cartesia.TTS:
    """Return a configured Cartesia TTS plugin instance."""
    logger.info(
        "TTS: Cartesia Sonic-2 initialised",
        voice_id=settings.CARTESIA_VOICE_ID,
    )
    return cartesia.TTS(
        api_key=settings.CARTESIA_API_KEY,
        model="sonic-2",
        voice=settings.CARTESIA_VOICE_ID,
        language="en",
        speed=1.0,
    )
