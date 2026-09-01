"""Evaluator Agent for step-by-step grading and error classification."""
from __future__ import annotations

import re
from typing import Optional, Tuple

from core.llm_provider import get_llm_provider
from prompts.agent_prompts import EVALUATOR_PROMPT


def parse_evaluation_metadata(feedback: str) -> Tuple[float, bool, str]:
    """Extracts (score, is_correct, error_type) from structured LLM feedback."""
    score = 0.0
    is_correct = False
    error_type = "Conceptual Error"

    # Match SCORE: [X / 10] or SCORE: X
    score_match = re.search(r"SCORE:\s*\[?(\d+(?:\.\d+)?)\s*(?:/\s*10)?\]?", feedback, re.IGNORECASE)
    if score_match:
        try:
            score = float(score_match.group(1))
        except ValueError:
            score = 0.0

    # Match VERDICT
    verdict_match = re.search(r"VERDICT:\s*\[?([A-Z\s]+)\]?", feedback, re.IGNORECASE)
    if verdict_match:
        verdict = verdict_match.group(1).strip().upper()
        if "CORRECT" in verdict and "INCORRECT" not in verdict and "PARTIAL" not in verdict:
            is_correct = True
            error_type = "None"
        elif "PARTIAL" in verdict:
            is_correct = score >= 5.0
            error_type = "Incomplete Solution"
        else:
            is_correct = False

    # Match ERROR_TYPE
    error_match = re.search(r"ERROR_TYPE:\s*\[?([^\]\n]+)\]?", feedback, re.IGNORECASE)
    if error_match:
        extracted = error_match.group(1).strip()
        if extracted and extracted.lower() != "none":
            error_type = extracted

    return score, is_correct, error_type


def evaluate_answer(
    question: str,
    student_answer: str,
    context: str = "",
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Tuple[str, float, bool, str]:
    """Evaluates the student's answer using the stronger 'pro' model tier."""
    provider = get_llm_provider(name=provider_name, api_key=api_key)

    prompt = EVALUATOR_PROMPT.format(
        question=question,
        student_answer=student_answer,
        context=context or "No specific notes provided.",
    )

    try:
        feedback = provider.generate(prompt, tier="pro")
        score, is_correct, error_type = parse_evaluation_metadata(feedback)
        return feedback, score, is_correct, error_type
    except Exception as exc:
        err_msg = f"Error evaluating answer: {exc}"
        return err_msg, 0.0, False, "Evaluation Failure"
