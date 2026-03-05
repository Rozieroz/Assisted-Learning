"""
 request and response models for the API to ensure data validation and serialization.

 actual database models are defined in app/models.py, - these Pydantic models are used for API interactions.
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List

# ---------- Student ----------
class StudentBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    learning_mode: Optional[str] = "normal"
    accessibility_enabled: Optional[bool] = False

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    risk_score: float
    created_at: datetime

    class Config:
        from_attributes = True  # orm_mode

# ---------- Topic ----------
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None
    difficulty_level: Optional[str] = "medium"

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- Quiz ----------
class QuizBase(BaseModel):
    topic_id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str = Field(..., pattern="^[A-D]$")
    difficulty_level: Optional[str] = None
    ai_generated: Optional[bool] = True

class QuizCreate(QuizBase):
    pass

class Quiz(QuizBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- QuizAttempt ----------
class QuizAttemptBase(BaseModel):
    student_id: int
    quiz_id: int
    selected_answer: Optional[str] = Field(None, pattern="^[A-D]$")
    is_correct: Optional[bool] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    time_taken: int  # seconds
    attempt_number: Optional[int] = 1

class QuizAttemptCreate(QuizAttemptBase):
    pass

class QuizAttempt(QuizAttemptBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- Answer Submission Request ----------
class AnswerSubmission(BaseModel):
    student_id: int
    quiz_id: int
    selected_answer: str = Field(..., pattern="^[A-D]$")
    time_taken: int  # seconds

# ---------- Student Progress Response ----------
class StudentProgress(BaseModel):
    student_id: int
    full_name: str
    average_score: float
    total_attempts: int
    topics_covered: List[str]
    last_activity: Optional[datetime]

# ---------- Teacher Report ----------
class TeacherReport(BaseModel):
    total_students: int
    average_class_score: float
    struggling_students: List[dict]  # student id, name, avg score
    most_difficult_topics: List[dict]  # topic name, avg score
    at_risk_students: List[dict]  # students with risk_score > threshold