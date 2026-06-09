import json
import os
import google.generativeai as genai
from prompts.agent_prompts import TRACKER_PROMPT

PROFILE_FILE = "student_profile.json"

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", "DUMMY_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {"weaknesses": []}

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=4)

def update_weaknesses(evaluator_feedback: str):
    """Extract weak concepts using LLM and update file."""
    prompt = TRACKER_PROMPT.format(evaluator_feedback=evaluator_feedback)
    try:
        response = model.generate_content(prompt)
        concept = response.text.strip()
        
        if concept.lower() not in ["none", "none.", "n/a"]:
            profile = load_profile()
            if concept not in profile["weaknesses"]:
                profile["weaknesses"].append(concept)
            save_profile(profile)
            return profile["weaknesses"]
    except Exception as e:
        print(f"Error in tracker: {e}")
    return load_profile()["weaknesses"]
