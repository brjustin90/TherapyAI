from typing import Any, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import json

from app.api.deps import get_current_user
from app.db.session import get_db
from app.core.config import settings
from app.models.user import User
from app.models.therapy import TherapySession, SessionType, SessionStatus

router = APIRouter()


@router.post("/create-session", response_model=Dict[str, Any])
async def create_video_session(
    *,
    db: Session = Depends(get_db),
    title: str = Body(..., embed=True),
    description: str = Body(None, embed=True),
    scheduled_start: datetime = Body(..., embed=True),
    duration_minutes: int = Body(60, embed=True),
    therapy_approach: str = Body("CBT", embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new video therapy session
    """
    # Calculate scheduled end time
    scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
    
    # Create therapy session
    session = TherapySession(
        user_id=current_user.id,
        session_type=SessionType.VIDEO,
        therapy_approach=therapy_approach,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        status=SessionStatus.SCHEDULED,
        title=title,
        description=description,
        is_recorded=False,  # Default to not recording
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "message": "Video session created successfully",
        "session_id": session.id,
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
    }


@router.post("/token", response_model=Dict[str, Any])
async def get_video_token(
    *,
    db: Session = Depends(get_db),
    session_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a token for connecting to a video session
    This would typically generate a token for a third-party video service like Twilio
    """
    session = db.query(TherapySession).filter(
        TherapySession.id == session_id,
        TherapySession.user_id == current_user.id,
        TherapySession.session_type == SessionType.VIDEO
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
        )
    
    # For a real implementation, this would generate a token for a service like Twilio
    # Here we're just creating a placeholder token structure
    
    # In production, use the following commented code to generate a real Twilio token
    """
    from twilio.jwt.access_token import AccessToken
    from twilio.jwt.access_token.grants import VideoGrant
    
    # Create access token with credentials
    token = AccessToken(settings.TWILIO_ACCOUNT_SID, 
                        settings.TWILIO_API_KEY, 
                        settings.TWILIO_API_SECRET,
                        identity=str(current_user.id))
    
    # Create a Video grant and add to token
    video_grant = VideoGrant(room=f"session-{session_id}")
    token.add_grant(video_grant)
    
    # Return token
    token_jwt = token.to_jwt()
    """
    
    # Placeholder for demo
    token_payload = {
        "session_id": session_id,
        "user_id": current_user.id,
        "exp": int((datetime.utcnow() + timedelta(hours=2)).timestamp()),
        "room": f"session-{session_id}"
    }
    
    # In a real app, this would be properly signed
    token_jwt = json.dumps(token_payload)
    
    return {
        "token": token_jwt,
        "room": f"session-{session_id}",
        "session_info": {
            "id": session.id,
            "title": session.title,
            "scheduled_start": session.scheduled_start,
            "scheduled_end": session.scheduled_end
        }
    }


@router.post("/join", response_model=Dict[str, Any])
async def join_video_session(
    *,
    db: Session = Depends(get_db),
    session_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Join a video therapy session and mark it as in progress
    """
    session = db.query(TherapySession).filter(
        TherapySession.id == session_id,
        TherapySession.user_id == current_user.id,
        TherapySession.session_type == SessionType.VIDEO
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
        )
    
    # Update session status if not already in progress
    if session.status == SessionStatus.SCHEDULED:
        session.status = SessionStatus.IN_PROGRESS
        session.actual_start = datetime.utcnow()
        db.add(session)
        db.commit()
    
    # Generate room connection info
    # In a real app, this would contain WebRTC connection details
    connection_info = {
        "room_id": f"session-{session_id}",
        "turn_servers": [
            {
                "urls": ["stun:stun.l.google.com:19302"]
            }
        ],
        "ice_servers": [
            {
                "urls": ["stun:stun.l.google.com:19302"]
            }
        ]
    }
    
    return {
        "message": "Joined video session",
        "session_id": session.id,
        "connection_info": connection_info
    }


@router.post("/end", response_model=Dict[str, Any])
async def end_video_session(
    *,
    db: Session = Depends(get_db),
    session_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    End a video therapy session
    """
    session = db.query(TherapySession).filter(
        TherapySession.id == session_id,
        TherapySession.user_id == current_user.id,
        TherapySession.session_type == SessionType.VIDEO
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
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
    
    # Calculate duration
    duration = session.duration_minutes()
    
    return {
        "message": "Video session ended successfully",
        "session_id": session.id,
        "duration_minutes": duration
    }


@router.post("/recording", response_model=Dict[str, Any])
async def manage_recording(
    *,
    db: Session = Depends(get_db),
    session_id: int = Body(..., embed=True),
    enable_recording: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Enable or disable recording for a video session
    """
    session = db.query(TherapySession).filter(
        TherapySession.id == session_id,
        TherapySession.user_id == current_user.id,
        TherapySession.session_type == SessionType.VIDEO
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video session not found"
        )
    
    # Update recording status
    session.is_recorded = enable_recording
    db.add(session)
    db.commit()
    
    message = "Recording enabled" if enable_recording else "Recording disabled"
    
    return {
        "message": message,
        "session_id": session.id,
        "is_recorded": enable_recording
    } 