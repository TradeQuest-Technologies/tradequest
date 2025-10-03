from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import secrets
import string
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.onboarding import UserSecurity
from app.schemas.auth import TwoFactorRequest
from app.services.totp_service import TOTPService
from app.services.sms_service import SMSService
from app.services.google_auth_service import GoogleAuthService
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary storage for verification codes (in production, use Redis)
verification_codes: Dict[str, Dict[str, Any]] = {}

@router.post("/setup/totp")
async def setup_totp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup TOTP 2FA for user"""
    try:
        # Generate TOTP setup
        secret, qr_code, backup_codes = TOTPService.setup_totp_for_user(db, current_user.id)
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "message": "Scan QR code with your authenticator app and enter the 6-digit code to complete setup"
        }
        
    except Exception as e:
        logger.error("TOTP setup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup TOTP"
        )

@router.post("/setup/email")
async def setup_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup Email 2FA for user - sends a 6-digit code to the account email"""
    try:
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        email_service = EmailService()
        await email_service.send_2fa_code_email(current_user.email, code)
        verification_codes[current_user.id] = {
            "code": code,
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        return {"message": f"Verification code sent to {current_user.email}"}
    except Exception as e:
        logger.error("Email 2FA setup failed", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to setup Email 2FA")

@router.post("/verify/email")
async def verify_email_setup(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify email 2FA code and enable email 2FA"""
    try:
        code = request.get("code")
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code is required")
        data = verification_codes.get(current_user.id)
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No verification initiated")
        if datetime.utcnow() > datetime.fromisoformat(data["expires_at"]):
            verification_codes.pop(current_user.id, None)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
        if code != data.get("code"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security:
            user_security = UserSecurity(user_id=current_user.id)
            db.add(user_security)
        user_security.two_factor_method = "email"
        db.commit()
        verification_codes.pop(current_user.id, None)
        return {"message": "Email 2FA enabled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Email 2FA verification failed", extra={"error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify Email 2FA")

@router.post("/verify/totp")
async def verify_totp_setup(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify TOTP setup with 6-digit code"""
    try:
        secret = request.get("secret")
        verification_code = request.get("code")
        backup_codes = request.get("backup_codes", [])
        
        if not secret or not verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Secret and verification code are required"
            )
        
        # Enable TOTP if verification succeeds
        success = TOTPService.enable_totp_for_user(
            db, current_user.id, secret, verification_code, backup_codes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        return {"message": "TOTP 2FA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("TOTP verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify TOTP"
        )

@router.post("/setup/sms")
async def setup_sms(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup SMS 2FA for user"""
    try:
        phone_number = request.get("phone_number")
        if not phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required"
            )
        
        # Validate and format phone number
        sms_service = SMSService()
        if not sms_service.validate_phone_number(phone_number):
            formatted_number = sms_service.format_phone_number(phone_number)
        else:
            formatted_number = phone_number
        
        # Generate verification code
        verification_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Send SMS
        sms_sent = sms_service.send_verification_code(formatted_number, verification_code)
        if not sms_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS verification code"
            )
        
        # Store verification code temporarily
        verification_codes[current_user.id] = {
            "code": verification_code,
            "phone_number": formatted_number,
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
        return {
            "message": f"SMS verification code sent to {formatted_number}",
            "phone_number": formatted_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SMS setup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup SMS 2FA"
        )

@router.post("/verify/sms")
async def verify_sms_setup(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify SMS setup with verification code"""
    try:
        verification_code = request.get("code")
        if not verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code is required"
            )
        
        # Check stored verification code
        stored_data = verification_codes.get(current_user.id)
        if not stored_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending SMS verification found"
            )
        
        # Check expiration
        expires_at = datetime.fromisoformat(stored_data["expires_at"])
        if datetime.utcnow() > expires_at:
            del verification_codes[current_user.id]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired"
            )
        
        # Verify code
        if stored_data["code"] != verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        # Enable SMS 2FA
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security:
            user_security = UserSecurity(user_id=current_user.id)
            db.add(user_security)
        
        user_security.phone_number = stored_data["phone_number"]
        user_security.phone_verified = True
        user_security.two_factor_method = "sms"
        
        db.commit()
        
        # Clean up verification code
        del verification_codes[current_user.id]
        
        return {"message": "SMS 2FA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("SMS verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify SMS"
        )

@router.post("/setup/google")
async def setup_google_auth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup Google OAuth 2FA"""
    try:
        google_service = GoogleAuthService()
        if not google_service.is_configured():
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google OAuth is not configured"
            )
        
        # Generate authorization URL
        state = f"{current_user.id}_{secrets.token_urlsafe(32)}"
        auth_url = google_service.generate_auth_url(state)
        
        return {
            "auth_url": auth_url,
            "state": state,
            "message": "Complete Google OAuth to enable 2FA"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google auth setup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup Google 2FA"
        )

@router.post("/verify/google")
async def verify_google_auth(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify Google OAuth and enable 2FA"""
    try:
        token = request.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token is required"
            )
        
        # Verify Google token
        google_service = GoogleAuthService()
        user_info = google_service.verify_token(token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token"
            )
        
        # Verify email matches
        if user_info["email"] != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email does not match your account"
            )
        
        # Enable Google 2FA
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if not user_security:
            user_security = UserSecurity(user_id=current_user.id)
            db.add(user_security)
        
        user_security.google_auth_enabled = True
        user_security.google_auth_secret = user_info["google_id"]
        user_security.two_factor_method = "google_auth"
        
        db.commit()
        
        return {"message": "Google 2FA enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google auth verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify Google auth"
        )

@router.get("/status")
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current 2FA status for user"""
    try:
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        
        if not user_security:
            return {
                "enabled": False,
                "method": None,
                "phone_number": None,
                "totp_enabled": False,
                "google_auth_enabled": False
            }
        
        return {
            "enabled": bool(user_security.two_factor_method),
            "method": user_security.two_factor_method,
            "phone_number": user_security.phone_number if user_security.phone_verified else None,
            "totp_enabled": user_security.totp_enabled,
            "google_auth_enabled": user_security.google_auth_enabled
        }
        
    except Exception as e:
        logger.error("Failed to get 2FA status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get 2FA status"
        )

@router.delete("/disable")
async def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA for user"""
    try:
        user_security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
        if user_security:
            user_security.two_factor_method = None
            user_security.totp_enabled = False
            user_security.phone_verified = False
            user_security.google_auth_enabled = False
            user_security.totp_secret = None
            user_security.google_auth_secret = None
            user_security.backup_codes_hash = None
        
        # Update user model
        current_user.totp_enabled = False
        
        db.commit()
        
        return {"message": "2FA disabled successfully"}
        
    except Exception as e:
        logger.error("Failed to disable 2FA", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )
