"""
Ticker database models
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base

class Ticker(Base):
    """Model for storing ticker symbols and basic info"""
    __tablename__ = "tickers"
    
    symbol = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    market_type = Column(String, nullable=False, index=True)  # 'stocks', 'crypto', 'forex'
    exchange = Column(String, nullable=True)
    currency = Column(String, default='USD')
    is_active = Column(Boolean, default=True)
    
    # For crypto
    coin_id = Column(String, nullable=True)  # CoinGecko ID
    rank = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Add indexes for fast search
    __table_args__ = (
        Index('idx_ticker_search', 'symbol', 'name'),
        Index('idx_market_type', 'market_type'),
    )
