"""SQLAlchemy models for ExamCoach's persistent store."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    attempts: Mapped[list["Attempt"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    mastery: Mapped[list["TopicMastery"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    mock_results: Mapped[list["MockExamResult"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Attempt(Base):
    """One practice question attempt (used for accuracy trends and adaptive difficulty)."""

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(64))
    topic: Mapped[str] = mapped_column(String(128), default="")
    difficulty: Mapped[str] = mapped_column(String(32), default="Moderate (Exam Level)")
    question: Mapped[str] = mapped_column(Text)
    student_answer: Mapped[str] = mapped_column(Text)
    feedback: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    user: Mapped["User"] = relationship(back_populates="attempts")


class TopicMastery(Base):
    """Rolling per-topic mastery used to scale difficulty and drive the radar chart."""

    __tablename__ = "topic_mastery"
    __table_args__ = (UniqueConstraint("user_id", "topic", name="uq_user_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(64), default="")
    topic: Mapped[str] = mapped_column(String(128))
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    is_weak: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="mastery")


class MockExamResult(Base):
    """Summary of one completed timed mock test."""

    __tablename__ = "mock_exam_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    exam_pattern: Mapped[str] = mapped_column(String(32))  # JEE / NEET / UPSC
    subject: Mapped[str] = mapped_column(String(64))
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float)
    num_questions: Mapped[int] = mapped_column(Integer)
    time_taken_seconds: Mapped[int] = mapped_column(Integer, default=0)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    user: Mapped["User"] = relationship(back_populates="mock_results")
