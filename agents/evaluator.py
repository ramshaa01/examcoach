import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import google.generativeai as genai
from prompts.agent_prompts import EVALUATOR_PROMPT

def evaluate_answer(question: str, student_answer: str, context: str = "") -> str:
    """Evaluates the student's answer."""
    # Configure and instantiate dynamically to pick up session API key
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "DUMMY_KEY"))
    model = genai.GenerativeModel('gemini-2.5-pro') # Using pro for better evaluation
    
    prompt = EVALUATOR_PROMPT.format(
        question=question,
        student_answer=student_answer,
        context=context
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        key = os.environ.get("GEMINI_API_KEY", "")
        masked_key = f"{key[:5]}...{key[-5:]}" if len(key) > 10 else "EMPTY/SHORT"
        return f"Error evaluating answer using key {masked_key}: {str(e)}"
