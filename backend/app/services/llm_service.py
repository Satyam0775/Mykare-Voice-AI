"""
LLM service — uses openrouter/free which auto-selects any working free model
with tool calling. Never goes 404.
"""
from __future__ import annotations

from livekit.plugins import openai as lk_openai

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def create_llm() -> lk_openai.LLM:
    logger.info("llm_provider_selected", provider="openrouter", model="openrouter/free")
    return lk_openai.LLM(
        model="openrouter/free",
        base_url=OPENROUTER_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        extra_headers={
            "HTTP-Referer": "https://mykare.health",
            "X-Title": "Mykare Voice AI",
        },
    )