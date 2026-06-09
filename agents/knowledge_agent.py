import os
import google.generativeai as genai
from prompts.agent_prompts import KNOWLEDGE_AGENT_PROMPT

def summarize_context(chunks: list) -> str:
    """Synthesizes the retrieved RAG chunks."""
    if not chunks:
        return ""
    
    # Configure and instantiate dynamically to pick up session API key
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "DUMMY_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    chunks_text = "\n\n".join(chunks)
    prompt = KNOWLEDGE_AGENT_PROMPT.format(chunks=chunks_text)
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in knowledge agent: {e}")
        return chunks_text # Fallback to raw chunks
