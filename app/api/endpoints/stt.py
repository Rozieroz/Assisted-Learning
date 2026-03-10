"""
POST /stt endpoint.
Transcribes uploaded audio using Groq Whisper.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from groq import Groq
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Groq client (reuse from automated service if possible)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(..., description="Audio file (mp3, wav, etc.)")
):
    """
    Transcribe an audio file using Groq's Whisper model.
    Returns the transcribed text.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    try:
        # Read file content
        content = await file.read()
        
        # Create a temporary file-like object for Groq
        # Groq expects a file-like object with a name attribute
        from io import BytesIO
        audio_file = BytesIO(content)
        audio_file.name = file.filename  # Groq uses the extension to determine format
        
        transcription = groq_client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",  # Groq's Whisper model
            response_format="text"
        )
        
        logger.info(f"Transcribed {len(content)} bytes of audio")
        return {"text": transcription}
    
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")