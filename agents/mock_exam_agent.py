"""Mock Exam Agent for timed tests with real exam marking schemes."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from core.llm_provider import get_llm_provider
from db.database import get_session
from db.models import MockExamResult
from prompts.agent_prompts import MOCK_EXAM_EVALUATOR_PROMPT, MOCK_EXAM_GENERATOR_PROMPT

EXAM_PATTERNS: Dict[str, Dict[str, Any]] = {
    "JEE Main": {
        "num_questions": 5,
        "time_minutes": 10,
        "correct_marks": 4,
        "negative_marks": -1,
        "instructions": "Single correct MCQs with 4 options (A, B, C, D). Focus on conceptual calculation and physics/math principles.",
        "marking_rules": "+4 marks for each correct option, -1 mark for each incorrect option, 0 for unattempted.",
    },
    "NEET-UG": {
        "num_questions": 5,
        "time_minutes": 5,
        "correct_marks": 4,
        "negative_marks": -1,
        "instructions": "Speed-focused biology/physics MCQs with 4 options (A, B, C, D).",
        "marking_rules": "+4 marks for correct, -1 mark for incorrect, 0 for unattempted.",
    },
    "UPSC CSE": {
        "num_questions": 2,
        "time_minutes": 15,
        "correct_marks": 10,
        "negative_marks": 0,
        "instructions": "Subjective analytical Mains questions (10 markers, 150 words). Evaluate on Structure, Content, Analysis, and Conclusion.",
        "marking_rules": "Score each question from 0 to 10 based on standard UPSC Mains rubric.",
    },
}


def parse_mcq_blocks(raw_text: str) -> List[Dict[str, Any]]:
    """Parses questions, options, keys, and explanations from generated mock text."""
    blocks = re.split(r"---|\n### Question \d+", raw_text)
    questions: List[Dict[str, Any]] = []

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 30:
            continue

        # Extract correct option
        key_match = re.search(r"\[CORRECT_OPTION\]:\s*\[?([A-D])\]?", block, re.IGNORECASE)
        correct_opt = key_match.group(1).upper() if key_match else "A"

        # Extract explanation
        exp_match = re.search(r"\[EXPLANATION\]:\s*\[?([^\]\n]+(?:[\n][^\n]+)*)\]?", block, re.IGNORECASE)
        explanation = exp_match.group(1).strip() if exp_match else ""

        # Extract question statement & options
        cleaned_body = re.sub(r"\[CORRECT_OPTION\]:.*", "", block, flags=re.IGNORECASE | re.DOTALL).strip()

        questions.append({
            "text": cleaned_body,
            "correct_option": correct_opt,
            "explanation": explanation,
        })

    return questions


def generate_mock_exam(
    exam_pattern: str,
    subject: str,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a full mini mock exam for the selected exam pattern."""
    pattern_cfg = EXAM_PATTERNS.get(exam_pattern, EXAM_PATTERNS["JEE Main"])
    provider = get_llm_provider(name=provider_name, api_key=api_key)

    prompt = MOCK_EXAM_GENERATOR_PROMPT.format(
        exam_pattern=exam_pattern,
        subject=subject,
        num_questions=pattern_cfg["num_questions"],
        pattern_instructions=pattern_cfg["instructions"],
        q_num="{q_num}",
    )

    try:
        raw_output = provider.generate(prompt, tier="fast")
        questions = parse_mcq_blocks(raw_output)
        if not questions:
            # Fallback single block
            questions = [{"text": raw_output, "correct_option": "A", "explanation": ""}]

        return {
            "exam_pattern": exam_pattern,
            "subject": subject,
            "time_minutes": pattern_cfg["time_minutes"],
            "max_score": pattern_cfg["num_questions"] * pattern_cfg["correct_marks"],
            "questions": questions,
            "raw_text": raw_output,
        }
    except Exception as exc:
        return {
            "exam_pattern": exam_pattern,
            "subject": subject,
            "time_minutes": 10,
            "max_score": 20,
            "questions": [],
            "error": str(exc),
        }


def evaluate_mock_exam(
    user_id: Optional[int],
    exam_pattern: str,
    subject: str,
    questions: List[Dict[str, Any]],
    student_answers: Dict[int, str],
    time_taken_seconds: int = 0,
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluates student answers, tallies score, and persists to DB."""
    pattern_cfg = EXAM_PATTERNS.get(exam_pattern, EXAM_PATTERNS["JEE Main"])
    total_score = 0.0
    correct_count = 0
    incorrect_count = 0
    unattempted_count = 0
    question_reports = []

    if exam_pattern in ["JEE Main", "NEET-UG"]:
        for idx, q in enumerate(questions):
            ans = student_answers.get(idx, "").strip().upper()
            correct_key = q.get("correct_option", "A").upper()

            if not ans or ans == "UNATTEMPTED":
                unattempted_count += 1
                awarded = 0.0
                status = "Unattempted"
            elif ans == correct_key:
                correct_count += 1
                awarded = float(pattern_cfg["correct_marks"])
                status = "Correct"
            else:
                incorrect_count += 1
                awarded = float(pattern_cfg["negative_marks"])
                status = "Incorrect"

            total_score += awarded
            question_reports.append({
                "q_num": idx + 1,
                "student_ans": ans or "None",
                "correct_key": correct_key,
                "status": status,
                "marks": awarded,
                "explanation": q.get("explanation", ""),
            })

        max_score = len(questions) * pattern_cfg["correct_marks"]
        accuracy = round((correct_count / max(1, len(questions) - unattempted_count)) * 100.0, 1)

    else:
        # UPSC Subjective Evaluation via LLM
        provider = get_llm_provider(name=provider_name, api_key=api_key)
        q_keys_str = "\n\n".join([f"Q{i+1}: {q['text']}" for i, q in enumerate(questions)])
        subs_str = "\n\n".join([f"Q{i+1} Answer:\n{student_answers.get(i, 'Unattempted')}" for i in range(len(questions))])

        prompt = MOCK_EXAM_EVALUATOR_PROMPT.format(
            exam_pattern=exam_pattern,
            questions_and_keys=q_keys_str,
            student_submissions=subs_str,
            marking_rules=pattern_cfg["marking_rules"],
        )

        feedback_report = provider.generate(prompt, tier="pro")
        max_score = len(questions) * 10.0
        # Parse score
        score_match = re.search(r"TOTAL_SCORE:\s*\[?(\d+(?:\.\d+)?)\s*/", feedback_report, re.IGNORECASE)
        total_score = float(score_match.group(1)) if score_match else 5.0 * len(questions)
        accuracy = round((total_score / max(1.0, max_score)) * 100.0, 1)
        question_reports = [{"feedback": feedback_report}]

    result_data = {
        "exam_pattern": exam_pattern,
        "subject": subject,
        "score": total_score,
        "max_score": max_score,
        "accuracy": accuracy,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "unattempted_count": unattempted_count,
        "time_taken_seconds": time_taken_seconds,
        "breakdown": question_reports,
    }

    # Persist in SQLite
    if user_id:
        try:
            with get_session() as session:
                rec = MockExamResult(
                    user_id=user_id,
                    exam_pattern=exam_pattern,
                    subject=subject,
                    score=total_score,
                    max_score=max_score,
                    num_questions=len(questions),
                    time_taken_seconds=time_taken_seconds,
                    details_json=json.dumps(result_data),
                )
                session.add(rec)
        except Exception as exc:
            print(f"Error saving MockExamResult: {exc}")

    return result_data
