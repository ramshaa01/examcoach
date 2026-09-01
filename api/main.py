from fastapi import FastAPI
from api.models import QuestionRequest, QuestionResponse, EvaluationRequest, EvaluationResponse, ProfileResponse
from agents.orchestrator import exam_orchestrator
from agents.tracker import get_user_weaknesses

app = FastAPI(title="ExamCoach API", description="AI Tutor for Indian Exams")

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "ExamCoach Multi-Agent API",
        "docs": "/docs",
        "endpoints": ["/generate_question", "/evaluate", "/profile"]
    }

@app.post("/generate_question", response_model=QuestionResponse)
async def generate_question_endpoint(req: QuestionRequest):
    question = exam_orchestrator.run_practice_flow(req.subject)
    return QuestionResponse(question=question)

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_endpoint(req: EvaluationRequest):
    feedback, weaknesses = exam_orchestrator.run_evaluation_flow(
        req.question, req.student_answer, req.subject
    )
    return EvaluationResponse(feedback=feedback, updated_weaknesses=weaknesses)

@app.get("/profile", response_model=ProfileResponse)
async def get_profile_endpoint():
    weaknesses = get_user_weaknesses(user_id=None)
    return ProfileResponse(weaknesses=weaknesses)
