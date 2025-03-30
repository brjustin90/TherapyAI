from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime

from app.models.therapy import TherapyApproach, SessionType, SessionStatus


# TherapySession Schemas
class TherapySessionBase(BaseModel):
    session_type: SessionType
    therapy_approach: TherapyApproach
    scheduled_start: datetime
    scheduled_end: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[List[str]] = None
    is_recorded: bool = False


class TherapySessionCreate(TherapySessionBase):
    user_id: int


class TherapySessionUpdate(BaseModel):
    session_type: Optional[SessionType] = None
    therapy_approach: Optional[TherapyApproach] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: Optional[SessionStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[List[str]] = None
    notes: Optional[str] = None
    is_recorded: Optional[bool] = None
    recording_url: Optional[str] = None


class TherapySession(TherapySessionBase):
    id: int
    user_id: int
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: SessionStatus
    notes: Optional[str] = None
    recording_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
    
    @property
    def duration_minutes(self) -> int:
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return int(delta.total_seconds() / 60)
        return 0


# TherapyMessage Schemas
class TherapyMessageBase(BaseModel):
    content: str
    is_from_ai: bool = False
    emotion: Optional[str] = None
    intent: Optional[str] = None
    therapy_technique: Optional[str] = None


class TherapyMessageCreate(TherapyMessageBase):
    session_id: int


class TherapyMessageUpdate(BaseModel):
    content: Optional[str] = None
    emotion: Optional[str] = None
    intent: Optional[str] = None
    therapy_technique: Optional[str] = None


class TherapyMessage(TherapyMessageBase):
    id: int
    session_id: int
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# MentalHealthData Schemas
class MentalHealthDataBase(BaseModel):
    data_type: str
    source: Optional[str] = None
    data: Dict[str, Any]


class MentalHealthDataCreate(MentalHealthDataBase):
    user_id: int


class MentalHealthDataUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None


class MentalHealthData(MentalHealthDataBase):
    id: int
    user_id: int
    timestamp: datetime
    analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# CheckIn Schemas
class CheckInBase(BaseModel):
    mood_rating: Optional[int] = None
    stress_level: Optional[int] = None
    sleep_quality: Optional[int] = None
    notes: Optional[str] = None
    
    @validator('mood_rating', 'stress_level', 'sleep_quality')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Rating must be between 1 and 10')
        return v


class CheckInCreate(CheckInBase):
    user_id: int


class CheckInUpdate(CheckInBase):
    analysis: Optional[Dict[str, Any]] = None


class CheckIn(CheckInBase):
    id: int
    user_id: int
    timestamp: datetime
    analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# UserActivity Schemas
class UserActivityBase(BaseModel):
    activity_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class UserActivityCreate(UserActivityBase):
    user_id: int


class UserActivityUpdate(UserActivityBase):
    pass


class UserActivity(UserActivityBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True 