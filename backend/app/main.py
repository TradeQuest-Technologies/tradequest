"""
TradeQuest - Path to Profitability Platform (P3)
Main FastAPI application entry point
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import structlog
import uvicorn
import os
import logging
import logging.handlers
from pathlib import Path
import time
import sys
import io

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.middleware import LoggingMiddleware, RateLimitMiddleware

# Import all models to ensure they are created in the database
from app.models import user, trade, strategy, onboarding, api_key, session, bug_report, referral

# Configure structured logging with file output
# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Custom StreamHandler that handles Unicode encoding errors gracefully
class SafeStreamHandler(logging.StreamHandler):
    """StreamHandler that gracefully handles Unicode encoding errors on Windows"""
    def emit(self, record):
        try:
            super().emit(record)
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            # Replace problematic characters with ASCII equivalents
            try:
                msg = self.format(record)
                # Replace common emoji with ASCII equivalents
                msg = msg.replace('❌', '[X]').replace('✅', '[OK]').replace('⚠️', '[!]')
                msg = msg.replace('🔍', '[?]').replace('💡', '[i]').replace('📊', '[#]')
                msg = msg.replace('🎯', '[>]').replace('🚀', '[^]').replace('⚡', '[~]')
                # Write with error handling - replace any remaining problematic characters
                stream = self.stream
                if hasattr(stream, 'buffer'):
                    # For binary streams, encode with error handling
                    stream.buffer.write((msg + self.terminator).encode('utf-8', errors='replace'))
                    stream.buffer.flush()
                else:
                    # For text streams, use errors='replace' when encoding
                    stream.write(msg.encode('ascii', errors='replace').decode('ascii', errors='replace') + self.terminator)
                    self.flush()
            except Exception:
                # If all else fails, just skip the problematic log message
                pass
        except Exception as e:
            # Catch any other exceptions in logging to prevent them from breaking the app
            pass

# Set up a handler for logging errors to prevent them from breaking the application
def handle_logging_error(record):
    """Handle errors in the logging system itself"""
    try:
        # Try to log to stderr as a last resort
        import sys
        sys.stderr.write(f"Logging error: {record.getMessage()}\n")
    except Exception:
        pass  # If even stderr fails, just ignore it

# Configure root logger to handle its own errors
logging.raiseExceptions = False  # Don't raise exceptions from logging

# Configure logging based on environment
if settings.ENVIRONMENT == "development":
    # Development mode - log to both file and console
    import os
    import tempfile
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create handlers with proper encoding
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/backend.log',  # Use local logs directory
        maxBytes=50*1024*1024,  # 50MB for more detailed logs
        backupCount=10,  # Keep more backups
        encoding='utf-8'  # Use UTF-8 encoding for file
    )
    
    # Create console handler with Unicode error handling
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    logging.basicConfig(
        level=logging.DEBUG,  # Capture everything including debug logs
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[file_handler, console_handler],
        force=True
    )
    
    # Suppress yfinance and peewee debug logs
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('peewee').setLevel(logging.WARNING)
    
    # Configure OpenAI and other third-party loggers to use safe handler
    for logger_name in ['openai', 'httpx', 'httpcore']:
        third_party_logger = logging.getLogger(logger_name)
        # Remove existing handlers and add our safe handler
        third_party_logger.handlers = []
        third_party_logger.addHandler(SafeStreamHandler(sys.stdout))
        third_party_logger.propagate = False
else:
    # Production mode - only log to console (CloudWatch will capture stdout)
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[console_handler],
        force=True  # Force reconfiguration
    )
    
    # Suppress yfinance and peewee debug logs
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('peewee').setLevel(logging.WARNING)
    
    # Configure OpenAI and other third-party loggers to use safe handler
    for logger_name in ['openai', 'httpx', 'httpcore']:
        third_party_logger = logging.getLogger(logger_name)
        # Remove existing handlers and add our safe handler
        third_party_logger.handlers = []
        third_party_logger.addHandler(SafeStreamHandler(sys.stdout))
        third_party_logger.propagate = False

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create database tables
Base.metadata.create_all(bind=engine)

# Run database migrations for missing columns
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    migrations = []
    if 'password_history' not in columns:
        migrations.append(("password_history", "ALTER TABLE users ADD COLUMN password_history TEXT;"))
    if 'totp_secret' not in columns:
        migrations.append(("totp_secret", "ALTER TABLE users ADD COLUMN totp_secret VARCHAR;"))
    if 'backup_codes' not in columns:
        migrations.append(("backup_codes", "ALTER TABLE users ADD COLUMN backup_codes TEXT;"))
    if 'last_password_change' not in columns:
        migrations.append(("last_password_change", "ALTER TABLE users ADD COLUMN last_password_change TIMESTAMP WITH TIME ZONE;"))
    if 'deletion_requested_at' not in columns:
        migrations.append(("deletion_requested_at", "ALTER TABLE users ADD COLUMN deletion_requested_at TIMESTAMP WITH TIME ZONE;"))
    if 'deleted_at' not in columns:
        migrations.append(("deleted_at", "ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;"))
    if 'display_name' not in columns:
        migrations.append(("display_name", "ALTER TABLE users ADD COLUMN display_name VARCHAR;"))
    if 'bio' not in columns:
        migrations.append(("bio", "ALTER TABLE users ADD COLUMN bio TEXT;"))
    if 'avatar_url' not in columns:
        migrations.append(("avatar_url", "ALTER TABLE users ADD COLUMN avatar_url VARCHAR;"))
    if 'twitter_handle' not in columns:
        migrations.append(("twitter_handle", "ALTER TABLE users ADD COLUMN twitter_handle VARCHAR;"))
    if 'trading_style' not in columns:
        migrations.append(("trading_style", "ALTER TABLE users ADD COLUMN trading_style VARCHAR;"))
    if 'privacy_settings' not in columns:
        migrations.append(("privacy_settings", "ALTER TABLE users ADD COLUMN privacy_settings TEXT;"))
    if 'referral_code' not in columns:
        migrations.append(("referral_code", "ALTER TABLE users ADD COLUMN referral_code VARCHAR;"))
        migrations.append(("referral_code_idx", "CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);"))
    
    if migrations:
        logger.info(f"Running {len(migrations)} database migrations for users table...")
        with engine.connect() as conn:
            for col_name, sql in migrations:
                logger.info(f"Adding missing {col_name} column to users table...")
                conn.execute(text(sql))
            conn.commit()
        logger.info("Successfully completed all user table migrations")
except Exception as e:
    logger.error(f"Failed to run database migration for users table: {e}")

# Run database migrations for daily_metrics table
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Check if daily_metrics table exists
    if 'daily_metrics' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('daily_metrics')]
        
        migrations = []
        if 'ai_risk_factor' not in columns:
            migrations.append(("ai_risk_factor", "ALTER TABLE daily_metrics ADD COLUMN ai_risk_factor NUMERIC;"))
        if 'adherence_score' not in columns:
            migrations.append(("adherence_score", "ALTER TABLE daily_metrics ADD COLUMN adherence_score NUMERIC;"))
        
        if migrations:
            logger.info(f"Running {len(migrations)} database migrations for daily_metrics table...")
            with engine.connect() as conn:
                for col_name, sql in migrations:
                    logger.info(f"Adding missing {col_name} column to daily_metrics table...")
                    conn.execute(text(sql))
                conn.commit()
            logger.info("Successfully completed all daily_metrics table migrations")
except Exception as e:
    logger.error(f"Failed to run database migration for daily_metrics table: {e}")

# Run database migrations for subscriptions table
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Check if subscriptions table exists
    if 'subscriptions' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('subscriptions')]
        
        migrations = []
        if 'stripe_subscription' not in columns:
            migrations.append(("stripe_subscription", "ALTER TABLE subscriptions ADD COLUMN stripe_subscription VARCHAR;"))
        if 'trial_start' not in columns:
            migrations.append(("trial_start", "ALTER TABLE subscriptions ADD COLUMN trial_start TIMESTAMP WITH TIME ZONE;"))
        if 'trial_end' not in columns:
            migrations.append(("trial_end", "ALTER TABLE subscriptions ADD COLUMN trial_end TIMESTAMP WITH TIME ZONE;"))
        if 'is_trial' not in columns:
            migrations.append(("is_trial", "ALTER TABLE subscriptions ADD COLUMN is_trial BOOLEAN DEFAULT FALSE;"))
        
        if migrations:
            logger.info(f"Running {len(migrations)} database migrations for subscriptions table...")
            with engine.connect() as conn:
                for col_name, sql in migrations:
                    logger.info(f"Adding missing {col_name} column to subscriptions table...")
                    conn.execute(text(sql))
                conn.commit()
            logger.info("Successfully completed all subscriptions table migrations")
except Exception as e:
    logger.error(f"Failed to run database migration for subscriptions table: {e}")

# Run database migrations for magic_link_tokens table
try:
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    
    # Check if magic_link_tokens table exists
    if 'magic_link_tokens' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('magic_link_tokens')]
        
        migrations = []
        if 'referral_code' not in columns:
            migrations.append(("referral_code", "ALTER TABLE magic_link_tokens ADD COLUMN referral_code VARCHAR;"))
        
        if migrations:
            logger.info(f"Running {len(migrations)} database migrations for magic_link_tokens table...")
            with engine.connect() as conn:
                for col_name, sql in migrations:
                    logger.info(f"Adding missing {col_name} column to magic_link_tokens table...")
                    conn.execute(text(sql))
                conn.commit()
            logger.info("Successfully completed all magic_link_tokens table migrations")
except Exception as e:
    logger.error(f"Failed to run database migration for magic_link_tokens table: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="TradeQuest API",
    description="Path to Profitability Platform - No gurus. No signals. Just your data, real analysis, and disciplined growth.",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Add custom exception handler for validation errors to log them
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Log validation errors for debugging"""
    logger.error(
        "Validation error",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
        body=exc.body if hasattr(exc, 'body') else None
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# CORS middleware - MUST be added FIRST (before other middlewares)  
# This ensures CORS preflight (OPTIONS) requests are handled properly
# Allow localhost for development and tradequest.tech for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "https://tradequest.tech",
        "https://www.tradequest.tech",
        "https://api.tradequest.tech"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Security middleware - only enforce in development
# In production, skip TrustedHostMiddleware as load balancer handles host routing
if settings.ENVIRONMENT == "development" and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Add simple request logging middleware with error catching
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"[REQUEST] {request.method} {request.url.path}")
    print(f"[FULL URL] {request.url}")
    print(f"[QUERY PARAMS] {dict(request.query_params)}")
    print(f"{'='*80}\n")
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"[RESPONSE] {request.method} {request.url.path}")
        print(f"[STATUS] {response.status_code}")
        print(f"[TIME] {process_time:.2f}s")
        print(f"{'='*80}\n")
        
        return response
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"[ERROR] Exception in request processing:")
        print(f"Path: {request.url.path}")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        print(f"{'='*80}\n")
        raise

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files for uploads
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize and start the RunManager for backtest processing
@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup"""
    from app.services.run_manager import get_run_manager
    from app.core.database import get_db
    from sqlalchemy import text
    
    # Run database migrations
    try:
        db = next(get_db())
        # Remove unique constraint from repro_id (users should be able to run same strategy multiple times)
        db.execute(text("DROP INDEX IF EXISTS ix_backtest_runs_repro_id;"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_backtest_runs_repro_id ON backtest_runs(repro_id);"))
        db.commit()
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.warning(f"Database migration failed (may already be applied): {e}")
    finally:
        db.close()
    
    # get_run_manager() automatically starts the worker if not already running
    get_run_manager()
    logger.info("RunManager initialized - ready to process backtests")
    
    # Log social media manager password for admin reference
    if settings.SOCIAL_MEDIA_MANAGER_PASSWORD:
        logger.info(
            "Social Media Manager Password",
            password=settings.SOCIAL_MEDIA_MANAGER_PASSWORD,
            note="Use this password to access referrals and analytics tabs"
        )
        print(f"\n{'='*80}")
        print(f"[SOCIAL MEDIA MANAGER PASSWORD] {settings.SOCIAL_MEDIA_MANAGER_PASSWORD}")
        print(f"[NOTE] This password grants access to referrals and analytics tabs only")
        print(f"{'='*80}\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on app shutdown"""
    from app.services.run_manager import get_run_manager
    run_manager = get_run_manager()
    await run_manager.stop()
    logger.info("RunManager stopped")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "TradeQuest API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",  # Placeholder: returns static DB status; replace with real health check if needed
        "redis": "connected"      # Placeholder: returns static Redis status; replace with real health check if needed
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_config=None  # Use our structured logging
    )
