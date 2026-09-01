"""Student Profiler & Weakness Tracker Agent with SQLite persistence."""
from __future__ import annotations

import datetime as dt
import json
import os
from typing import Optional

from core.llm_provider import get_llm_provider
from db.database import get_session
from db.models import Attempt, TopicMastery
from prompts.agent_prompts import TRACKER_PROMPT

PROFILE_FILE = "student_profile.json"


def load_profile_json() -> dict:
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"weaknesses": []}


def save_profile_json(profile: dict) -> None:
    try:
        with open(PROFILE_FILE, "w") as f:
            json.dump(profile, f, indent=4)
    except Exception as exc:
        print(f"Error saving student_profile.json: {exc}")


def extract_weak_concept(
    evaluator_feedback: str,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[str]:
    """Uses LLM to extract the core weak concept from evaluation feedback."""
    prompt = TRACKER_PROMPT.format(evaluator_feedback=evaluator_feedback)
    try:
        provider = get_llm_provider(name=provider_name, api_key=api_key)
        concept = provider.generate(prompt, tier="fast").strip()
        concept_clean = concept.strip(".\"'\n ")
        if concept_clean.lower() not in ["none", "none.", "n/a", "", "no weakness"]:
            return concept_clean
    except Exception as exc:
        print(f"Error in tracker LLM extraction: {exc}")
    return None


def record_attempt_and_update_mastery(
    user_id: Optional[int],
    subject: str,
    topic: str,
    difficulty: str,
    question: str,
    student_answer: str,
    feedback: str,
    score: float,
    is_correct: bool,
    error_type: str,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> list[str]:
    """Records the attempt in SQLite and updates the topic mastery rolling score."""
    weak_concept = extract_weak_concept(feedback, provider_name, api_key)
    active_topic = weak_concept or topic or subject

    # 1. Update SQLite DB if user_id is provided
    if user_id:
        try:
            with get_session() as session:
                attempt = Attempt(
                    user_id=user_id,
                    subject=subject,
                    topic=active_topic,
                    difficulty=difficulty,
                    question=question,
                    student_answer=student_answer,
                    feedback=feedback,
                    score=score,
                    is_correct=is_correct,
                    error_type=error_type,
                    created_at=dt.datetime.now(dt.timezone.utc),
                )
                session.add(attempt)

                # Upsert TopicMastery
                mastery = (
                    session.query(TopicMastery)
                    .filter(TopicMastery.user_id == user_id, TopicMastery.topic == active_topic)
                    .first()
                )
                if not mastery:
                    mastery = TopicMastery(
                        user_id=user_id,
                        subject=subject,
                        topic=active_topic,
                        correct_count=1 if is_correct else 0,
                        total_count=1,
                        mastery_score=100.0 if is_correct else max(0.0, score * 10.0),
                        is_weak=not is_correct,
                        last_seen=dt.datetime.now(dt.timezone.utc),
                    )
                    session.add(mastery)
                else:
                    mastery.total_count += 1
                    if is_correct:
                        mastery.correct_count += 1
                    # Exponential rolling average (60% history, 40% latest attempt)
                    latest_score = 100.0 if is_correct else (score * 10.0)
                    mastery.mastery_score = round(0.6 * mastery.mastery_score + 0.4 * latest_score, 1)
                    mastery.is_weak = mastery.mastery_score < 60.0
                    mastery.last_seen = dt.datetime.now(dt.timezone.utc)
        except Exception as exc:
            print(f"Error persisting to SQLite: {exc}")

    # 2. Update student_profile.json as local mirror/fallback
    profile = load_profile_json()
    weaknesses = profile.get("weaknesses", [])
    if weak_concept and weak_concept not in weaknesses:
        weaknesses.append(weak_concept)
        profile["weaknesses"] = weaknesses
        save_profile_json(profile)
    elif is_correct and active_topic in weaknesses:
        # If successfully answered, student may have cleared it
        pass

    return get_user_weaknesses(user_id)


def get_user_weaknesses(user_id: Optional[int] = None) -> list[str]:
    """Fetches active weak topics for the user from SQLite, falling back to JSON."""
    if user_id:
        try:
            with get_session() as session:
                records = (
                    session.query(TopicMastery)
                    .filter(TopicMastery.user_id == user_id, TopicMastery.is_weak == True)
                    .order_by(TopicMastery.mastery_score.asc())
                    .all()
                )
                if records:
                    return [r.topic for r in records]
        except Exception as exc:
            print(f"Error reading weaknesses from DB: {exc}")

    return load_profile_json().get("weaknesses", [])
