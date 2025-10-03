"""
Strategy and backtest models
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Date, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    spec = Column(Text, nullable=False)  # Strategy specification (JSON as text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy")

class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(String, ForeignKey("strategies.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metrics = Column(Text)  # Backtest metrics (JSON as text)
    equity_curve = Column(Text)  # Equity curve data (JSON as text)
    trades = Column(Text)  # Generated trades (JSON as text)
    mc_summary = Column(Text)  # Monte Carlo summary (JSON as text)
    
    # Relationships
    user = relationship("User", back_populates="backtests")
    strategy = relationship("Strategy", back_populates="backtests")

class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    day = Column(Date, nullable=False)
    kpis = Column(Text)  # Daily KPIs (JSON as text)
    
    # Relationships
    user = relationship("User", back_populates="daily_metrics")
