"""
Onboarding endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.onboarding import (
    UserProfile, UserGoals, UserSecurity, AlertRules, CoachPreferences,
    BacktestPreferences, NotificationSettings, MarketingProfile, OnboardingProgress
)
from app.schemas.onboarding import (
    LegalAcceptance, AccountBasics, SecuritySetup, TradingProfile, GoalsAndRisk,
    DisciplineRules, BrokerConnection, TradeImport, CoachDefaults, BacktestDefaults,
    NotificationSettings as NotificationSettingsSchema, AttributionData, PlanSelection,
    OnboardingComplete, OnboardingStepResponse, OnboardingStatusResponse, 
    OnboardingProgress as OnboardingProgressSchema
)
from datetime import datetime
import json
import structlog

logger = structlog.get_logger()
router = APIRouter()

def get_or_create_onboarding_progress(db: Session, user_id: str) -> OnboardingProgress:
    """Get or create onboarding progress for user"""
    progress = db.query(OnboardingProgress).filter(OnboardingProgress.user_id == user_id).first()
    if not progress:
        progress = OnboardingProgress(
            user_id=user_id,
            current_step=1,
            completed_steps=json.dumps([])
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress

def update_progress(db: Session, user_id: str, step: int):
    """Update onboarding progress"""
    progress = get_or_create_onboarding_progress(db, user_id)
    completed_steps = json.loads(progress.completed_steps) if progress.completed_steps else []
    if step not in completed_steps:
        completed_steps.append(step)
        progress.completed_steps = json.dumps(completed_steps)
        progress.current_step = min(step + 1, 14)
        db.commit()

def create_step_response(db: Session, user_id: str, success: bool, message: str, next_step: int = None) -> OnboardingStepResponse:
    """Create a standardized onboarding step response"""
    progress = get_or_create_onboarding_progress(db, user_id)
    return OnboardingStepResponse(
        success=success,
        message=message,
        next_step=next_step,
        progress=OnboardingProgressSchema(
            current_step=progress.current_step,
            completed_steps=json.loads(progress.completed_steps) if progress.completed_steps else [],
            completed=progress.current_step >= 14
        )
    )

@router.get("/status", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current onboarding status"""
    
    # Check if user has completed onboarding
    if current_user.onboarding_completed:
        return OnboardingStatusResponse(
            current_step=14,
            completed_steps=list(range(1, 15)),
            progress_percentage=100.0,
            completed=True
        )
    
    progress = get_or_create_onboarding_progress(db, current_user.id)
    completed_steps = json.loads(progress.completed_steps) if progress.completed_steps else []
    
    return OnboardingStatusResponse(
        current_step=progress.current_step,
        completed_steps=completed_steps,
        progress_percentage=(len(completed_steps) / 14) * 100,
        completed=False
    )

@router.post("/step/1", response_model=OnboardingStepResponse)
async def complete_step_1_legal(
    data: LegalAcceptance,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 1: Legal acceptance"""
    
    if not data.age_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must be 16 or older to use TradeQuest"
        )
    
    if not data.accept_tos or not data.accept_privacy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept Terms of Service and Privacy Policy"
        )
    
    # Update user with legal acceptance
    current_user.age_confirmed_at = datetime.utcnow()
    current_user.tos_accepted_at = datetime.utcnow()
    current_user.privacy_accepted_at = datetime.utcnow()
    current_user.region = data.region
    
    update_progress(db, current_user.id, 1)
    db.commit()
    
    logger.info("onboarding.step1_legal_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Legal acceptance completed", 2)

@router.post("/step/2", response_model=OnboardingStepResponse)
async def complete_step_2_basics(
    data: AccountBasics,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 2: Account basics"""
    
    # Get or create user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Identity basics
    # keep legacy legal_name nullable for backwards-compat
    if getattr(data, 'first_name', None) or getattr(data, 'last_name', None):
        profile.first_name = data.first_name
        profile.last_name = data.last_name
    # Validate age >= 16 if birth_date provided
    if data.birth_date:
        try:
            birth = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
            today = datetime.utcnow().date()
            age_years = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            if age_years < 16:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must be at least 16 years old to use TradeQuest")
            profile.birth_date = data.birth_date
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid birth date format. Use YYYY-MM-DD")
    profile.alias = data.alias or current_user.email.split('@')[0]
    profile.timezone = data.timezone
    profile.display_currency = data.display_currency
    profile.pnl_visibility_default = data.pnl_visibility_default
    
    update_progress(db, current_user.id, 2)
    db.commit()
    
    logger.info("onboarding.step2_basics_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Account basics completed", 3)

@router.post("/step/3", response_model=OnboardingStepResponse)
async def complete_step_3_security(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 3: Security setup (password + 2FA required)"""
    
    print(f"Step 3 received request: {request}")
    logger.info("Step 3 raw request", user_id=current_user.id, request_data=request)
    
    # Parse the request data
    try:
        print(f"Attempting to parse SecuritySetup with: {request}")
        data = SecuritySetup(**request)
        print(f"Successfully parsed SecuritySetup: {data}")
    except Exception as e:
        print(f"SecuritySetup validation failed: {e}")
        logger.error("Step 3 validation failed", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request data: {str(e)}"
        )
    
    logger.info("Step 3 received data", user_id=current_user.id, 
                has_password=bool(data.set_password), 
                has_confirm=bool(data.confirm_password),
                two_factor_method=data.two_factor_method,
                phone_number=data.phone_number)
    
    try:
        # Validate password requirements
        if data.set_password != data.confirm_password:
            logger.error("Password mismatch", user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        if len(data.set_password) < 10:
            logger.error("Password too short", user_id=current_user.id, length=len(data.set_password))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 10 characters long"
            )
        
        # Validate 2FA method
        if data.two_factor_method not in ["email", "sms", "google_auth", "totp"]:
            logger.error("Invalid 2FA method", user_id=current_user.id, method=data.two_factor_method)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA method"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Step 3 validation error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    
    # Get or create security record
    print(f"Querying UserSecurity for user: {current_user.id}")
    security = db.query(UserSecurity).filter(UserSecurity.user_id == current_user.id).first()
    if not security:
        print("Creating new UserSecurity record")
        security = UserSecurity(user_id=current_user.id)
        db.add(security)
    else:
        print(f"Found existing UserSecurity record: {security}")
    
    # Hash and store password
    print(f"Hashing password: {data.set_password}")
    from app.core.auth import get_password_hash
    try:
        hashed_password = get_password_hash(data.set_password)
        print(f"Password hashed successfully: {hashed_password[:20]}...")
        security.password_hash = hashed_password
    except Exception as e:
        print(f"Password hashing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password hashing failed: {str(e)}"
        )
    
    # Set 2FA method
    security.two_factor_method = data.two_factor_method
    
    # Handle specific 2FA method setup
    if data.two_factor_method == "sms":
        if not data.phone_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required for SMS 2FA"
            )
        security.phone_number = data.phone_number
        # Note: phone verification will be done via /2fa/setup/sms endpoint
    
    elif data.two_factor_method == "totp":
        print(f"Handling TOTP 2FA setup - verification will be done separately")
        # TOTP setup will be completed via /2fa/setup/totp endpoint
        # No verification code required at this step
    
    elif data.two_factor_method == "google_auth":
        # Google auth setup will be completed via /2fa/setup/google endpoint
        pass
    
    # Update user model
    print(f"Updating user password_hash")
    current_user.password_hash = security.password_hash
    
    print(f"Updating progress for step 3")
    update_progress(db, current_user.id, 3)
    
    print(f"Committing to database")
    try:
        db.commit()
        print(f"Database commit successful")
    except Exception as e:
        print(f"Database commit failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    logger.info("onboarding.step3_security_set", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Security setup completed", 4)

@router.post("/step/4", response_model=OnboardingStepResponse)
async def complete_step_4_profile(
    data: TradingProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 4: Trading profile"""
    
    # Get or create user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.experience_level = data.experience_level
    profile.markets = json.dumps(data.markets)
    profile.style = json.dumps(data.style)
    profile.timeframes = json.dumps(data.timeframes)
    profile.platforms = json.dumps(data.platforms)
    profile.days_active_per_week = data.days_active_per_week
    profile.session_pref = json.dumps(data.session_pref)
    
    update_progress(db, current_user.id, 4)
    db.commit()
    
    logger.info("onboarding.step4_profile_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Trading profile completed", 5)

@router.post("/step/5", response_model=OnboardingStepResponse)
async def complete_step_5_goals(
    data: GoalsAndRisk,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 5: Goals and risk setup"""
    
    # Get or create user goals
    goals = db.query(UserGoals).filter(UserGoals.user_id == current_user.id).first()
    if not goals:
        goals = UserGoals(user_id=current_user.id)
        db.add(goals)
    
    goals.primary_goal = data.primary_goal
    goals.account_size_band = data.account_size_band
    goals.risk_per_trade_pct = data.risk_per_trade_pct
    goals.target_mdd_pct = data.max_monthly_drawdown_target_pct
    goals.target_winrate_hint = data.target_winrate_hint
    
    update_progress(db, current_user.id, 5)
    db.commit()
    
    logger.info("onboarding.step5_goals_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Goals and risk setup completed", 6)

@router.post("/step/6", response_model=OnboardingStepResponse)
async def complete_step_6_rules(
    data: DisciplineRules,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 6: Discipline rules"""
    
    # Create alert rule
    rule = AlertRules(
        user_id=current_user.id,
        daily_stop_type=data.daily_stop_type,
        daily_stop_value=data.daily_stop_value,
        max_trades_per_day=data.max_trades_per_day,
        cooldown_minutes=data.cooldown_minutes,
        quiet_hours_start=data.quiet_hours_start,
        quiet_hours_end=data.quiet_hours_end,
        enabled=data.apply_rules_now
    )
    db.add(rule)
    
    update_progress(db, current_user.id, 6)
    db.commit()
    
    logger.info("onboarding.step6_rules_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Discipline rules completed", 7)

@router.post("/step/7", response_model=OnboardingStepResponse)
async def complete_step_7_broker(
    data: BrokerConnection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 7: Broker connection (optional)"""
    
    # TODO: Implement actual broker connection and API key validation
    # For now, just skip this step
    
    logger.info("onboarding.step7_broker_skipped", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Broker connection skipped", 8)

@router.post("/step/8", response_model=OnboardingStepResponse)
async def complete_step_8_import(
    data: TradeImport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 8: Trade import (optional)"""
    
    # TODO: Implement trade import logic
    # For now, just skip this step
    
    logger.info("onboarding.step8_import_skipped", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Trade import skipped", 9)

@router.post("/step/9", response_model=OnboardingStepResponse)
async def complete_step_9_coach(
    data: CoachDefaults,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 9: AI Coach defaults"""
    
    # Get or create coach preferences
    prefs = db.query(CoachPreferences).filter(CoachPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = CoachPreferences(user_id=current_user.id)
        db.add(prefs)
    
    prefs.tone = data.coach_tone
    prefs.tools_allowed = json.dumps(data.tool_permissions)
    prefs.data_window_days = data.data_window_days
    prefs.action_items_per_session = data.action_items_per_session
    prefs.anonymized_optin = data.anonymized_usage_optin
    
    update_progress(db, current_user.id, 9)
    db.commit()
    
    logger.info("onboarding.step9_coach_prefs_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "AI Coach preferences completed", 10)

@router.post("/step/10", response_model=OnboardingStepResponse)
async def complete_step_10_backtest(
    data: BacktestDefaults,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 10: Backtesting defaults"""
    
    # Get or create backtest preferences
    prefs = db.query(BacktestPreferences).filter(BacktestPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = BacktestPreferences(user_id=current_user.id)
        db.add(prefs)
    
    symbol_tf = data.default_symbol_tf.split(' ')
    prefs.default_symbol = symbol_tf[0] if len(symbol_tf) > 0 else "BTC/USDT"
    prefs.default_timeframe = symbol_tf[1] if len(symbol_tf) > 1 else "1m"
    prefs.fees_bps_default = data.fees_bps_default
    prefs.slip_bps_default = data.slip_bps_default
    prefs.mc_runs_default = data.mc_runs_default
    prefs.default_strategies = json.dumps(data.default_strategies)
    
    update_progress(db, current_user.id, 10)
    db.commit()
    
    logger.info("onboarding.step10_backtest_prefs_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Backtesting preferences completed", 11)

@router.post("/step/11", response_model=OnboardingStepResponse)
async def complete_step_11_notifications(
    data: NotificationSettingsSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 11: Notification settings"""
    
    # Get or create notification settings
    settings = db.query(NotificationSettings).filter(NotificationSettings.user_id == current_user.id).first()
    if not settings:
        settings = NotificationSettings(user_id=current_user.id)
        db.add(settings)
    
    settings.email_alerts = data.email_alerts
    settings.telegram_user_id = data.telegram_link  # TODO: Extract user ID from link
    settings.daily_summary_time = data.daily_summary_time
    settings.weekly_report_email = data.weekly_report_email
    
    update_progress(db, current_user.id, 11)
    db.commit()
    
    logger.info("onboarding.step11_notifications_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Notification settings completed", 12)

@router.post("/step/12", response_model=OnboardingStepResponse)
async def complete_step_12_attribution(
    data: AttributionData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 12: Attribution data"""
    
    # Get or create marketing profile
    profile = db.query(MarketingProfile).filter(MarketingProfile.user_id == current_user.id).first()
    if not profile:
        profile = MarketingProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.acquisition_sources = json.dumps(data.acquisition_sources)
    profile.referral_code = data.referral_code
    profile.community_invite_optin = data.community_invite_optin
    
    update_progress(db, current_user.id, 12)
    db.commit()
    
    logger.info("onboarding.step12_attribution_ok", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Attribution data completed", 13)

@router.post("/step/13", response_model=OnboardingStepResponse)
async def complete_step_13_plan(
    data: PlanSelection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 13: Plan selection"""
    
    # Update user subscription
    if hasattr(current_user, 'subscription') and current_user.subscription:
        current_user.subscription.plan = data.plan
    # TODO: Handle Stripe checkout for paid plans
    
    update_progress(db, current_user.id, 13)
    db.commit()
    
    logger.info("onboarding.step13_plan_selected", user_id=current_user.id, plan=data.plan)
    
    return create_step_response(db, current_user.id, True, "Plan selection completed", 14)

@router.post("/step/14", response_model=OnboardingStepResponse)
async def complete_step_14_finish(
    data: OnboardingComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 14: Complete onboarding"""
    
    # Mark onboarding as completed
    current_user.onboarding_completed = True
    current_user.onboarding_completed_at = datetime.utcnow()
    
    # Update progress
    progress = get_or_create_onboarding_progress(db, current_user.id)
    progress.completed_at = datetime.utcnow()
    
    update_progress(db, current_user.id, 14)
    db.commit()
    
    logger.info("onboarding.completed", user_id=current_user.id)
    
    return create_step_response(db, current_user.id, True, "Onboarding completed successfully!", None)
