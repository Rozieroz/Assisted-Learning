"""
SQLAlchemy ORM models corresponding to the database tables.
All tables reside in the configured schema.

Map the tables created in 01_create_tables.sql to SQLAlchemy models. Use __table_args__ to set the schema
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Text,
    CheckConstraint, UniqueConstraint, Index, TIMESTAMP
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import os

# Ensure schema is always lowercase and defaults to 'public'
SCHEMA = os.getenv("SCHEMA", "public").lower()


class Student(Base):
    __tablename__ = "students"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    learning_mode = Column(String(50), default="normal")
    accessibility_enabled = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    performance_logs = relationship("PerformanceLog", back_populates="student")
    ai_feedback_logs = relationship("AIFeedbackLog", back_populates="student")
    teacher_notes = relationship("TeacherNote", back_populates="student")
    classes = relationship("ClassStudent", back_populates="student")



class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    difficulty_level = Column(String(50), default="medium")
    created_at = Column(TIMESTAMP, server_default=func.now())

    quizzes = relationship("Quiz", back_populates="topic")
    performance_logs = relationship("PerformanceLog", back_populates="topic")


class Quiz(Base):
    __tablename__ = "quizzes"
    __table_args__ = (
        CheckConstraint("correct_answer IN ('A','B','C','D')", name="check_correct_answer"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey(f"{SCHEMA}.topics.id", ondelete="CASCADE"))
    question = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)
    difficulty_level = Column(String(50))
    ai_generated = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    topic = relationship("Topic", back_populates="quizzes")
    attempts = relationship("QuizAttempt", back_populates="quiz")
    feedback_logs = relationship("AIFeedbackLog", back_populates="quiz")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint("selected_answer IN ('A','B','C','D')", name="check_selected_answer"),
        CheckConstraint("score >= 0 AND score <= 100", name="check_score_range"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA}.students.id", ondelete="CASCADE"))
    quiz_id = Column(Integer, ForeignKey(f"{SCHEMA}.quizzes.id", ondelete="CASCADE"))
    selected_answer = Column(String(1))
    is_correct = Column(Boolean)
    score = Column(Float)  # 0-100
    time_taken = Column(Integer)  # seconds
    attempt_number = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship("Student", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")


class PerformanceLog(Base):
    __tablename__ = "performance_logs"
    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", name="unique_student_topic"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA}.students.id", ondelete="CASCADE"))
    topic_id = Column(Integer, ForeignKey(f"{SCHEMA}.topics.id", ondelete="CASCADE"))
    average_score = Column(Float)
    improvement_rate = Column(Float)
    mastery_level = Column(Float)
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="performance_logs")
    topic = relationship("Topic", back_populates="performance_logs")


class AIFeedbackLog(Base):
    __tablename__ = "ai_feedback_logs"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA}.students.id", ondelete="CASCADE"))
    quiz_id = Column(Integer, ForeignKey(f"{SCHEMA}.quizzes.id"))
    prompt = Column(Text)
    ai_response = Column(Text)
    simplified_mode = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship("Student", back_populates="ai_feedback_logs")
    quiz = relationship("Quiz", back_populates="feedback_logs")


class TeacherNote(Base):
    __tablename__ = "teacher_notes"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA}.students.id", ondelete="CASCADE"))
    note = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    student = relationship("Student", back_populates="teacher_notes")

# =============================================================
# ADVANCE THE PROJECT - added in scripts/01_create_tables.sql
# =================================================================
class Teacher(Base):
    __tablename__ = "teachers"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    classes = relationship("Class", back_populates="teacher")


class Class(Base):
    __tablename__ = "classes"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    class_code = Column(String(20), unique=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey(f"{SCHEMA}.teachers.id", ondelete="CASCADE"))
    subject = Column(String(100))
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    teacher = relationship("Teacher", back_populates="classes")
    students = relationship("ClassStudent", back_populates="class_")


class ClassStudent(Base):
    __tablename__ = "class_students"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="unique_class_student"),
        {"schema": SCHEMA}
    )

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey(f"{SCHEMA}.classes.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey(f"{SCHEMA}.students.id", ondelete="CASCADE"))
    enrolled_at = Column(TIMESTAMP, server_default=func.now())

    class_ = relationship("Class", back_populates="students")
    student = relationship("Student", back_populates="classes")

"""
Table	            Purpose
students	        users
topics	            subjects
quizzes	            questions
quiz_attempts	    answers
performance_logs	progress
ai_feedback_logs	AI explanations
teacher_notes	    teacher comments
"""