"""
Settings management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.onboarding import UserProfile, CoachPreferences, BacktestPreferences, NotificationSettings as NotificationSettingsModel
from app.services.session_service import SessionService

logger = structlog.get_logger()
router = APIRouter()

# Pydantic models
class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    alias: Optional[str] = None
    timezone: Optional[str] = None
    display_currency: Optional[str] = None
    birth_date: Optional[str] = None

class SecuritySettings(BaseModel):
    two_factor_enabled: bool = False
    last_password_change: Optional[str] = None
    active_sessions: int = 0

class NotificationPreferences(BaseModel):
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    email_frequency_limit: str = "immediate"
    sms_frequency_limit: str = "daily"

class TradingPreferences(BaseModel):
    default_symbol: str = "BTC/USDT"
    default_timeframe: str = "1m"
    fees_bps_default: float = 2.0
    slip_bps_default: float = 2.0
    mc_runs_default: int = 2000

class CoachPrefs(BaseModel):
    tone: str = "succinct"
    data_window_days: int = 30
    action_items_per_session: int = 1
    anonymized_optin: bool = False

class SessionInfo(BaseModel):
    id: str
    created_at: datetime
    last_used: datetime
    ip_address: str
    user_agent: str
    is_current: bool = False

class ApiKeyInfo(BaseModel):
    id: str
    venue: str
    created_at: datetime
    masked_key: str

# Profile endpoints
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile settings"""
    
    # Get or create user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        # Create default profile
        profile = UserProfile(
            user_id=current_user.id,
            timezone="UTC",
            display_currency="USD"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return {
        "first_name": profile.first_name or "",
        "last_name": profile.last_name or "",
        "alias": profile.alias or "",
        "email": current_user.email,
        "timezone": profile.timezone,
        "display_currency": profile.display_currency,
        "birth_date": profile.birth_date or ""
    }

@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile settings"""
    
    try:
        # Get or create profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
        
        # Update fields
        if profile_data.first_name is not None:
            profile.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            profile.last_name = profile_data.last_name
        if profile_data.alias is not None:
            profile.alias = profile_data.alias
        if profile_data.timezone is not None:
            profile.timezone = profile_data.timezone
        if profile_data.display_currency is not None:
            profile.display_currency = profile_data.display_currency
        if profile_data.birth_date is not None:
            profile.birth_date = profile_data.birth_date
        
        db.commit()
        
        logger.info("Profile updated", user_id=str(current_user.id))
        
        return {
            "message": "Profile updated successfully",
            "profile": profile_data.dict(exclude_unset=True)
        }
        
    except Exception as e:
        logger.error("Profile update failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

# Security endpoints
@router.get("/security")
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security settings"""
    
    try:
        from app.models.session import UserSession
        from app.models.onboarding import UserSecurity
        
        # Count active sessions from database
        active_sessions_count = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).count()
        
        # Check 2FA status from UserSecurity (this is what login actually checks)
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        is_2fa_enabled = user_security and user_security.two_factor_method in ["totp", "sms", "email"]
        two_factor_method = user_security.two_factor_method if user_security else None
        
        return {
            "two_factor_enabled": is_2fa_enabled,
            "two_factor_method": two_factor_method,  # "totp", "email", "sms", or None
            "last_password_change": current_user.last_password_change.isoformat() if current_user.last_password_change else None,
            "active_sessions": active_sessions_count
        }
    except Exception as e:
        logger.error("Failed to get security settings", error=str(e))
        return {
            "two_factor_enabled": False,
            "last_password_change": None,
            "active_sessions": 0
        }

class Enable2FARequest(BaseModel):
    method: str = "totp"  # "totp" or "email"

@router.post("/2fa/enable")
async def enable_2fa(
    request: Enable2FARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable two-factor authentication"""
    
    try:
        from app.models.onboarding import UserSecurity
        
        # Check if 2FA is already enabled
        if current_user.totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is already enabled. Please disable it first if you want to reconfigure."
            )
        
        # Validate method
        if request.method not in ["totp", "email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA method. Must be 'totp' or 'email'"
            )
        
        # Also enable in UserSecurity table (this is what login checks!)
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security:
            # Create UserSecurity if it doesn't exist
            user_security = UserSecurity(user_id=current_user.id)
            db.add(user_security)
        
        # Don't set method yet - will be set after verification
        user_security.two_factor_method = None
        user_security.totp_enabled = False
        
        if request.method == "totp":
            import pyotp
            import secrets
            import json
            from app.core.auth import get_password_hash
            
            # Generate TOTP secret
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            
            # Hash backup codes before storing
            hashed_backup_codes = [get_password_hash(code) for code in backup_codes]
            
            # Create TOTP object
            totp = pyotp.TOTP(secret)
            
            # Generate QR code URL
            qr_code_url = totp.provisioning_uri(
                name=current_user.email,
                issuer_name="TradeQuest"
            )
            
            # Store secret and hashed backup codes in User model (but don't enable yet)
            current_user.totp_secret = secret
            current_user.backup_codes = json.dumps(hashed_backup_codes)
            # Don't set totp_enabled = True yet - wait for verification
            
            db.commit()
            
            logger.info("TOTP 2FA setup initiated (pending verification)", user_id=str(current_user.id))
            
            return {
                "message": "TOTP setup initiated. Please scan QR code and verify with a test code.",
                "qr_code_url": qr_code_url,
                "backup_codes": backup_codes,  # Return unhashed codes to user (only time they see them)
                "requires_verification": True
            }
            
        elif request.method == "email":
            # For email 2FA, send a test code first
            from app.services.email_service import EmailService
            
            # Generate test code
            test_code = f"{int(datetime.utcnow().timestamp()) % 1000000:06d}"
            
            # Store test code temporarily (expires in 5 minutes)
            temp_2fa_codes[str(current_user.id)] = {
                "code": test_code,
                "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                "type": "setup_verification"
            }
            
            # Send test email
            email_service = EmailService()
            await email_service.send_2fa_code_email(current_user.email, test_code)
            
            db.commit()
            
            logger.info("Email 2FA setup initiated (pending verification)", user_id=str(current_user.id))
            
            return {
                "message": "Email 2FA setup initiated. Please check your email for a verification code.",
                "requires_verification": True
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("2FA enable failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable 2FA: {str(e)}"
        )

class Disable2FARequest(BaseModel):
    two_factor_code: str

class Verify2FASetupRequest(BaseModel):
    verification_code: str

@router.post("/2fa/verify-setup")
async def verify_2fa_setup(
    request: Verify2FASetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify 2FA setup with test code"""
    
    try:
        from app.models.onboarding import UserSecurity
        
        # Check if user has a pending 2FA setup
        if current_user.totp_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled"
            )
        
        # Get user security record
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security or user_security.two_factor_method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending 2FA setup found"
            )
        
        # Check if user has TOTP secret (TOTP setup)
        if current_user.totp_secret:
            # Verify TOTP code
            import pyotp
            totp = pyotp.TOTP(current_user.totp_secret)
            if not totp.verify(request.verification_code, valid_window=1):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code"
                )
            
            # Enable TOTP 2FA
            current_user.totp_enabled = True
            user_security.two_factor_method = "totp"
            user_security.totp_enabled = True
            
            db.commit()
            
            logger.info("TOTP 2FA verified and enabled", user_id=str(current_user.id))
            
            return {
                "message": "TOTP 2FA enabled successfully!",
                "method": "totp"
            }
        
        # Check if user has email verification code
        stored_data = temp_2fa_codes.get(str(current_user.id))
        if stored_data and stored_data.get("type") == "setup_verification":
            # Check expiration
            expires_at = datetime.fromisoformat(stored_data["expires_at"])
            if datetime.utcnow() > expires_at:
                del temp_2fa_codes[str(current_user.id)]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code expired. Please try setting up 2FA again."
                )
            
            # Verify code
            if stored_data["code"] != request.verification_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code"
                )
            
            # Enable email 2FA
            current_user.totp_enabled = True
            user_security.two_factor_method = "email"
            user_security.totp_enabled = True
            
            # Clean up verification code
            del temp_2fa_codes[str(current_user.id)]
            
            db.commit()
            
            logger.info("Email 2FA verified and enabled", user_id=str(current_user.id))
            
            return {
                "message": "Email 2FA enabled successfully!",
                "method": "email"
            }
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending 2FA setup found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("2FA verification failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify 2FA: {str(e)}"
        )

@router.post("/2fa/disable")
async def disable_2fa(
    request: Disable2FARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable two-factor authentication"""
    
    try:
        from app.models.onboarding import UserSecurity
        
        # Check if 2FA is enabled (check UserSecurity which is what login actually uses)
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security or not user_security.two_factor_method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Two-factor authentication is not enabled"
            )
        
        # user_security already queried above, no need to query again
        
        # Verify based on 2FA method
        if user_security.two_factor_method == "totp":
            # Verify TOTP code
            import pyotp
            if current_user.totp_secret:
                totp = pyotp.TOTP(current_user.totp_secret)
                if not totp.verify(request.two_factor_code, valid_window=1):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid two-factor authentication code"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA secret not found"
                )
        elif user_security.two_factor_method == "email":
            # Verify email code
            stored_data = temp_2fa_codes.get(str(current_user.id))
            if not stored_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No verification code found. Please request a new code."
                )
            
            # Check expiration
            expires_at = datetime.fromisoformat(stored_data["expires_at"])
            if datetime.utcnow() > expires_at:
                del temp_2fa_codes[str(current_user.id)]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code expired. Please request a new code."
                )
            
            # Verify code
            if stored_data["code"] != request.two_factor_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code"
                )
            
            # Clean up used code
            del temp_2fa_codes[str(current_user.id)]
        
        # Disable 2FA in User model
        current_user.totp_enabled = False
        current_user.totp_secret = None
        current_user.backup_codes = None
        
        # Also disable in UserSecurity table (this is what login checks!)
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if user_security:
            user_security.two_factor_method = None
            user_security.totp_enabled = False
        
        db.commit()
        
        logger.info("2FA disabled in both User and UserSecurity", user_id=str(current_user.id))
        
        return {"message": "2FA disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("2FA disable failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}"
        )

# 2FA code sending for sensitive operations
# In-memory store for temporary codes (use Redis in production)
temp_2fa_codes = {}

@router.post("/2fa/send-code")
async def send_2fa_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send 2FA code via email for password change or other sensitive operations"""
    
    try:
        from app.models.onboarding import UserSecurity
        from app.services.email_service import EmailService
        
        # Check if user has email-based 2FA
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security or user_security.two_factor_method != "email":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email-based 2FA is not enabled"
            )
        
        # Generate 6-digit code
        code = f"{int(datetime.utcnow().timestamp()) % 1000000:06d}"
        
        # Store code temporarily (expires in 5 minutes)
        temp_2fa_codes[str(current_user.id)] = {
            "code": code,
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
        # Send email
        email_service = EmailService()
        await email_service.send_2fa_code_email(current_user.email, code)
        
        logger.info("2FA code sent via email", user_id=str(current_user.id))
        
        return {"message": "Verification code sent to your email"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send 2FA code", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification code: {str(e)}"
        )

# Password change
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    two_factor_code: Optional[str] = None

@router.post("/password/change")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    try:
        from app.core.auth import verify_password, get_password_hash
        from app.models.onboarding import UserSecurity
        from datetime import datetime
        import json
        
        # Check if 2FA is actually enabled (check UserSecurity which is what login uses)
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        is_2fa_enabled = user_security and user_security.two_factor_method in ["totp", "sms", "email"]
        
        # Verify 2FA if enabled
        if is_2fa_enabled:
            if not request.two_factor_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Two-factor authentication code is required"
                )
            
            # Verify based on 2FA method
            if user_security.two_factor_method == "totp":
                # Verify TOTP code
                import pyotp
                if current_user.totp_secret:
                    totp = pyotp.TOTP(current_user.totp_secret)
                    if not totp.verify(request.two_factor_code, valid_window=1):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid two-factor authentication code"
                        )
            elif user_security.two_factor_method == "email":
                # Verify email code
                stored_data = temp_2fa_codes.get(str(current_user.id))
                if not stored_data:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No verification code found. Please request a new code."
                    )
                
                # Check expiration
                expires_at = datetime.fromisoformat(stored_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    del temp_2fa_codes[str(current_user.id)]
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verification code expired. Please request a new code."
                    )
                
                # Verify code
                if stored_data["code"] != request.two_factor_code:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid verification code"
                    )
                
                # Clean up used code
                del temp_2fa_codes[str(current_user.id)]
        
        # Verify current password
        if not current_user.password_hash or not verify_password(request.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Check password strength (minimum 8 characters)
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Check if new password was used before
        if current_user.password_history:
            try:
                password_history = json.loads(current_user.password_history)
                for old_hash in password_history:
                    if verify_password(request.new_password, old_hash):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Password was used recently. Please choose a different password."
                        )
            except json.JSONDecodeError:
                password_history = []
        else:
            password_history = []
        
        # Hash new password
        new_hash = get_password_hash(request.new_password)
        
        # Update password history (keep last 5 passwords)
        password_history.insert(0, current_user.password_hash)
        password_history = password_history[:5]
        
        # Update user
        current_user.password_hash = new_hash
        current_user.password_history = json.dumps(password_history)
        current_user.last_password_change = datetime.utcnow()
        db.commit()
        
        logger.info("Password changed", user_id=str(current_user.id))
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

# Session management
@router.get("/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active sessions"""
    
    try:
        from app.models.session import UserSession
        
        # Get all active sessions for user from database
        db_sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).order_by(UserSession.last_used.desc()).all()
        
        sessions = []
        for idx, sess in enumerate(db_sessions):
            sessions.append({
                "id": sess.id,
                "created_at": sess.created_at.isoformat() if sess.created_at else None,
                "last_used": sess.last_used.isoformat() if sess.last_used else None,
                "ip_address": sess.ip_address or "Unknown",
                "user_agent": sess.user_agent or "Unknown",
                "is_current": idx == 0  # Most recent session is current
            })
        
        logger.info("Sessions retrieved", user_id=str(current_user.id), count=len(sessions))
        
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error("Failed to get sessions", error=str(e))
        return {"sessions": []}

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    
    try:
        from app.models.session import UserSession
        
        # Find and revoke the session
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.is_active = False
        db.commit()
        
        logger.info("Session revoked", user_id=str(current_user.id), session_id=session_id)
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Session revocation failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}"
        )

# Notification preferences
@router.get("/notifications")
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification settings"""
    
    # Get or create notification settings
    settings = db.query(NotificationSettingsModel).filter(
        NotificationSettingsModel.user_id == current_user.id
    ).first()
    
    if not settings:
        # Create default settings
        settings = NotificationSettingsModel(
            user_id=current_user.id,
            email_enabled=True,
            push_enabled=True,
            sms_enabled=False,
            in_app_enabled=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "email_enabled": settings.email_enabled,
        "push_enabled": settings.push_enabled,
        "sms_enabled": settings.sms_enabled,
        "in_app_enabled": settings.in_app_enabled,
        "quiet_hours_start": settings.quiet_hours_start,
        "quiet_hours_end": settings.quiet_hours_end,
        "email_frequency_limit": settings.email_frequency_limit,
        "sms_frequency_limit": settings.sms_frequency_limit
    }

@router.put("/notifications")
async def update_notification_settings(
    settings_data: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification settings"""
    
    try:
        # Get or create settings
        settings = db.query(NotificationSettingsModel).filter(
            NotificationSettingsModel.user_id == current_user.id
        ).first()
        
        if not settings:
            settings = NotificationSettingsModel(user_id=current_user.id)
            db.add(settings)
        
        # Update fields
        settings.email_enabled = settings_data.email_enabled
        settings.push_enabled = settings_data.push_enabled
        settings.sms_enabled = settings_data.sms_enabled
        settings.in_app_enabled = settings_data.in_app_enabled
        settings.quiet_hours_start = settings_data.quiet_hours_start
        settings.quiet_hours_end = settings_data.quiet_hours_end
        settings.email_frequency_limit = settings_data.email_frequency_limit
        settings.sms_frequency_limit = settings_data.sms_frequency_limit
        
        db.commit()
        
        logger.info("Notification settings updated", user_id=str(current_user.id))
        
        return {
            "message": "Notification settings updated successfully",
            "settings": settings_data.dict()
        }
        
    except Exception as e:
        logger.error("Notification settings update failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification settings: {str(e)}"
        )

# Trading preferences
@router.get("/trading")
async def get_trading_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trading preferences"""
    
    # Get or create trading preferences
    prefs = db.query(BacktestPreferences).filter(
        BacktestPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = BacktestPreferences(
            user_id=current_user.id,
            default_symbol="BTC/USDT",
            default_timeframe="1m",
            fees_bps_default=2.0,
            slip_bps_default=2.0,
            mc_runs_default=2000
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return {
        "default_symbol": prefs.default_symbol,
        "default_timeframe": prefs.default_timeframe,
        "fees_bps_default": prefs.fees_bps_default,
        "slip_bps_default": prefs.slip_bps_default,
        "mc_runs_default": prefs.mc_runs_default
    }

@router.put("/trading")
async def update_trading_preferences(
    prefs_data: TradingPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update trading preferences"""
    
    try:
        # Get or create preferences
        prefs = db.query(BacktestPreferences).filter(
            BacktestPreferences.user_id == current_user.id
        ).first()
        
        if not prefs:
            prefs = BacktestPreferences(user_id=current_user.id)
            db.add(prefs)
        
        # Update fields
        prefs.default_symbol = prefs_data.default_symbol
        prefs.default_timeframe = prefs_data.default_timeframe
        prefs.fees_bps_default = prefs_data.fees_bps_default
        prefs.slip_bps_default = prefs_data.slip_bps_default
        prefs.mc_runs_default = prefs_data.mc_runs_default
        
        db.commit()
        
        logger.info("Trading preferences updated", user_id=str(current_user.id))
        
        return {
            "message": "Trading preferences updated successfully",
            "preferences": prefs_data.dict()
        }
        
    except Exception as e:
        logger.error("Trading preferences update failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update trading preferences: {str(e)}"
        )

# Coach preferences
@router.get("/coach")
async def get_coach_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI coach preferences"""
    
    # Get or create coach preferences
    prefs = db.query(CoachPreferences).filter(
        CoachPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = CoachPreferences(
            user_id=current_user.id,
            tone="succinct",
            data_window_days=30,
            action_items_per_session=1,
            anonymized_optin=False
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return {
        "tone": prefs.tone,
        "data_window_days": prefs.data_window_days,
        "action_items_per_session": prefs.action_items_per_session,
        "anonymized_optin": prefs.anonymized_optin
    }

@router.put("/coach")
async def update_coach_preferences(
    prefs_data: CoachPrefs,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update AI coach preferences"""
    
    try:
        # Get or create preferences
        prefs = db.query(CoachPreferences).filter(
            CoachPreferences.user_id == current_user.id
        ).first()
        
        if not prefs:
            prefs = CoachPreferences(user_id=current_user.id)
            db.add(prefs)
        
        # Update fields
        prefs.tone = prefs_data.tone
        prefs.data_window_days = prefs_data.data_window_days
        prefs.action_items_per_session = prefs_data.action_items_per_session
        prefs.anonymized_optin = prefs_data.anonymized_optin
        
        db.commit()
        
        logger.info("Coach preferences updated", user_id=str(current_user.id))
        
        return {
            "message": "Coach preferences updated successfully",
            "preferences": prefs_data.dict()
        }
        
    except Exception as e:
        logger.error("Coach preferences update failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update coach preferences: {str(e)}"
        )

# API Keys management
@router.get("/api-keys")
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's API keys"""
    # API keys feature removed - return empty list
    return {"api_keys": []}

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    
    # API keys feature removed
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="API key not found"
    )

# Billing & Subscription
@router.get("/billing")
async def get_billing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing and subscription information from Stripe"""
    
    try:
        from app.models.user import Subscription
        from app.services.stripe_service import StripeService
        import stripe
        
        # Get subscription from database
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription or not subscription.stripe_customer:
            return {
                "plan": subscription.plan if subscription else "free",
                "status": subscription.status if subscription else "active",
                "stripe_customer_id": None,
                "stripe_subscription_id": None,
                "current_period_end": None,
                "cancel_at_period_end": False,
                "payment_method": None
            }
        
        # Fetch real data from Stripe
        stripe_service = StripeService()
        
        # Get customer and subscription details
        try:
            customer = stripe.Customer.retrieve(subscription.stripe_customer)
            
            # Get subscription from Stripe
            stripe_subscription = None
            if subscription.stripe_subscription:
                try:
                    stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription)
                except:
                    pass
            
            # Get default payment method
            payment_method = None
            if customer.invoice_settings and customer.invoice_settings.default_payment_method:
                pm = stripe.PaymentMethod.retrieve(customer.invoice_settings.default_payment_method)
                payment_method = {
                    "brand": pm.card.brand if pm.card else None,
                    "last4": pm.card.last4 if pm.card else None,
                    "exp_month": pm.card.exp_month if pm.card else None,
                    "exp_year": pm.card.exp_year if pm.card else None
                }
            
            return {
                "plan": subscription.plan,
                "status": stripe_subscription.status if stripe_subscription else subscription.status,
                "stripe_customer_id": subscription.stripe_customer,
                "stripe_subscription_id": subscription.stripe_subscription,
                "current_period_end": stripe_subscription.current_period_end if stripe_subscription else None,
                "cancel_at_period_end": stripe_subscription.cancel_at_period_end if stripe_subscription else False,
                "payment_method": payment_method
            }
            
        except stripe.error.StripeError as e:
            logger.error("Stripe API error", error=str(e))
            # Return database info as fallback
            return {
                "plan": subscription.plan,
                "status": subscription.status or "active",
                "stripe_customer_id": subscription.stripe_customer,
                "stripe_subscription_id": subscription.stripe_subscription,
                "current_period_end": None,
                "cancel_at_period_end": False,
                "payment_method": None
            }
        
    except Exception as e:
        logger.error("Failed to get billing info", error=str(e))
        return {
            "plan": "free",
            "status": "active",
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
            "payment_method": None
        }

@router.post("/billing/portal")
async def create_billing_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe customer portal session for managing billing"""
    
    try:
        from app.models.user import Subscription
        from app.services.stripe_service import StripeService
        from app.core.config import settings
        
        # Get subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription or not subscription.stripe_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe customer found. Please subscribe first."
            )
        
        # Create portal session
        stripe_service = StripeService()
        return_url = f"{settings.FRONTEND_URL}/settings"
        
        portal_session = stripe_service.create_customer_portal_session(
            customer_id=subscription.stripe_customer,
            return_url=return_url
        )
        
        return {
            "url": portal_session["url"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create portal session", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )

@router.post("/billing/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel subscription at end of billing period"""
    
    try:
        from app.models.user import Subscription
        import stripe
        
        # Get subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription or not subscription.stripe_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        # Cancel subscription at period end in Stripe
        try:
            updated_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription,
                cancel_at_period_end=True
            )
            
            logger.info("Subscription cancelled", 
                       user_id=str(current_user.id), 
                       subscription_id=subscription.stripe_subscription)
            
            return {
                "message": "Subscription will be cancelled at the end of the billing period",
                "cancel_at_period_end": updated_subscription.cancel_at_period_end,
                "current_period_end": updated_subscription.current_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error("Stripe cancellation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel subscription", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

# Account deletion
@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data"""
    
    try:
        # TODO: Implement cascade deletion of all user data
        # For now, just delete the user
        
        logger.warning("Account deletion requested", user_id=str(current_user.id), email=current_user.email)
        
        # In production, you'd want to:
        # 1. Delete all trades
        # 2. Delete all journal entries
        # 3. Delete all strategies
        # 4. Delete all backtests
        # 5. Cancel any subscriptions
        # 6. Delete API keys
        # 7. Delete sessions
        # 8. Finally delete the user
        
        db.delete(current_user)
        db.commit()
        
        logger.info("Account deleted", user_id=str(current_user.id))
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        logger.error("Account deletion failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
