"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import structlog

logger = structlog.get_logger()

# Get database URL (supports both direct URLs and component-based)
database_url = settings.get_database_url()
logger.info(f"Database URL: {database_url.split('@')[-1] if '@' in database_url else database_url}")

# Create database engine with production-ready settings
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
    # PostgreSQL specific settings
    connect_args={
        "options": "-c timezone=utc"
    } if database_url.startswith("postgresql") else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
