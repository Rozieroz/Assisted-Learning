"""
Seed script to populate the database with sample data:
- Create a demo teacher.
- Create a class.
- Create two students: John Doe and Jane Doe.
- Enrol them in the class.
- Insert a few topics (if not already present).
"""

import os
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv
from app import models
from app.database import Base

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the ASYNC database URL from .env
ASYNC_DB_URL = os.getenv("DATABASE_URL_ASYNC")
if not ASYNC_DB_URL:
    raise RuntimeError("DATABASE_URL_ASYNC not set in .env")

DB_SCHEMA = os.getenv("schema", "public")

async def seed():
    """Create async engine and seed data."""
    engine = create_async_engine(ASYNC_DB_URL, echo=True)

    # Create schema if not exists (using raw connection)
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        await conn.execute(text(f"SET search_path TO {DB_SCHEMA}"))

    # Create tables (if not already present)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a session for inserting data
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # 1. Create a teacher
        teacher = models.Teacher(
            name="Demo Teacher",
            email="teacher@kipaji.com",
            password_hash=""  # no auth for demo
        )
        db.add(teacher)
        await db.flush()  # to get teacher.id

        # 2. Create a class
        class_ = models.Class(
            name="Mathematics 101",
            class_code="MATH101",
            teacher_id=teacher.id,
            subject="Mathematics",
            description="Introductory math class"
        )
        db.add(class_)
        await db.flush()

        # 3. Create students
        student1 = models.Student(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            learning_mode="normal",
            accessibility_enabled=False,
            risk_score=0.0
        )
        student2 = models.Student(
            first_name="Jane",
            last_name="Doe",
            email="jane.doe@example.com",
            learning_mode="simplified",
            accessibility_enabled=True,
            risk_score=0.0
        )
        db.add_all([student1, student2])
        await db.flush()

        # 4. Enrol students in class
        enrolment1 = models.ClassStudent(class_id=class_.id, student_id=student1.id)
        enrolment2 = models.ClassStudent(class_id=class_.id, student_id=student2.id)
        db.add_all([enrolment1, enrolment2])

        # 5. Create some topics
        topics = [
            models.Topic(name="Algebra", description="Equations and variables", difficulty_level="medium"),
            models.Topic(name="Geometry", description="Shapes and angles", difficulty_level="hard"),
            models.Topic(name="Arithmetic", description="Basic operations", difficulty_level="easy"),
        ]
        db.add_all(topics)

        await db.commit()
        logger.info("Seed data inserted successfully!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())