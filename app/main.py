"""
Main FastAPI application.
Configures logging, CORS, and includes API routers.
Uses lifespan context manager instead of deprecated on_event.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import submit, progress, reports, questions, tts, stt

# Mount static files for frontend (if needed)
from fastapi.staticfiles import StaticFiles


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Kipaji Chetu API...")
    yield
    # Shutdown
    logger.info("Shutting down...")

# Create FastAPI instance with lifespan
app = FastAPI(
    title="Kipaji Chetu API",
    description="AI-powered personalized learning system with inclusive design",
    version="0.1.0",
    lifespan=lifespan,
)

# Serve static files (for frontend)
# access via http://localhost:8000/static/index.html
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# app.mount("/static", StaticFiles(directory="static"), name="static")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(submit.router, prefix="/api", tags=["Student Actions"])
app.include_router(progress.router, prefix="/api", tags=["Student Progress"])
app.include_router(reports.router, prefix="/api", tags=["Teacher Reports"])
app.include_router(questions.router, prefix="/api", tags=["Quiz Questions"])
app.include_router(tts.router, prefix="/api", tags=["Text-to-Speech"])
app.include_router(stt.router, prefix="/api", tags=["Speech-to-Text"])




@app.get("/")
async def root():
    return {"message": "Kipaji Chetu API is running."}


"""
run with: uvicorn app.main:app --reload - in the root directory of the project
"""