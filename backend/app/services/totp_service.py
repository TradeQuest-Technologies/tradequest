import pyotp
import qrcode
import io
import base64
from typing import Optional, Tuple
import secrets
import string
from sqlalchemy.orm import Session
from app.models.onboarding import UserSecurity
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class TOTPService:
    """TOTP (Time-based One-Time Password) service for 2FA"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email: str, secret: str, issuer: str = "TradeQuest") -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Convert to base64 string
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp(secret: str, token: str, window: int = 1) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=window)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """Generate backup codes for TOTP"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        return codes
    
    @staticmethod
    def setup_totp_for_user(db: Session, user_id: str) -> Tuple[str, str, list[str]]:
        """Setup TOTP for a user and return secret, QR code, and backup codes"""
        try:
            # Generate secret
            secret = TOTPService.generate_secret()
            
            # Generate QR code
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            qr_code = TOTPService.generate_qr_code(user.email, secret)
            
            # Generate backup codes
            backup_codes = TOTPService.generate_backup_codes()
            
            logger.info("TOTP setup initiated", user_id=user_id)
            
            return secret, qr_code, backup_codes
            
        except Exception as e:
            logger.error("TOTP setup failed", error=str(e))
            raise
    
    @staticmethod
    def enable_totp_for_user(db: Session, user_id: str, secret: str, verification_token: str, backup_codes: list[str]) -> bool:
        """Enable TOTP for user after verification"""
        try:
            # Verify the token first
            if not TOTPService.verify_totp(secret, verification_token):
                return False
            
            # Get or create user security record
            user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user_id).first()
            if not user_security:
                user_security = UserSecurity(user_id=user_id)
                db.add(user_security)
            
            # Update security settings
            user_security.totp_secret = secret
            user_security.totp_enabled = True
            user_security.two_factor_method = "totp"
            user_security.backup_codes_hash = "|".join(backup_codes)  # Simple storage for demo
            
            # Update user model
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.totp_enabled = True
            
            db.commit()
            
            logger.info("TOTP enabled successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("TOTP enable failed", error=str(e))
            db.rollback()
            return False
    
    @staticmethod
    def verify_user_totp(db: Session, user_id: str, token: str) -> bool:
        """Verify TOTP token for a user"""
        try:
            user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user_id).first()
            if not user_security or not user_security.totp_secret or not user_security.totp_enabled:
                return False
            
            return TOTPService.verify_totp(user_security.totp_secret, token)
            
        except Exception as e:
            logger.error("TOTP verification failed", error=str(e))
            return False
    
    @staticmethod
    def disable_totp_for_user(db: Session, user_id: str) -> bool:
        """Disable TOTP for user"""
        try:
            user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user_id).first()
            if user_security:
                user_security.totp_enabled = False
                user_security.totp_secret = None
                user_security.two_factor_method = "email"  # Fallback to email
                user_security.backup_codes_hash = None
            
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.totp_enabled = False
            
            db.commit()
            
            logger.info("TOTP disabled successfully", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("TOTP disable failed", error=str(e))
            db.rollback()
            return False
