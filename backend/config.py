from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # LiveKit
    livekit_url: str = "wss://localhost:7880"
    livekit_api_key: str = "devkey"
    livekit_api_secret: str = "secret"

    # Deepgram
    deepgram_api_key: str = ""
    deepgram_stt_model: str = "nova-2"
    deepgram_tts_model: str = "aura-asteria-en"

    # OpenRouter
    openrouter_api_key: str = ""

    # ── LLM model ──────────────────────────────────────────────────────────
    # meta-llama/Meta-Llama-3-8B-Instruct (original default) is unreliable
    # for tool-calling: it frequently returns plain text instead of tool_calls,
    # ignores the function schema, or produces malformed JSON arguments.
    #
    # Upgrade to a 70B model that has consistent tool-calling.
    # Override in .env:  LLM_MODEL=openai/gpt-4o-mini  (most reliable)
    #                    LLM_MODEL=meta-llama/llama-3.1-70b-instruct
    #                    LLM_MODEL=meta-llama/llama-3.3-70b-instruct
    # ──────────────────────────────────────────────────────────────────────
    llm_model: str = "meta-llama/llama-3.1-70b-instruct"

    # Database
    database_url: str = "sqlite+aiosqlite:///./healthcare.db"

    # App
    app_name: str = "Mykare Voice AI"
    debug: bool = False
    cors_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings() 