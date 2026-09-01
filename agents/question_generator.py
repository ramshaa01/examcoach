"""Question Generator Agent using the pluggable LLM provider layer."""
from __future__ import annotations

from typing import Optional

from core.llm_provider import get_llm_provider
from prompts.agent_prompts import QUESTION_GENERATOR_PROMPT


def generate_question(
    subject: str,
    topic: str = "",
    weaknesses: Optional[list[str]] = None,
    difficulty: str = "Moderate (Exam Level)",
    context: str = "",
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Generates a competitive exam question using the active LLM provider."""
    provider = get_llm_provider(name=provider_name, api_key=api_key)
    weak_str = ", ".join(weaknesses) if weaknesses else "None specific"
    target_topic = topic.strip() or "Core Syllabus"

    prompt = QUESTION_GENERATOR_PROMPT.format(
        subject=subject,
        topic=target_topic,
        weaknesses=weak_str,
        difficulty=difficulty,
        context=context or "No specific notes provided.",
    )

    try:
        return provider.generate(prompt, tier="fast")
    except Exception as exc:
        return f"Error generating question: {exc}"
