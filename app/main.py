"""
Main FastAPI application.
Configures logging, CORS, and includes API routers.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import submit, progress, reports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(
    title="Kipaji Chetu API",
    description="AI-powered personalized learning system with inclusive design",
    version="0.1.0",
)

# CORS middleware (allow frontend during development)
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

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Kipaji Chetu API...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")