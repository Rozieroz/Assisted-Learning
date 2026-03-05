"""
==> Returns teacher‑level analytics
GET /teacher-report endpoint.
Provides class-wide analytics: average scores, struggling students, difficult topics.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app import models, schemas, crud
from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/teacher-report", response_model=schemas.TeacherReport)
async def get_teacher_report(
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a teacher report with class summary.
    """
    # Total students
    total_students = await db.scalar(select(func.count(models.Student.id)))

    # Overall class average score
    avg_class_score = await db.scalar(select(func.avg(models.QuizAttempt.score)))
    if avg_class_score is None:
        avg_class_score = 0.0

    # Struggling students (average score < 50%)
    struggling = await crud.get_students_below_threshold(db, 50.0)
    struggling_list = [
        {"student_id": s.id, "name": f"{s.first_name} {s.last_name}", "avg_score": await crud.get_student_avg_score(db, s.id)}
        for s in struggling
    ]

    # Most difficult topics (lowest average scores)
    topic_avgs = await crud.get_topic_avg_scores(db)
    # Already ordered ascending (lowest first)
    difficult_topics = [
        {"topic_id": t["topic_id"], "topic_name": t["topic_name"], "avg_score": t["avg_score"]}
        for t in topic_avgs[:5]  # top 5 hardest
    ]

    # At-risk students (those with risk_score > 0.7, for example)
    at_risk_students = await db.execute(
        select(models.Student).where(models.Student.risk_score > 0.7)
    )
    at_risk = at_risk_students.scalars().all()
    at_risk_list = [
        {"student_id": s.id, "name": f"{s.first_name} {s.last_name}", "risk_score": s.risk_score}
        for s in at_risk
    ]

    return schemas.TeacherReport(
        total_students=total_students,
        average_class_score=avg_class_score,
        struggling_students=struggling_list,
        most_difficult_topics=difficult_topics,
        at_risk_students=at_risk_list
    )