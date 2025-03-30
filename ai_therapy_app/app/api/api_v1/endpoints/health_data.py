from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db, get_mongo_db
from app.models.user import User
from app.models.therapy import MentalHealthData
from app.schemas.therapy import (
    MentalHealthData as MentalHealthDataSchema,
    MentalHealthDataCreate,
    MentalHealthDataUpdate,
)

router = APIRouter()


@router.post("", response_model=MentalHealthDataSchema)
def create_health_data(
    *,
    db: Session = Depends(get_db),
    health_data_in: MentalHealthDataCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new mental health data
    """
    # Only users can create data for themselves
    if health_data_in.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    health_data = MentalHealthData(**health_data_in.dict())
    db.add(health_data)
    db.commit()
    db.refresh(health_data)
    return health_data


@router.get("", response_model=List[MentalHealthDataSchema])
def read_health_data(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    data_type: Optional[str] = None,
    source: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve mental health data
    """
    query = db.query(MentalHealthData).filter(MentalHealthData.user_id == current_user.id)
    
    if data_type:
        query = query.filter(MentalHealthData.data_type == data_type)
    
    if source:
        query = query.filter(MentalHealthData.source == source)
    
    if start_date:
        query = query.filter(MentalHealthData.timestamp >= start_date)
    
    if end_date:
        query = query.filter(MentalHealthData.timestamp <= end_date)
    
    query = query.order_by(MentalHealthData.timestamp.desc())
    health_data = query.offset(skip).limit(limit).all()
    
    return health_data


@router.get("/{health_data_id}", response_model=MentalHealthDataSchema)
def read_health_data_by_id(
    *,
    db: Session = Depends(get_db),
    health_data_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get mental health data by ID
    """
    health_data = db.query(MentalHealthData).filter(MentalHealthData.id == health_data_id).first()
    if not health_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health data not found"
        )
    if health_data.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return health_data


@router.put("/{health_data_id}", response_model=MentalHealthDataSchema)
def update_health_data(
    *,
    db: Session = Depends(get_db),
    health_data_id: int,
    health_data_in: MentalHealthDataUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update mental health data
    """
    health_data = db.query(MentalHealthData).filter(MentalHealthData.id == health_data_id).first()
    if not health_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health data not found"
        )
    if health_data.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    update_data = health_data_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(health_data, field, value)
    
    db.add(health_data)
    db.commit()
    db.refresh(health_data)
    return health_data


@router.delete("/{health_data_id}", response_model=MentalHealthDataSchema)
def delete_health_data(
    *,
    db: Session = Depends(get_db),
    health_data_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete mental health data
    """
    health_data = db.query(MentalHealthData).filter(MentalHealthData.id == health_data_id).first()
    if not health_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health data not found"
        )
    if health_data.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db.delete(health_data)
    db.commit()
    return health_data


@router.get("/types", response_model=List[str])
def get_data_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all available data types
    """
    data_types = (
        db.query(MentalHealthData.data_type)
        .filter(MentalHealthData.user_id == current_user.id)
        .distinct()
        .all()
    )
    return [data_type[0] for data_type in data_types]


@router.get("/sources", response_model=List[str])
def get_data_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get all available data sources
    """
    sources = (
        db.query(MentalHealthData.source)
        .filter(MentalHealthData.user_id == current_user.id)
        .distinct()
        .all()
    )
    return [source[0] for source in sources if source[0]] 