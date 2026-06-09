import os
import google.generativeai as genai
from prompts.agent_prompts import QUESTION_GENERATOR_PROMPT

def generate_question(subject: str, weaknesses: list = None, context: str = "") -> str:
    """Generates a question using Gemini."""
    # Configure and instantiate dynamically to pick up session API key
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "DUMMY_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
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
        key = os.environ.get("GEMINI_API_KEY", "")
        masked_key = f"{key[:5]}...{key[-5:]}" if len(key) > 10 else "EMPTY/SHORT"
        return f"Error generating question using key {masked_key}: {str(e)}"
