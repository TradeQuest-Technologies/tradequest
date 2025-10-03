"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import create_access_token, generate_magic_token, generate_temp_token, verify_token, verify_password, get_current_user
from app.schemas.auth import MagicLinkRequest, MagicLinkResponse, PasswordLoginRequest, PasswordLoginResponse, TwoFactorRequest, TokenConsumeRequest, TokenResponse, UserResponse
from app.models.user import User, Subscription
from app.models.onboarding import UserSecurity
from app.services.email_service import EmailService
from app.services.email_service import EmailService
from datetime import timedelta, datetime
import structlog

logger = structlog.get_logger()
router = APIRouter()

# In-memory store for magic tokens and temp tokens (use Redis in production)
magic_tokens = {}
temp_tokens = {}

@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db)
):
    """Send magic link to user's email"""
    
    # Generate magic token
    token = generate_magic_token()
    expires_at = datetime.utcnow() + timedelta(minutes=15)  # 15 minute expiration
    magic_tokens[token] = {
        "email": request.email,
        "expires_at": expires_at.isoformat()
    }
    
    # Create or get user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        user = User(email=request.email)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create default subscription
        subscription = Subscription(user_id=user.id, plan="free", status="active")
        db.add(subscription)
        db.commit()
    
    # Send magic link email
    email_service = EmailService()
    magic_link_url = f"http://localhost:3000/auth/callback?token={token}"
    
    try:
        await email_service.send_magic_link_email(request.email, magic_link_url)
        logger.info("Magic link email sent", email=request.email, token=token[:8] + "...")
    except Exception as e:
        logger.error("Failed to send magic link email", email=request.email, error=str(e))
        # Still return success to prevent email enumeration attacks
    
    return MagicLinkResponse(message=f"Magic link sent to {request.email}")

@router.post("/password-login", response_model=PasswordLoginResponse)
async def password_login(
    request: PasswordLoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user with password"""
    
    # Get user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user has a password set
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password set for this account. Please use magic link to sign in."
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user has 2FA enabled
    user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if user_security and user_security.two_factor_method in ["totp", "sms", "email"]:
        # Generate temporary token for 2FA
        temp_token = generate_temp_token()
        temp_tokens[temp_token] = {
            "user_id": user.id,
            "email": user.email,
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        # If email-based 2FA, generate and send code
        if user_security.two_factor_method == "email":
            code = f"{int(datetime.utcnow().timestamp()) % 1000000:06d}"
            temp_tokens[temp_token]["email_code"] = code
            try:
                email_service = EmailService()
                await email_service.send_2fa_code_email(user.email, code)
            except Exception as e:
                logger.error("Failed to send 2FA email", email=user.email, error=str(e))
        
        logger.info("Password verified, 2FA required", email=user.email)
        
        return PasswordLoginResponse(
            requires_2fa=True,
            temp_token=temp_token,
            message="Password verified. Please complete 2FA.",
            two_factor_method=user_security.two_factor_method
        )
    
    # No 2FA, create access token directly
    expires_delta = timedelta(days=30) if request.remember_me else timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=expires_delta
    )
    
    logger.info("Password login successful", email=user.email, remember_me=request.remember_me)
    
    return PasswordLoginResponse(
        requires_2fa=False,
        message="Login successful"
    )

@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    request: TwoFactorRequest,
    db: Session = Depends(get_db)
):
    """Verify 2FA code and complete login"""
    
    # Get temp token data
    temp_data = temp_tokens.get(request.temp_token)
    if not temp_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired temporary token"
        )
    
    # Check if temp token is expired
    expires_at = datetime.fromisoformat(temp_data["expires_at"])
    if datetime.utcnow() > expires_at:
        del temp_tokens[request.temp_token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temporary token has expired"
        )
    
    # Get user
    user = db.query(User).filter(User.id == temp_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify 2FA based on user's method
    user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if not user_security:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not configured for this user"
        )
    
    # Verify based on method
    if user_security.two_factor_method == "totp" and user_security.totp_enabled:
        # TOTP verification
        from app.services.totp_service import TOTPService
        if not TOTPService.verify_user_totp(db, user.id, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
    elif user_security.two_factor_method == "sms" and user_security.phone_verified:
        # SMS verification - check against stored codes
        stored_data = temp_tokens.get(request.temp_token)
        if not stored_data or stored_data.get("sms_code") != request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid SMS code"
            )
    elif user_security.two_factor_method == "email":
        # Email verification - compare against code we sent during login
        stored_code = temp_data.get("email_code")
        if not stored_code or request.code != stored_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA method or not configured"
        )
    
    # Create access token
    expires_delta = timedelta(days=30) if request.remember_me else timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=expires_delta
    )
    
    # Clean up temp token
    del temp_tokens[request.temp_token]
    
    logger.info("2FA verification successful", email=user.email, remember_me=request.remember_me)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds())
    )

@router.post("/resend-2fa")
async def resend_two_factor_code(
    request: dict,
    db: Session = Depends(get_db)
):
    temp_token = request.get("temp_token")
    if not temp_token or temp_token not in temp_tokens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid temp token")
    temp_data = temp_tokens[temp_token]
    user = db.query(User).filter(User.id == temp_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if not user_security or user_security.two_factor_method != "email":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resend supported only for email 2FA")
    # generate fresh code and extend expiry a bit
    code = f"{int(datetime.utcnow().timestamp()) % 1000000:06d}"
    temp_tokens[temp_token]["email_code"] = code
    temp_tokens[temp_token]["expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    try:
        email_service = EmailService()
        await email_service.send_2fa_code_email(user.email, code)
    except Exception as e:
        logger.error("Failed to resend 2FA email", email=user.email, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resend code")
    return {"message": "Code resent"}

@router.post("/consume", response_model=TokenResponse)
async def consume_magic_link(
    request: TokenConsumeRequest,
    db: Session = Depends(get_db)
):
    """Consume magic link token and return JWT"""
    
    # Verify magic token
    token_data = magic_tokens.get(request.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link"
        )
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.utcnow() > expires_at:
        del magic_tokens[request.token]  # Clean up expired token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link has expired"
        )
    
    # Get user
    user = db.query(User).filter(User.email == token_data["email"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create JWT token (24 hours for magic link)
    expires_delta = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=expires_delta
    )
    
    # Clean up magic token
    del magic_tokens[request.token]
    
    logger.info("Magic link consumed", email=user.email)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(expires_delta.total_seconds())
    )

from app.models.onboarding import UserProfile

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    
    # Get subscription info
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    plan = subscription.plan if subscription else "free"
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    alias = profile.alias if profile else None
    legal_name = getattr(profile, 'legal_name', None) if profile else None
    first_name = getattr(profile, 'first_name', None) if profile else None
    last_name = getattr(profile, 'last_name', None) if profile else None
    if not first_name and legal_name:
        stripped = legal_name.strip()
        first_name = stripped.split(" ")[0] if stripped else None
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at,
        plan=plan,
        alias=alias,
        legal_name=legal_name,
        first_name=first_name
    )
