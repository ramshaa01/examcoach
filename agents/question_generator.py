import os
import google.generativeai as genai
from prompts.agent_prompts import QUESTION_GENERATOR_PROMPT

# Configure API key (Assuming it's set in the environment or passed)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "DUMMY_KEY"))

model = genai.GenerativeModel('gemini-1.5-flash')

def generate_question(subject: str, weaknesses: list = None, context: str = "") -> str:
    """Generates a question using Gemini."""
    weak_str = ", ".join(weaknesses) if weaknesses else "None specific"
    prompt = QUESTION_GENERATOR_PROMPT.format(
        subject=subject,
        weaknesses=weak_str,
        context=context
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating question: {str(e)}"
