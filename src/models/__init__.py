from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class Project(BaseModel):
    id: UUID
    name: str
    description: str
    tech_stack: List[str]
    project_time: str
    responsibilities: str
    results: str

class QuestionRecord(BaseModel):
    question: str
    logic: str

class GenerateQuestionsRequest(BaseModel):
    project_id: str
    project_name: str
    project_description: str

class GenerateQuestionsResponse(BaseModel):
    success: bool
    project_id: str
    questions: List[QuestionRecord]
    request_id: str
    latency_ms: int