from typing import Optional, Dict, List
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[Dict] = None
    data_permissions: Optional[Dict] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    @validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Properties to return via API
class User(UserBase):
    id: int
    bio: Optional[str] = None
    preferences: Dict = {}
    data_permissions: Dict = {}
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# Additional properties stored in DB
class UserInDB(User):
    hashed_password: str 