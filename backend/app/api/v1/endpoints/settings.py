"""
Settings management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trade import ApiKey
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
        session_service = SessionService()
        sessions = session_service.get_user_sessions(str(current_user.id))
        
        return {
            "two_factor_enabled": current_user.totp_enabled or False,
            "last_password_change": None,  # TODO: Track password changes
            "active_sessions": len(sessions)
        }
    except Exception as e:
        logger.error("Failed to get security settings", error=str(e))
        return {
            "two_factor_enabled": False,
            "last_password_change": None,
            "active_sessions": 0
        }

@router.post("/2fa/enable")
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable two-factor authentication"""
    
    try:
        import pyotp
        import secrets
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate QR code URL
        qr_code_url = totp.provisioning_uri(
            name=current_user.email,
            issuer_name="TradeQuest"
        )
        
        # TODO: Store secret and backup codes in database
        # For now, just enable the flag
        current_user.totp_enabled = True
        db.commit()
        
        logger.info("2FA enabled", user_id=str(current_user.id))
        
        return {
            "message": "2FA enabled successfully",
            "secret": secret,
            "qr_code_url": qr_code_url,
            "backup_codes": backup_codes
        }
        
    except Exception as e:
        logger.error("2FA enable failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable 2FA: {str(e)}"
        )

@router.post("/2fa/disable")
async def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable two-factor authentication"""
    
    try:
        current_user.totp_enabled = False
        db.commit()
        
        logger.info("2FA disabled", user_id=str(current_user.id))
        
        return {"message": "2FA disabled successfully"}
        
    except Exception as e:
        logger.error("2FA disable failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable 2FA: {str(e)}"
        )

# Session management
@router.get("/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active sessions"""
    
    try:
        session_service = SessionService()
        sessions = session_service.get_user_sessions(str(current_user.id))
        
        # Mark current session (simplified - in real app, pass current session token)
        if sessions:
            sessions[0]["is_current"] = True
        
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
        session_service = SessionService()
        session_service.revoke_session(session_id)
        
        logger.info("Session revoked", user_id=str(current_user.id), session_id=session_id)
        
        return {"message": "Session revoked successfully"}
        
    except Exception as e:
        logger.error("Session revocation failed", error=str(e))
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
    
    try:
        api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
        
        keys_info = []
        for key in api_keys:
            # Mask the API key for security
            masked = key.key_enc[:4] + "..." + key.key_enc[-4:] if len(key.key_enc) > 8 else "****"
            keys_info.append({
                "id": key.id,
                "venue": key.venue,
                "created_at": key.created_at.isoformat(),
                "masked_key": masked
            })
        
        return {"api_keys": keys_info}
        
    except Exception as e:
        logger.error("Failed to get API keys", error=str(e))
        return {"api_keys": []}

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    
    try:
        api_key = db.query(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.user_id == current_user.id
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        db.delete(api_key)
        db.commit()
        
        logger.info("API key deleted", user_id=str(current_user.id), key_id=key_id, venue=api_key.venue)
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API key deletion failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
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
