"""
Speech-to-text service: Deepgram Nova-2 via livekit-plugins-deepgram.
"""
from livekit.plugins import deepgram

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_stt() -> deepgram.STT:
    """Return a configured Deepgram STT plugin instance."""
    logger.info("STT: Deepgram Nova-2 initialised")
    return deepgram.STT(
        api_key=settings.DEEPGRAM_API_KEY,
        model="nova-2-general",
        language="en-US",
    )
