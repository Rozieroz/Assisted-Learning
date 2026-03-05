"""
Async functions to interact with the database- to be used by the endpoints.
CRUD operations for database models.
All functions are async and use SQLAlchemy 1.4+ async syntax.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any

from app import models, schemas

logger = logging.getLogger(__name__)

# ---------- Student ----------
async def get_student(db: AsyncSession, student_id: int) -> Optional[models.Student]:
    result = await db.execute(select(models.Student).where(models.Student.id == student_id))
    return result.scalar_one_or_none()

async def get_students(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[models.Student]:
    result = await db.execute(select(models.Student).offset(skip).limit(limit))
    return result.scalars().all()

async def create_student(db: AsyncSession, student: schemas.StudentCreate) -> models.Student:
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)
    return db_student

# ---------- Quiz Attempt ----------
async def create_quiz_attempt(db: AsyncSession, attempt: schemas.QuizAttemptCreate) -> models.QuizAttempt:
    db_attempt = models.QuizAttempt(**attempt.model_dump())
    db.add(db_attempt)
    await db.commit()
    await db.refresh(db_attempt)
    return db_attempt

async def get_student_attempts(db: AsyncSession, student_id: int) -> List[models.QuizAttempt]:
    result = await db.execute(
        select(models.QuizAttempt)
        .where(models.QuizAttempt.student_id == student_id)
        .order_by(models.QuizAttempt.created_at.desc())
    )
    return result.scalars().all()

# ---------- Analytics ----------
async def get_student_avg_score(db: AsyncSession, student_id: int) -> float:
    """Calculate average score for a student across all attempts."""
    result = await db.execute(
        select(func.avg(models.QuizAttempt.score))
        .where(models.QuizAttempt.student_id == student_id)
    )
    avg = result.scalar()
    return avg if avg is not None else 0.0

async def get_topic_avg_scores(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return average score per topic (only for topics with attempts)."""
    stmt = (
        select(
            models.Topic.id,
            models.Topic.name,
            func.avg(models.QuizAttempt.score).label("avg_score")
        )
        .join(models.Quiz, models.Quiz.topic_id == models.Topic.id)
        .join(models.QuizAttempt, models.QuizAttempt.quiz_id == models.Quiz.id)
        .group_by(models.Topic.id, models.Topic.name)
        .order_by(func.avg(models.QuizAttempt.score))
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [{"topic_id": r.id, "topic_name": r.name, "avg_score": r.avg_score} for r in rows]

async def get_students_below_threshold(db: AsyncSession, threshold: float = 50.0) -> List[models.Student]:
    """Find students whose average score is below threshold."""
    subq = (
        select(models.QuizAttempt.student_id, func.avg(models.QuizAttempt.score).label("avg_score"))
        .group_by(models.QuizAttempt.student_id)
        .subquery()
    )
    stmt = (
        select(models.Student)
        .join(subq, models.Student.id == subq.c.student_id)
        .where(subq.c.avg_score < threshold)
    )
    result = await db.execute(stmt)
    return result.scalars().all()