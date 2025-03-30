from sqlalchemy import Boolean, Column, String, Text, JSON, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.models.base import BaseModel


class TherapyApproach(enum.Enum):
    CBT = "Cognitive Behavioral Therapy"
    DBT = "Dialectical Behavior Therapy"
    MINDFULNESS = "Mindfulness-Based Cognitive Therapy"
    MOTIVATIONAL = "Motivational Interviewing"
    SOLUTION_FOCUSED = "Solution-Focused Brief Therapy"


class SessionType(enum.Enum):
    VOICE = "Voice"
    VIDEO = "Video"
    TEXT = "Text"
    CHECK_IN = "Check-in"


class SessionStatus(enum.Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    MISSED = "Missed"


class TherapySession(BaseModel):
    """Model for therapy sessions between user and AI"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    session_type = Column(Enum(SessionType), nullable=False)
    therapy_approach = Column(Enum(TherapyApproach), nullable=False)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    
    # Session metadata
    title = Column(String)
    description = Column(Text)
    goals = Column(JSON, default=[])
    notes = Column(Text)
    
    # For recordings (optional)
    recording_url = Column(String)
    is_recorded = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="therapy_sessions")
    messages = relationship("TherapyMessage", back_populates="session", cascade="all, delete-orphan")
    
    def duration_minutes(self) -> int:
        """Calculate the duration of the session in minutes"""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return int(delta.total_seconds() / 60)
        return 0


class TherapyMessage(BaseModel):
    """Model for messages exchanged during therapy sessions"""
    
    session_id = Column(Integer, ForeignKey("therapysession.id"), nullable=False)
    is_from_ai = Column(Boolean, default=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Message metadata
    emotion = Column(String)  # Detected emotion
    intent = Column(String)  # Detected intent
    therapy_technique = Column(String)  # Technique being used
    
    # Relationships
    session = relationship("TherapySession", back_populates="messages")


class MentalHealthData(BaseModel):
    """Model for storing mental health related data collected from the user"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    data_type = Column(String, nullable=False)  # e.g., "sleep", "mood", "activity"
    source = Column(String)  # e.g., "phone_sensors", "user_input", "wearable"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # The actual data, structure depends on data_type
    data = Column(JSON, nullable=False)
    
    # Analysis results
    analysis = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="mental_health_data")


class UserActivity(BaseModel):
    """Model for tracking user activities and behaviors"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    activity_type = Column(String, nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Activity details
    details = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="user_activities")


class CheckIn(BaseModel):
    """Model for daily check-ins with the user"""
    
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    mood_rating = Column(Integer)  # Scale of 1-10
    stress_level = Column(Integer)  # Scale of 1-10
    sleep_quality = Column(Integer)  # Scale of 1-10
    
    # User provided notes
    notes = Column(Text)
    
    # AI analysis of the check-in
    analysis = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="check_ins") 