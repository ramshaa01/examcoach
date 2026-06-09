from agents.question_generator import generate_question
from agents.evaluator import evaluate_answer
from agents.tracker import update_weaknesses, load_profile
from agents.knowledge_agent import summarize_context
from rag.retriever import retrieve_context

class Orchestrator:
    def __init__(self):
        # The orchestrator manages the high-level workflow
        pass

    def run_practice_flow(self, subject: str):
        """Initiates the generation of a new question."""
        # 1. Fetch profile
        profile = load_profile()
        weaknesses = profile.get("weaknesses", [])
        
        # 2. Retrieve relevant context for weak areas (if any)
        context = ""
        if weaknesses:
            raw_chunks = retrieve_context(weaknesses[0]) # Get context for biggest weakness
            context = summarize_context(raw_chunks)
        
        # 3. Generate Question
        question = generate_question(subject, weaknesses, context)
        return question

    def run_evaluation_flow(self, question: str, student_answer: str, subject: str):
        """Handles evaluation and updates student profile."""
        # 1. Retrieve subject context
        raw_chunks = retrieve_context(subject)
        context = summarize_context(raw_chunks)
        
        # 2. Evaluate Answer
        feedback = evaluate_answer(question, student_answer, context)
        
        # 3. Update Weaknesses
        new_weaknesses = update_weaknesses(feedback)
        
        return feedback, new_weaknesses

# Singleton instance
exam_orchestrator = Orchestrator()
