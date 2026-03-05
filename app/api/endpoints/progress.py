"""
--> Returns a summary of a student's performance.

GET /student-progress/{student_id} endpoint.
Provides aggregated progress data for a specific student.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app import models, schemas
from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/student-progress/{student_id}", response_model=schemas.StudentProgress)
async def get_student_progress(
    student_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Return progress summary for a student: average score, total attempts,
    topics covered, and last activity date.
    """
    # Check if student exists
    student = await db.get(models.Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get all attempts for the student
    attempts = await db.execute(
        select(models.QuizAttempt)
        .where(models.QuizAttempt.student_id == student_id)
    )
    attempts_list = attempts.scalars().all()

    if not attempts_list:
        # No attempts yet
        return schemas.StudentProgress(
            student_id=student_id,
            full_name=f"{student.first_name} {student.last_name}",
            average_score=0.0,
            total_attempts=0,
            topics_covered=[],
            last_activity=None
        )

    # Calculate average score
    avg_score = sum(a.score for a in attempts_list) / len(attempts_list)

    # Get distinct topics covered
    topic_ids = set()
    for a in attempts_list:
        quiz = await db.get(models.Quiz, a.quiz_id)
        if quiz:
            topic_ids.add(quiz.topic_id)

    topics = []
    for tid in topic_ids:
        topic = await db.get(models.Topic, tid)
        if topic:
            topics.append(topic.name)

    # Last activity
    last_activity = max(a.created_at for a in attempts_list)

    return schemas.StudentProgress(
        student_id=student_id,
        full_name=f"{student.first_name} {student.last_name}",
        average_score=avg_score,
        total_attempts=len(attempts_list),
        topics_covered=topics,
        last_activity=last_activity
    )