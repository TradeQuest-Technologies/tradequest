"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class MagicLinkRequest(BaseModel):
    email: EmailStr
    is_signup: bool = True  # Distinguish between signup and signin flows

class MagicLinkResponse(BaseModel):
    message: str = "Magic link sent to your email"
    user_exists: bool = False  # Indicate if user already exists

class PasswordLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class PasswordLoginResponse(BaseModel):
    requires_2fa: bool = False
    temp_token: Optional[str] = None
    message: str = "Login successful"
    two_factor_method: Optional[str] = None
    access_token: Optional[str] = None

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

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    two_factor_code: Optional[str] = None  # Required if 2FA is enabled

class ForgotPasswordResponse(BaseModel):
    message: str = "Password reset instructions sent to your email"
    requires_2fa: bool = False
    two_factor_method: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    # Note: 2FA verification happens before the reset link is sent, not here

class ResetPasswordResponse(BaseModel):
    message: str = "Password reset successful"
    # Note: No 2FA fields needed - verification already happened in forgot_password

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
