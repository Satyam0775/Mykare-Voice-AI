"""
ORM models: users · appointments · sessions · tool_events
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r} phone={self.phone!r}>"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_phone = Column(String(20), index=True, nullable=False)
    date = Column(String(20), nullable=False)   # YYYY-MM-DD
    time = Column(String(20), nullable=False)   # HH:MM AM/PM
    status = Column(String(20), default="scheduled", nullable=False)  # scheduled | cancelled
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} {self.date}@{self.time} {self.status}>"


class Session(Base):
    """Tracks a single voice call / conversation."""

    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True)          # UUID
    room_name = Column(String(100), nullable=True)
    user_phone = Column(String(20), nullable=True)
    user_name = Column(String(200), nullable=True)
    context_json = Column(Text, default="{}")           # arbitrary session data
    summary_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ToolEvent(Base):
    """Records every tool call made during a session."""

    __tablename__ = "tool_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, nullable=False)
    tool_name = Column(String(60), nullable=False)
    status = Column(String(30), nullable=False)   # calling | success | error | conflict | ...
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
