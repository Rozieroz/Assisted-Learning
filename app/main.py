"""
Main FastAPI application.
Configures logging, CORS, and includes API routers.
Uses lifespan context manager instead of deprecated on_event.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import submit, progress, reports

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

@app.get("/")
async def root():
    return {"message": "Kipaji Chetu API is running."}