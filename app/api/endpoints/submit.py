"""
POST /submit-answer endpoint.
Records a student's quiz attempt and returns basic result.
--> This endpoint accepts a student's answer submission, evaluates it against the correct answer, 
    stores the attempt in the database, and returns the recorded attempt with correctness and score.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, models
from app.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/submit-answer", response_model=schemas.QuizAttempt)
async def submit_answer(
    submission: schemas.AnswerSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept a student's answer, evaluate it, store the attempt,
    and return the recorded attempt with correctness and score.
    """
    # Fetch the quiz to get correct answer
    quiz = await db.get(models.Quiz, submission.quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Determine if answer is correct
    is_correct = (submission.selected_answer == quiz.correct_answer)
    score = 100.0 if is_correct else 0.0  # Simple scoring

    # Create attempt record
    attempt_data = schemas.QuizAttemptCreate(
        student_id=submission.student_id,
        quiz_id=submission.quiz_id,
        selected_answer=submission.selected_answer,
        is_correct=is_correct,
        score=score,
        time_taken=submission.time_taken,
        attempt_number=1  # Can be enhanced by counting previous attempts
    )
    try:
        attempt = await crud.create_quiz_attempt(db, attempt_data)
        logger.info(f"Stored attempt {attempt.id} for student {submission.student_id}")
    except Exception as e:
        logger.error(f"Failed to store attempt: {e}")
        raise HTTPException(status_code=500, detail="Database error")

    return attempt