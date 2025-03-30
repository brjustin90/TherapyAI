from typing import Any, Dict
import base64
import tempfile
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import speech_recognition as sr
import pyttsx3
import io
from openai import OpenAI

from app.api.deps import get_current_user
from app.db.session import get_db, get_redis
from app.core.config import settings
from app.models.user import User
from app.models.therapy import TherapySession, TherapyMessage, SessionType, SessionStatus

router = APIRouter()


@router.post("/transcribe", response_model=Dict[str, str])
async def transcribe_audio(
    *,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Transcribe audio to text
    """
    try:
        # Save the uploaded audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        # Use speech recognition to transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
        
        # Remove the temporary file
        os.unlink(temp_audio_path)
        
        return {"text": text}
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'temp_audio_path' in locals():
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transcribing audio: {str(e)}"
        )


@router.post("/synthesize", response_class=StreamingResponse)
async def synthesize_speech(
    *,
    db: Session = Depends(get_db),
    text: str = Body(..., embed=True),
    voice_id: str = Body("default", embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Convert text to speech and return audio stream
    """
    try:
        # Initialize text-to-speech engine
        engine = pyttsx3.init()
        
        # Set voice if available
        voices = engine.getProperty('voices')
        for voice in voices:
            if voice_id in voice.id:
                engine.setProperty('voice', voice.id)
                break
        
        # Set default properties
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        
        # Create a bytes buffer for the audio
        with io.BytesIO() as buffer:
            # Save speech to buffer
            engine.save_to_file(text, 'temp.wav')
            engine.runAndWait()
            
            # Read the generated audio file
            with open('temp.wav', 'rb') as audio_file:
                buffer.write(audio_file.read())
            
            # Clean up
            os.remove('temp.wav')
            
            # Return the audio as streaming response
            buffer.seek(0)
            return StreamingResponse(
                buffer, 
                media_type="audio/wav",
                headers={"Content-Disposition": "attachment; filename=speech.wav"}
            )
    
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists('temp.wav'):
            try:
                os.remove('temp.wav')
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error synthesizing speech: {str(e)}"
        )


@router.post("/chat", response_model=Dict[str, Any])
async def voice_chat(
    *,
    db: Session = Depends(get_db),
    redis = Depends(get_redis),
    user_message: str = Body(..., embed=True),
    session_id: int = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Process a voice chat message and return AI response
    """
    # Check if session exists or create a new one
    if session_id:
        session = db.query(TherapySession).filter(
            TherapySession.id == session_id,
            TherapySession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Update session if it's not already in progress
        if session.status == SessionStatus.SCHEDULED:
            session.status = SessionStatus.IN_PROGRESS
            session.actual_start = datetime.utcnow()
            db.add(session)
            db.commit()
    else:
        # Create a new voice session
        session = TherapySession(
            user_id=current_user.id,
            session_type=SessionType.VOICE,
            therapy_approach="CBT",  # Default approach
            scheduled_start=datetime.utcnow(),
            scheduled_end=datetime.utcnow(),
            actual_start=datetime.utcnow(),
            status=SessionStatus.IN_PROGRESS,
            title="Voice Chat Session",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Store user message
    user_message_obj = TherapyMessage(
        session_id=session.id,
        is_from_ai=False,
        content=user_message,
    )
    db.add(user_message_obj)
    db.commit()
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=settings.LLM_API_KEY)
        
        # Get conversation history from Redis
        conversation_key = f"conversation:{current_user.id}:{session.id}"
        conversation_history = redis.lrange(conversation_key, 0, -1)
        
        # Convert bytes to strings
        conversation_history = [msg.decode('utf-8') for msg in conversation_history]
        
        # If no history, initialize with system message
        if not conversation_history:
            system_message = (
                "You are an AI mental health therapist. Be empathetic, supportive, and helpful. "
                "Respect privacy and maintain confidentiality. If the user appears to be in crisis, "
                "suggest they contact emergency services. Focus on evidence-based therapeutic approaches."
            )
            conversation_history = [f"system: {system_message}"]
        
        # Add user message to history
        conversation_history.append(f"user: {user_message}")
        
        # Call LLM for response
        messages = [
            {"role": "system", "content": conversation_history[0].replace("system: ", "")}
        ]
        
        for msg in conversation_history[1:]:
            if msg.startswith("user: "):
                messages.append({"role": "user", "content": msg.replace("user: ", "")})
            elif msg.startswith("assistant: "):
                messages.append({"role": "assistant", "content": msg.replace("assistant: ", "")})
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        
        ai_response = response.choices[0].message.content
        
        # Store AI message
        ai_message_obj = TherapyMessage(
            session_id=session.id,
            is_from_ai=True,
            content=ai_response,
        )
        db.add(ai_message_obj)
        db.commit()
        
        # Update conversation history in Redis
        conversation_history.append(f"assistant: {ai_response}")
        redis.delete(conversation_key)
        for msg in conversation_history:
            redis.rpush(conversation_key, msg)
        
        # Set expiration time for conversation history (24 hours)
        redis.expire(conversation_key, 60 * 60 * 24)
        
        return {
            "response": ai_response,
            "session_id": session.id,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice chat: {str(e)}"
        )


@router.post("/end-session", response_model=Dict[str, Any])
async def end_voice_session(
    *,
    db: Session = Depends(get_db),
    session_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    End a voice chat session
    """
    session = db.query(TherapySession).filter(
        TherapySession.id == session_id,
        TherapySession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.status != SessionStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in progress"
        )
    
    # Update session status
    session.status = SessionStatus.COMPLETED
    session.actual_end = datetime.utcnow()
    db.add(session)
    db.commit()
    
    return {
        "message": "Session ended successfully",
        "session_id": session.id,
        "duration_minutes": session.duration_minutes(),
    } 