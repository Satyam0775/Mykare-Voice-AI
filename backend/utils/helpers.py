import uuid
from datetime import datetime
from livekit.api import AccessToken, VideoGrants
from config import settings


def generate_livekit_token(room_name: str, participant_name: str, is_agent: bool = False) -> str:
    """Generate a LiveKit access token for a participant."""
    token = AccessToken(
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
    )
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(
        VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )
    )
    return token.to_jwt()


def generate_room_name() -> str:
    """Generate a unique room name."""
    return f"mykare-{uuid.uuid4().hex[:8]}"


def format_date(date_str: str) -> str:
    """Format a date string for display."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A, %B %d, %Y")
    except Exception:
        return date_str


def format_time(time_str: str) -> str:
    """Format a time string for display."""
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%I:%M %p")
    except Exception:
        return time_str


def sanitize_phone(phone: str) -> str:
    """Normalize phone number to digits only."""
    import re
    digits = re.sub(r'\D', '', phone)
    return digits[-10:] if len(digits) >= 10 else digits
