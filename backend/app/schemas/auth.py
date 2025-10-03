"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkResponse(BaseModel):
    message: str = "Magic link sent to your email"

class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordLoginResponse(BaseModel):
    requires_2fa: bool = False
    temp_token: Optional[str] = None
    message: str = "Login successful"
    two_factor_method: Optional[str] = None

class TwoFactorRequest(BaseModel):
    temp_token: str
    code: str
    remember_me: bool = False

class TokenConsumeRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    plan: str = "free"
    alias: Optional[str] = None
    legal_name: Optional[str] = None
    first_name: Optional[str] = None
    
    class Config:
        from_attributes = True
