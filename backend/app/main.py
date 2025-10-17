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

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.middleware import LoggingMiddleware, RateLimitMiddleware

# Import all models to ensure they are created in the database
from app.models import user, trade, strategy, onboarding, api_key, session

# Configure structured logging with file output
# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging based on environment
if settings.ENVIRONMENT == "development":
    # Development mode - log to both file and console
    import os
    import tempfile
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,  # Capture everything including debug logs
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                'logs/backend.log',  # Use local logs directory
                maxBytes=50*1024*1024,  # 50MB for more detailed logs
                backupCount=10  # Keep more backups
            ),
            logging.StreamHandler()  # Also log to console
        ]
    )
else:
    # Production mode - only log to console (CloudWatch will capture stdout)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()],
        force=True  # Force reconfiguration
    )

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
    
    if migrations:
        logger.info(f"Running {len(migrations)} database migrations...")
        with engine.connect() as conn:
            for col_name, sql in migrations:
                logger.info(f"Adding missing {col_name} column to users table...")
                conn.execute(text(sql))
            conn.commit()
        logger.info("Successfully completed all migrations")
except Exception as e:
    logger.error(f"Failed to run database migration: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="TradeQuest API",
    description="Path to Profitability Platform - No gurus. No signals. Just your data, real analysis, and disciplined growth.",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Security middleware - only enforce in development
# In production, skip TrustedHostMiddleware as load balancer handles host routing
if settings.ENVIRONMENT == "development" and settings.ALLOWED_HOSTS != ["*"]:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    # get_run_manager() automatically starts the worker if not already running
    get_run_manager()
    logger.info("RunManager initialized - ready to process backtests")

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
        "database": "connected",  # TODO: Add actual DB health check
        "redis": "connected"      # TODO: Add actual Redis health check
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_config=None  # Use our structured logging
    )
