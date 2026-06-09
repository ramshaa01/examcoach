from pydantic import BaseModel
from typing import List

class QuestionRequest(BaseModel):
    subject: str

class QuestionResponse(BaseModel):
    question: str

class EvaluationRequest(BaseModel):
    question: str
    student_answer: str
    subject: str

class EvaluationResponse(BaseModel):
    feedback: str
    updated_weaknesses: List[str]

class ProfileResponse(BaseModel):
    weaknesses: List[str]
