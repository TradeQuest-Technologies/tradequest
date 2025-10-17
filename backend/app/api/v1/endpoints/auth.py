"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.auth import create_access_token, generate_magic_token, generate_temp_token, verify_token, verify_password, get_password_hash, get_current_user
from app.schemas.auth import (
    MagicLinkRequest, MagicLinkResponse, PasswordLoginRequest, 
    PasswordLoginResponse, TwoFactorRequest, TokenConsumeRequest, 
    TokenResponse, UserResponse, ForgotPasswordRequest, 
    ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
)
from app.models.user import User, Subscription
from app.models.onboarding import UserSecurity
from app.services.email_service import EmailService
from app.services.email_service import EmailService
from datetime import timedelta, datetime
import structlog

logger = structlog.get_logger()
router = APIRouter()

# In-memory store for magic tokens, temp tokens, and reset tokens (use Redis in production)
magic_tokens = {}
temp_tokens = {}
reset_tokens = {}

@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db)
):
    """Send magic link to user's email"""
    
    # Debug prints (will show in console)
    print(f"\n{'='*60}")
    print(f"MAGIC LINK REQUEST")
    print(f"Email: {request.email}")
    print(f"Is Signup: {request.is_signup}")
    print(f"{'='*60}\n")
    
    # Check if user already exists
    user = db.query(User).filter(User.email == request.email).first()
    user_exists = user is not None
    
    print(f"User exists in database: {user_exists}")
    print(f"Should block signup: {request.is_signup and user_exists}")
    
    # Debug logging
    logger.info("Magic link request", 
                email=request.email, 
                is_signup=request.is_signup, 
                user_exists=user_exists)
    
    # If this is a signup flow and user exists, return error
    if request.is_signup and user_exists:
        print(f"BLOCKING SIGNUP - User already exists!")
        logger.warning("Signup blocked - user already exists", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please sign in instead."
        )
    
    # Generate magic token
    token = generate_magic_token()
    expires_at = datetime.utcnow() + timedelta(minutes=15)  # 15 minute expiration
    magic_tokens[token] = {
        "email": request.email,
        "expires_at": expires_at.isoformat()
    }
    
    # Create user if doesn't exist (signin flow)
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
    magic_link_url = f"{settings.FRONTEND_URL}/auth/callback?token={token}"
    
    try:
        await email_service.send_magic_link_email(request.email, magic_link_url)
        logger.info("Magic link email sent", email=request.email, token=token[:8] + "...", user_exists=user_exists)
    except Exception as e:
        logger.error("Failed to send magic link email", email=request.email, error=str(e))
        # Still return success to prevent email enumeration attacks
    
    return MagicLinkResponse(
        message=f"Magic link sent to {request.email}",
        user_exists=user_exists
    )

@router.post("/password-login", response_model=PasswordLoginResponse)
async def password_login(
    login_request: PasswordLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user with password"""
    
    # Get user
    user = db.query(User).filter(User.email == login_request.email).first()
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
    if not verify_password(login_request.password, user.password_hash):
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
    expires_delta = timedelta(days=30) if login_request.remember_me else timedelta(hours=24)
    logger.info("Creating access token for user without 2FA", email=user.email, expires_delta=str(expires_delta))
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=expires_delta
    )
    logger.info("Access token created successfully", email=user.email, token_length=len(access_token))
    
    # Create session record
    try:
        from app.models.session import UserSession
        import hashlib
        
        session_token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        
        # Extract user agent and IP from request
        user_agent = request.headers.get("user-agent", "Unknown")
        # Try to get real IP from X-Forwarded-For or X-Real-IP headers (for proxies)
        ip_address = request.headers.get("x-forwarded-for", request.headers.get("x-real-ip", request.client.host if request.client else "Unknown"))
        
        session = UserSession(
            user_id=user.id,
            session_token_hash=session_token_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + expires_delta
        )
        db.add(session)
        db.commit()
        logger.info("Session record created", session_id=session.id, user_agent=user_agent[:50], ip=ip_address)
    except Exception as e:
        logger.error("Failed to create session record", error=str(e))
    
    logger.info("Password login successful", email=user.email, remember_me=login_request.remember_me)
    
    return PasswordLoginResponse(
        requires_2fa=False,
        message="Login successful",
        access_token=access_token
    )

@router.post("/verify-2fa", response_model=TokenResponse)
async def verify_2fa(
    two_fa_request: TwoFactorRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify 2FA code and complete login"""
    
    # Get temp token data
    temp_data = temp_tokens.get(two_fa_request.temp_token)
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
    
    # Create session record
    try:
        from app.models.session import UserSession
        import hashlib
        
        session_token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session = UserSession(
            user_id=user.id,
            session_token_hash=session_token_hash,
            user_agent="Unknown",  # TODO: Get from request headers
            ip_address="Unknown",
            expires_at=datetime.utcnow() + expires_delta
        )
        db.add(session)
        db.commit()
    except Exception as e:
        logger.error("Failed to create session record", error=str(e))
    
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
    
    # Create session record
    try:
        from app.models.session import UserSession
        import hashlib
        
        session_token_hash = hashlib.sha256(access_token.encode()).hexdigest()
        session = UserSession(
            user_id=user.id,
            session_token_hash=session_token_hash,
            user_agent="Unknown",  # TODO: Get from request headers
            ip_address="Unknown",
            expires_at=datetime.utcnow() + expires_delta
        )
        db.add(session)
        db.commit()
    except Exception as e:
        logger.error("Failed to create session record", error=str(e))
    
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

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Send password reset email (with 2FA verification if enabled)"""
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == request.email).first()
    except Exception as e:
        logger.error("Database error checking user", email=request.email, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    # If user doesn't exist, return generic success to prevent enumeration
    if not user:
        logger.info("Password reset requested for non-existent user", email=request.email)
        return ForgotPasswordResponse(
            message="If an account exists with this email, you will receive password reset instructions."
        )
    
    # Check if user has 2FA enabled
    user_security = db.query(UserSecurity).filter(UserSecurity.user_id == user.id).first()
    if user_security and user_security.two_factor_method in ["totp", "sms", "email"]:
        # 2FA is enabled - verification required before sending reset link
        if not request.two_factor_code:
            # First request - need to send 2FA code if email-based
            if user_security.two_factor_method == "email":
                # Generate and send code
                code = f"{int(datetime.utcnow().timestamp()) % 1000000:06d}"
                # Store temporarily (use user email as key since we don't have a token yet)
                temp_key = f"forgot_pwd_{request.email}"
                temp_tokens[temp_key] = {
                    "email": request.email,
                    "email_2fa_code": code,
                    "code_sent_at": datetime.utcnow().isoformat(),
                    "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
                }
                
                try:
                    email_service = EmailService()
                    await email_service.send_2fa_code_email(request.email, code)
                    logger.info("2FA code sent for forgot password", email=request.email)
                except Exception as e:
                    logger.error("Failed to send 2FA code", email=request.email, error=str(e))
            
            # Return response indicating 2FA is required
            return ForgotPasswordResponse(
                message="2FA verification required. Please enter your verification code.",
                requires_2fa=True,
                two_factor_method=user_security.two_factor_method
            )
        
        # 2FA code provided - verify it
        if user_security.two_factor_method == "totp" and user_security.totp_enabled:
            from app.services.totp_service import TOTPService
            if not TOTPService.verify_user_totp(db, user.id, request.two_factor_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid TOTP code"
                )
        elif user_security.two_factor_method == "email":
            temp_key = f"forgot_pwd_{request.email}"
            temp_data = temp_tokens.get(temp_key)
            if not temp_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA session expired. Please try again."
                )
            
            stored_code = temp_data.get("email_2fa_code")
            if not stored_code or request.two_factor_code != stored_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code"
                )
            
            # Check if code is not too old (10 minutes)
            code_sent_at = temp_data.get("code_sent_at")
            if code_sent_at:
                code_sent_time = datetime.fromisoformat(code_sent_at)
                if datetime.utcnow() > code_sent_time + timedelta(minutes=10):
                    del temp_tokens[temp_key]
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Verification code has expired"
                    )
            
            # Clean up temp token
            del temp_tokens[temp_key]
        elif user_security.two_factor_method == "sms" and user_security.phone_verified:
            temp_key = f"forgot_pwd_{request.email}"
            temp_data = temp_tokens.get(temp_key)
            stored_code = temp_data.get("sms_2fa_code") if temp_data else None
            if not stored_code or request.two_factor_code != stored_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid SMS code"
                )
            # Clean up
            if temp_data:
                del temp_tokens[temp_key]
        
        logger.info("2FA verification successful for forgot password", email=request.email)
    
    # Generate reset token and send email
    reset_token = generate_magic_token()
    expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
    reset_tokens[reset_token] = {
        "email": request.email,
        "expires_at": expires_at.isoformat()
    }
    
    # Send password reset email
    email_service = EmailService()
    try:
        await email_service.send_password_reset_email(request.email, reset_token)
        logger.info("Password reset email sent", email=request.email, token=reset_token[:8] + "...")
    except Exception as e:
        logger.error("Failed to send password reset email", email=request.email, error=str(e))
    
    return ForgotPasswordResponse(
        message="Password reset instructions sent to your email.",
        requires_2fa=False
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using reset token (2FA was already verified when getting the token)"""
    
    # Verify reset token
    token_data = reset_tokens.get(request.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.utcnow() > expires_at:
        del reset_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Get user
    user = db.query(User).filter(User.email == token_data["email"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Note: 2FA was already verified when the reset link was sent (in forgot_password endpoint)
    # The token itself is proof that the user passed 2FA verification
    
    # Validate password strength - minimum 10 characters
    if len(request.new_password) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 10 characters long"
        )
    
    # Check if new password matches current password
    if user.password_hash and verify_password(request.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as your current password"
        )
    
    # Check against password history (last 5 passwords)
    import json
    if user.password_history:
        try:
            password_history = json.loads(user.password_history)
            for old_hash in password_history:
                if verify_password(request.new_password, old_hash):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="New password cannot be the same as any of your previous passwords"
                    )
        except json.JSONDecodeError:
            logger.warning("Failed to parse password history", user_id=user.id)
    
    # Update password history (keep last 5 passwords)
    new_hash = get_password_hash(request.new_password)
    password_history = []
    if user.password_history:
        try:
            password_history = json.loads(user.password_history)
        except json.JSONDecodeError:
            password_history = []
    
    # Add current password to history if it exists
    if user.password_hash:
        password_history.insert(0, user.password_hash)
    
    # Keep only last 5 passwords
    password_history = password_history[:5]
    user.password_history = json.dumps(password_history)
    
    # Update password
    user.password_hash = new_hash
    db.commit()
    
    # Clean up reset token
    del reset_tokens[request.token]
    
    logger.info("Password reset successful", email=user.email)
    
    return ResetPasswordResponse(
        message="Password reset successful. You can now sign in with your new password."
    )
