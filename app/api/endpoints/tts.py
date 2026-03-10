"""
GET /tts endpoint.
Returns audio (MP3) for the provided text.
Supports optional voice and rate parameters.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.tts.service import tts_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tts")
async def text_to_speech(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query("sw-KE-ZuriNeural", description="Voice name (see Edge-TTS docs)"),
    rate: str = Query("+0%", description="Speaking rate: e.g., '-10%' for slower, '+10%' for faster")
):
    """
    Generate speech audio from text.
    Returns an MP3 file that can be played directly in the browser.
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text parameter is required")
    
    try:
        audio_bytes = await tts_service.synthesize(text, voice, rate)
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename=speech.mp3"}
        )
    except Exception as e:
        logger.error(f"TTS endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")