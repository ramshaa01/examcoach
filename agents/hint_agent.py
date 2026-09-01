"""Socratic Hint Agent for non-spoiler conceptual nudges."""
from __future__ import annotations

from typing import Optional

from core.llm_provider import get_llm_provider
from prompts.agent_prompts import HINT_PROMPT


def generate_hint(
    question: str,
    hint_level: int = 1,
    student_work: str = "",
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Generates a progressive Socratic hint (Level 1, 2, or 3) for the given question."""
    provider = get_llm_provider(name=provider_name, api_key=api_key)
    clamped_level = max(1, min(3, hint_level))

    prompt = HINT_PROMPT.format(
        question=question,
        hint_level=clamped_level,
        student_work=student_work.strip() or "None provided yet.",
    )

    try:
        return provider.generate(prompt, tier="fast")
    except Exception as exc:
        return f"Error generating hint: {exc}"
