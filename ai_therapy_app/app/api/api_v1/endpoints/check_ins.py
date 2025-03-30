from typing import Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.therapy import CheckIn
from app.schemas.therapy import (
    CheckIn as CheckInSchema,
    CheckInCreate,
    CheckInUpdate,
)

router = APIRouter()


@router.post("", response_model=CheckInSchema)
def create_check_in(
    *,
    db: Session = Depends(get_db),
    check_in_in: CheckInCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new check-in
    """
    # Only users can create check-ins for themselves
    if check_in_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if user already has a check-in today
    today = datetime.utcnow().date()
    existing_checkin = (
        db.query(CheckIn)
        .filter(
            CheckIn.user_id == check_in_in.user_id,
            func.date(CheckIn.timestamp) == today
        )
        .first()
    )
    
    # If there's already a check-in today, update it instead of creating a new one
    if existing_checkin:
        update_data = check_in_in.dict(exclude={"user_id"})
        for field, value in update_data.items():
            setattr(existing_checkin, field, value)
        
        db.add(existing_checkin)
        db.commit()
        db.refresh(existing_checkin)
        return existing_checkin
    
    # Otherwise create a new check-in
    check_in = CheckIn(**check_in_in.dict())
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.get("", response_model=List[CheckInSchema])
def read_check_ins(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve check-ins
    """
    query = db.query(CheckIn).filter(CheckIn.user_id == current_user.id)
    
    if start_date:
        query = query.filter(CheckIn.timestamp >= start_date)
    
    if end_date:
        query = query.filter(CheckIn.timestamp <= end_date)
    
    query = query.order_by(CheckIn.timestamp.desc())
    check_ins = query.offset(skip).limit(limit).all()
    
    return check_ins


@router.get("/today", response_model=Optional[CheckInSchema])
def read_today_check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get today's check-in
    """
    today = datetime.utcnow().date()
    check_in = (
        db.query(CheckIn)
        .filter(
            CheckIn.user_id == current_user.id,
            func.date(CheckIn.timestamp) == today
        )
        .first()
    )
    
    return check_in


@router.get("/stats/mood", response_model=List[dict])
def get_mood_stats(
    db: Session = Depends(get_db),
    days: int = 30,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get mood stats for the last N days
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    check_ins = (
        db.query(CheckIn)
        .filter(
            CheckIn.user_id == current_user.id,
            CheckIn.timestamp >= start_date,
            CheckIn.mood_rating.isnot(None)
        )
        .order_by(CheckIn.timestamp)
        .all()
    )
    
    return [
        {
            "date": check_in.timestamp.date().isoformat(),
            "mood_rating": check_in.mood_rating,
            "stress_level": check_in.stress_level,
            "sleep_quality": check_in.sleep_quality
        }
        for check_in in check_ins
    ]


@router.get("/{check_in_id}", response_model=CheckInSchema)
def read_check_in(
    *,
    db: Session = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get check-in by ID
    """
    check_in = db.query(CheckIn).filter(CheckIn.id == check_in_id).first()
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
    if check_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return check_in


@router.put("/{check_in_id}", response_model=CheckInSchema)
def update_check_in(
    *,
    db: Session = Depends(get_db),
    check_in_id: int,
    check_in_in: CheckInUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a check-in
    """
    check_in = db.query(CheckIn).filter(CheckIn.id == check_in_id).first()
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
    if check_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    update_data = check_in_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(check_in, field, value)
    
    db.add(check_in)
    db.commit()
    db.refresh(check_in)
    return check_in


@router.delete("/{check_in_id}", response_model=CheckInSchema)
def delete_check_in(
    *,
    db: Session = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a check-in
    """
    check_in = db.query(CheckIn).filter(CheckIn.id == check_in_id).first()
    if not check_in:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
    if check_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(check_in)
    db.commit()
    return check_in 