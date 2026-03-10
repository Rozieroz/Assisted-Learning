"""
POST /submit-answer endpoint with Groq-powered feedback.

Records a student's quiz attempt and returns basic result.
--> This endpoint accepts a student's answer submission, evaluates it against the correct answer, 
    stores the attempt in the database, and returns the recorded attempt with correctness and score.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, models
from app.database import get_db
from app.automated.client import automated_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/submit-answer", response_model=schemas.QuizAttemptWithFeedback)
async def submit_answer(
    submission: schemas.AnswerSubmission,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept a student's answer, evaluate it, generate AI feedback,
    store the attempt and feedback log, and return the recorded attempt with feedback.
    """
    # Fetch quiz and student
    quiz = await db.get(models.Quiz, submission.quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    student = await db.get(models.Student, submission.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Determine correctness and score
    is_correct = (submission.selected_answer == quiz.correct_answer)
    score = 100.0 if is_correct else 0.0
    
    # Generate feedback using Groq
    simplified_mode = student.learning_mode == "simplified" or student.accessibility_enabled
    feedback_text = await automated_service.generate_feedback(
        question=quiz.question,
        user_answer=submission.selected_answer,
        correct_answer=quiz.correct_answer,
        is_correct=is_correct,
        simplified=simplified_mode
    )
    
    # Prepare attempt data
    attempt_data = schemas.QuizAttemptCreate(
        student_id=submission.student_id,
        quiz_id=submission.quiz_id,
        selected_answer=submission.selected_answer,
        is_correct=is_correct,
        score=score,
        time_taken=submission.time_taken,
        attempt_number=1  # Placeholder; could be computed
    )
    
    try:
        # Store attempt in database
        attempt = await crud.create_quiz_attempt(db, attempt_data)
        
        # Log the automated(ai) interaction for audit
        await crud.log_automated_interaction(
            db=db,
            student_id=student.id,
            quiz_id=quiz.id,
            prompt=f"Q: {quiz.question}\nUser: {submission.selected_answer}\nCorrect: {quiz.correct_answer}",
            response=feedback_text,
            simplified_mode=simplified_mode
        )
        
        # Attach feedback to the attempt object (will be included in response)
        attempt.feedback = feedback_text
        
        logger.info(f"Stored attempt {attempt.id} for student {submission.student_id}")
        
    except Exception as e:
        logger.error(f"Failed to store attempt or log interaction: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    
    # call update_student_difficulty after storing the attempt to ensure we have the latest data for the student
    await crud.update_student_difficulty(db, submission.student_id)

    # Generate TTS URL for the feedback text which can be used by frontend to fetch audio
    tts_url = f"/api/tts?text={quote(feedback_text)}"

    return attempt

