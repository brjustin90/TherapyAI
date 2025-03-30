from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.therapy import TherapySession, TherapyMessage, SessionStatus
from app.schemas.therapy import (
    TherapySession as TherapySessionSchema,
    TherapySessionCreate,
    TherapySessionUpdate,
    TherapyMessage as TherapyMessageSchema,
    TherapyMessageCreate,
)

router = APIRouter()


@router.post("", response_model=TherapySessionSchema)
def create_therapy_session(
    *,
    db: Session = Depends(get_db),
    session_in: TherapySessionCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new therapy session
    """
    # Only users can create sessions for themselves
    if session_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    session = TherapySession(**session_in.dict())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=List[TherapySessionSchema])
def read_sessions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[SessionStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve therapy sessions
    """
    query = db.query(TherapySession).filter(TherapySession.user_id == current_user.id)
    
    if status:
        query = query.filter(TherapySession.status == status)
    
    if start_date:
        query = query.filter(TherapySession.scheduled_start >= start_date)
    
    if end_date:
        query = query.filter(TherapySession.scheduled_start <= end_date)
    
    query = query.order_by(TherapySession.scheduled_start.desc())
    sessions = query.offset(skip).limit(limit).all()
    
    return sessions


@router.get("/{session_id}", response_model=TherapySessionSchema)
def read_session(
    *,
    db: Session = Depends(get_db),
    session_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get therapy session by ID
    """
    session = db.query(TherapySession).filter(TherapySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return session


@router.put("/{session_id}", response_model=TherapySessionSchema)
def update_session(
    *,
    db: Session = Depends(get_db),
    session_id: int,
    session_in: TherapySessionUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a therapy session
    """
    session = db.query(TherapySession).filter(TherapySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    update_data = session_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{session_id}", response_model=TherapySessionSchema)
def delete_session(
    *,
    db: Session = Depends(get_db),
    session_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a therapy session
    """
    session = db.query(TherapySession).filter(TherapySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(session)
    db.commit()
    return session


@router.post("/{session_id}/messages", response_model=TherapyMessageSchema)
def create_therapy_message(
    *,
    db: Session = Depends(get_db),
    session_id: int,
    message_in: TherapyMessageCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new message in a therapy session
    """
    session = db.query(TherapySession).filter(TherapySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    message = TherapyMessage(**message_in.dict())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/{session_id}/messages", response_model=List[TherapyMessageSchema])
def read_session_messages(
    *,
    db: Session = Depends(get_db),
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all messages from a therapy session
    """
    session = db.query(TherapySession).filter(TherapySession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    messages = (
        db.query(TherapyMessage)
        .filter(TherapyMessage.session_id == session_id)
        .order_by(TherapyMessage.timestamp)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return messages 