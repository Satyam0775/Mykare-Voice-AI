"""LiveKit worker launcher for Mykare voice agent."""
from __future__ import annotations

from livekit.agents import cli

from app.agent.voice_agent import get_worker_options
from app.config import settings
from app.utils.logger import setup_logging


if __name__ == "__main__":
    setup_logging(settings.LOG_LEVEL)
    cli.run_app(get_worker_options())