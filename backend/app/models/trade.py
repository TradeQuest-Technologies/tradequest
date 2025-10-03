"""
Trade and journal models
"""

from sqlalchemy import Column, String, DateTime, Numeric, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    venue = Column(String, nullable=False)  # kraken, coinbase
    key_enc = Column(Text, nullable=False)  # Encrypted API key
    secret_enc = Column(Text, nullable=False)  # Encrypted API secret
    meta = Column(Text)  # Additional metadata (JSON as text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    account = Column(String)  # spot, margin, futures
    venue = Column(String, nullable=False)  # KRAKEN, COINBASE
    symbol = Column(String, nullable=False)  # BTC/USDT, ETH/USDT
    side = Column(String, nullable=False)  # buy, sell
    qty = Column(Numeric, nullable=False)
    avg_price = Column(Numeric, nullable=False)
    fees = Column(Numeric, default=0)
    pnl = Column(Numeric, default=0)
    submitted_at = Column(DateTime(timezone=True))
    filled_at = Column(DateTime(timezone=True), nullable=False)
    order_ref = Column(String)  # External order reference
    session_id = Column(String)  # Trading session identifier
    raw = Column(Text)  # Original broker data (JSON as text)
    chart_image = Column(String)  # URL or path to chart image
    
    # Relationships
    user = relationship("User", back_populates="trades")
    journal_entries = relationship("JournalEntry", back_populates="trade")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    trade_id = Column(String, ForeignKey("trades.id"))
    ts = Column(DateTime(timezone=True), server_default=func.now())
    note = Column(Text)
    tags = Column(Text)  # Array of tags (JSON as text)
    attachments = Column(Text)  # [{"name":"cap.png","url":"..."}] (JSON as text)
    
    # Relationships
    user = relationship("User", back_populates="journal_entries")
    trade = relationship("Trade", back_populates="journal_entries")
