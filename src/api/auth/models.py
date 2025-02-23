from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    tier: str = "free_tier"
    scopes: List[str] = ["read"]

class UserCreate(UserBase):
    """User creation model."""
    password: str
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    tier: Optional[str] = None
    scopes: Optional[List[str]] = None

class UserInDB(UserBase):
    """User database model."""
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime

class Token(BaseModel):
    """Authentication token model."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None 