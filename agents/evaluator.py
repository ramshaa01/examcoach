import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import google.generativeai as genai
from prompts.agent_prompts import EVALUATOR_PROMPT

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "DUMMY_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro') # Using pro for better evaluation

def evaluate_answer(question: str, student_answer: str, context: str = "") -> str:
    """Evaluates the student's answer."""
    prompt = EVALUATOR_PROMPT.format(
        question=question,
        student_answer=student_answer,
        context=context
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error evaluating answer: {str(e)}"
