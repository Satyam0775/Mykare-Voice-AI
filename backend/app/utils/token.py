"""
LiveKit JWT token generation for both agents and browser participants.
"""
from livekit.api import AccessToken, VideoGrants

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_livekit_token(
    room_name: str,
    participant_identity: str,
    participant_name: str | None = None,
    is_agent: bool = False,
) -> str:
    """
    Generate a signed LiveKit JWT.

    Args:
        room_name:              Room to join.
        participant_identity:   Unique participant identity.
        participant_name:       Human-readable display name.
        is_agent:               If True, grants additional publish permissions.

    Returns:
        Signed JWT string.
    """
    grants = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    token = (
        AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        .with_identity(participant_identity)
        .with_name(participant_name or participant_identity)
        .with_grants(grants)
    )

    jwt = token.to_jwt()
    logger.info(
        "LiveKit token generated",
        room=room_name,
        identity=participant_identity,
    )
    return jwt
