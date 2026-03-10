"""
CRUD operations for database models.
Async functions to interact with the database- to be used by the endpoints.
All functions are async and use SQLAlchemy 1.4+ async syntax.

contains functions to create and retrieve students, quiz attempts, and analytics data.
Also includes a function to log interactions with the AI for audit purposes, and functions 
    to update student difficulty and risk scores based on their performance trends.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any

from app import models, schemas

# For analytics, => scikit-learn's LinearRegression to analyze performance trends for risk scoring.
from sklearn.linear_model import LinearRegression


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


# ---------- Automated Feedback Logs ----------
#  function to log interactions with the AI for audit and analysis purposes.
# It stores the prompt and response, along with metadata about the student and quiz.
# This allows us to track how the AI is being used and analyze the effectiveness of the feedback.
async def log_automated_interaction(
    db: AsyncSession,
    student_id: int,
    quiz_id: int,
    prompt: str,
    response: str,
    simplified_mode: bool = False
) -> models.AIFeedbackLog:
    """
    Log an automated content generation interaction.
    Stores the prompt and response for audit and analysis.
    """
    log_entry = models.AIFeedbackLog(
        student_id=student_id,
        quiz_id=quiz_id,
        prompt=prompt,
        ai_response=response,
        simplified_mode=simplified_mode
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    logger.info(f"Logged automated interaction for student {student_id}")
    return log_entry


# recalculate a student's preferred difficulty based on recent quiz scores.
# This can be called after each quiz attempt to adjust the difficulty of future quizzes for that student.

async def update_student_difficulty(db: AsyncSession, student_id: int):
    """
    Recalculate student's preferred difficulty based on last 5 quiz attempts.
    If average score > 80% -> hard
    If average score < 50% -> easy
    Else -> medium

    => to be called in submit endpoint after storing the attempt to ensure we have the latest data for the student.
    """
    # Get last 5 attempts for the student
    result = await db.execute(
        select(models.QuizAttempt)
        .where(models.QuizAttempt.student_id == student_id)
        .order_by(models.QuizAttempt.created_at.desc())
        .limit(5)
    )
    attempts = result.scalars().all()
    
    if not attempts:
        return  # No attempts yet, keep current
    
    avg_score = sum(a.score for a in attempts) / len(attempts)
    
    new_difficulty = "medium"
    if avg_score >= 80:
        new_difficulty = "hard"
    elif avg_score <= 50:
        new_difficulty = "easy"
    
    # Update student record
    student = await db.get(models.Student, student_id)
    if student and student.preferred_difficulty != new_difficulty:
        student.preferred_difficulty = new_difficulty
        db.add(student)
        await db.commit()
        logger.info(f"Updated student {student_id} difficulty to {new_difficulty}")

# function that calculates risk scores for all students based on their recent performance trends.
async def update_risk_scores(db: AsyncSession):
    """Calculate risk scores for all students based on performance trends."""
    # Get all students
    students = await get_students(db)
    for student in students:
        # Get their last 10 attempts ordered by date
        attempts = await db.execute(
            select(models.QuizAttempt)
            .where(models.QuizAttempt.student_id == student.id)
            .order_by(models.QuizAttempt.created_at)
            .limit(10)
        )
        scores = [a.score for a in attempts.scalars().all()]
        if len(scores) < 3:
            continue  # Not enough data
        
        # Simple linear regression on attempt indices (0,1,2,...)
        X = list(range(len(scores)))
        model = LinearRegression()
        model.fit([[x] for x in X], scores)
        slope = model.coef_[0]
        
        # Risk score: high if average low and trend negative
        avg_score = sum(scores)/len(scores)
        risk = 0.0
        if avg_score < 50:
            risk = 0.7
        if slope < -2:  # dropping more than 2 points per attempt
            risk = max(risk, 0.8)
        elif slope < 0:
            risk = max(risk, 0.5)
        
        student.risk_score = risk
        db.add(student)
    await db.commit()