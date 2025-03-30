from sqlalchemy import Boolean, Column, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User model for authentication and profile information"""
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    phone_number = Column(String)
    
    # User preferences and settings
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Profile information
    bio = Column(Text)
    preferences = Column(JSON, default={})
    
    # Data permission settings - what data the user has allowed the app to access
    data_permissions = Column(JSON, default={})
    
    # Emergency contact information
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    emergency_contact_relation = Column(String)
    
    # Relationships
    therapy_sessions = relationship("TherapySession", back_populates="user")
    mental_health_data = relationship("MentalHealthData", back_populates="user")
    user_activities = relationship("UserActivity", back_populates="user")
    check_ins = relationship("CheckIn", back_populates="user") 