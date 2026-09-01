"""Central Orchestrator coordinating all multi-agent workflows."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agents.evaluator import evaluate_answer
from agents.hint_agent import generate_hint
from agents.knowledge_agent import summarize_context
from agents.mock_exam_agent import evaluate_mock_exam, generate_mock_exam
from agents.question_generator import generate_question
from agents.tracker import (
    get_user_weaknesses,
    load_profile_json,
    record_attempt_and_update_mastery,
)
from db.database import get_session
from db.models import TopicMastery
from rag.retriever import retrieve_context


class Orchestrator:
    """Coordinates high-level workflows across all agents."""

    def __init__(self, provider_name: Optional[str] = None, api_key: Optional[str] = None):
        self.provider_name = provider_name
        self.api_key = api_key

    def set_provider(self, provider_name: Optional[str], api_key: Optional[str]) -> None:
        self.provider_name = provider_name
        self.api_key = api_key

    def determine_adaptive_difficulty(self, user_id: Optional[int], topic: str) -> str:
        """Determines difficulty (Foundation / Moderate / Challenger) based on student's topic mastery."""
        if not user_id or not topic:
            return "Moderate (Exam Level)"

        try:
            with get_session() as session:
                rec = (
                    session.query(TopicMastery)
                    .filter(TopicMastery.user_id == user_id, TopicMastery.topic == topic)
                    .first()
                )
                if rec:
                    if rec.mastery_score < 40.0:
                        return "Foundation"
                    elif rec.mastery_score > 75.0:
                        return "Challenger (Advanced)"
        except Exception:
            pass

        return "Moderate (Exam Level)"

    def run_practice_flow(
        self,
        subject: str,
        user_id: Optional[int] = None,
        topic: str = "",
        difficulty: Optional[str] = None,
    ) -> str:
        """Practice workflow: fetches weaknesses, context, and generates a question."""
        # 1. Fetch user weaknesses
        weaknesses = get_user_weaknesses(user_id)

        # 2. Adaptive difficulty if not explicitly chosen
        resolved_diff = difficulty or self.determine_adaptive_difficulty(user_id, topic or (weaknesses[0] if weaknesses else ""))

        # 3. Retrieve relevant context for target topic/weakness
        query = topic or (weaknesses[0] if weaknesses else subject)
        raw_chunks = retrieve_context(query)
        context = summarize_context(raw_chunks, provider_name=self.provider_name, api_key=self.api_key) if raw_chunks else ""

        # 4. Generate Question
        return generate_question(
            subject=subject,
            topic=topic or (weaknesses[0] if weaknesses else ""),
            weaknesses=weaknesses,
            difficulty=resolved_diff,
            context=context,
            provider_name=self.provider_name,
            api_key=self.api_key,
        )

    def run_hint_flow(self, question: str, hint_level: int, student_work: str = "") -> str:
        """Hint workflow: requests progressive Socratic guidance."""
        return generate_hint(
            question=question,
            hint_level=hint_level,
            student_work=student_work,
            provider_name=self.provider_name,
            api_key=self.api_key,
        )

    def run_evaluation_flow(
        self,
        question: str,
        student_answer: str,
        subject: str,
        user_id: Optional[int] = None,
        topic: str = "",
        difficulty: str = "Moderate (Exam Level)",
    ) -> Tuple[str, list[str]]:
        """Evaluation workflow: grades answer, extracts weaknesses, updates SQLite."""
        # 1. Retrieve subject context
        raw_chunks = retrieve_context(topic or subject)
        context = summarize_context(raw_chunks, provider_name=self.provider_name, api_key=self.api_key) if raw_chunks else ""

        # 2. Evaluate
        feedback, score, is_correct, error_type = evaluate_answer(
            question=question,
            student_answer=student_answer,
            context=context,
            provider_name=self.provider_name,
            api_key=self.api_key,
        )

        # 3. Update Weaknesses & Mastery
        updated_weaknesses = record_attempt_and_update_mastery(
            user_id=user_id,
            subject=subject,
            topic=topic or subject,
            difficulty=difficulty,
            question=question,
            student_answer=student_answer,
            feedback=feedback,
            score=score,
            is_correct=is_correct,
            error_type=error_type,
            provider_name=self.provider_name,
            api_key=self.api_key,
        )

        return feedback, updated_weaknesses

    def run_mock_exam_generation(self, exam_pattern: str, subject: str) -> Dict[str, Any]:
        """Mock exam generation workflow."""
        return generate_mock_exam(
            exam_pattern=exam_pattern,
            subject=subject,
            provider_name=self.provider_name,
            api_key=self.api_key,
        )

    def run_mock_exam_evaluation(
        self,
        user_id: Optional[int],
        exam_pattern: str,
        subject: str,
        questions: List[Dict[str, Any]],
        student_answers: Dict[int, str],
        time_taken_seconds: int = 0,
    ) -> Dict[str, Any]:
        """Mock exam evaluation workflow."""
        return evaluate_mock_exam(
            user_id=user_id,
            exam_pattern=exam_pattern,
            subject=subject,
            questions=questions,
            student_answers=student_answers,
            time_taken_seconds=time_taken_seconds,
            provider_name=self.provider_name,
            api_key=self.api_key,
        )


# Global singleton instance
exam_orchestrator = Orchestrator()
