import uuid
from pydantic import BaseModel
from typing import List

interview_sessions = {}

class ResumeProfile(BaseModel):
    candidate_name: str
    skills: List[str]
    projects: List[str]
    experience: List[str]
    education: List[str]
    certifications: List[str]


class AnswerRequest(BaseModel):
    answer: str