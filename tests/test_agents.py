"""Unit tests for agents and parsing utilities."""
from agents.evaluator import parse_evaluation_metadata
from agents.mock_exam_agent import parse_mcq_blocks
from agents.orchestrator import Orchestrator


def test_parse_evaluation_metadata():
    feedback_text = """
    ### VERDICT: [CORRECT]
    ### SCORE: [9.5 / 10]
    ### ERROR_TYPE: [None]

    Great step-by-step logic.
    """
    score, is_correct, error_type = parse_evaluation_metadata(feedback_text)
    assert score == 9.5
    assert is_correct is True
    assert error_type == "None"


def test_parse_incorrect_evaluation():
    feedback_text = """
    ### VERDICT: [INCORRECT]
    ### SCORE: [3 / 10]
    ### ERROR_TYPE: [Conceptual Error]

    Failed to apply Newton's second law.
    """
    score, is_correct, error_type = parse_evaluation_metadata(feedback_text)
    assert score == 3.0
    assert is_correct is False
    assert error_type == "Conceptual Error"


def test_parse_mcq_blocks():
    raw_mock_output = """
    ### Question 1
    What is the SI unit of electric flux?
    (A) Volt-meter
    (B) Newton/Coulomb
    (C) Weber
    (D) Tesla

    [CORRECT_OPTION]: A
    [EXPLANATION]: Electric flux is E*A which equals (V/m)*m^2 = Volt-meter.
    ---
    ### Question 2
    Find the derivative of sin(x).
    (A) cos(x)
    (B) -cos(x)
    (C) tan(x)
    (D) cot(x)

    [CORRECT_OPTION]: A
    [EXPLANATION]: Standard calculus rule d/dx(sin x) = cos x.
    """
    questions = parse_mcq_blocks(raw_mock_output)
    assert len(questions) == 2
    assert questions[0]["correct_option"] == "A"
    assert "electric flux" in questions[0]["text"].lower()


def test_orchestrator_initialization():
    orch = Orchestrator(provider_name="gemini", api_key="dummy_key")
    assert orch.provider_name == "gemini"
    assert orch.api_key == "dummy_key"
    assert orch.determine_adaptive_difficulty(None, "") == "Moderate (Exam Level)"
