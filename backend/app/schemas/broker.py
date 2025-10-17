"""
Broker integration schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BrokerConnectionRequest(BaseModel):
    """Request to connect a broker"""
    venue: str = Field(..., description="Broker venue (hyperliquid, kraken, coinbase)")
    
    # For Hyperliquid
    wallet_address: Optional[str] = Field(None, description="Wallet address (for Hyperliquid)")
    private_key: Optional[str] = Field(None, description="Private key for signing (optional, for trading)")
    
    # For traditional exchanges
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")
    passphrase: Optional[str] = Field(None, description="API passphrase (for Coinbase)")
    
    # Options
    auto_sync: bool = Field(True, description="Automatically sync trades")
    sync_interval_minutes: int = Field(15, description="Auto-sync interval in minutes")

class BrokerConnectionResponse(BaseModel):
    """Response after connecting a broker"""
    id: str
    venue: str
    status: str
    wallet_address: Optional[str] = None
    api_key_masked: Optional[str] = None
    account_value: Optional[float] = None
    positions_count: Optional[int] = None
    message: str

class BrokerConnectionInfo(BaseModel):
    """Information about a broker connection"""
    id: str
    venue: str
    wallet_address: Optional[str] = None
    api_key_masked: Optional[str] = None
    status: str
    last_sync: Optional[datetime] = None
    trade_count: int = 0
    created_at: datetime
    meta: Optional[Dict[str, Any]] = None

class SyncTradesRequest(BaseModel):
    """Request to sync trades from broker"""
    venue: Optional[str] = Field(None, description="Specific venue to sync (optional)")
    symbols: Optional[List[str]] = Field(None, description="Filter by specific symbols")
    start_date: Optional[datetime] = Field(None, description="Start date for historical sync")
    end_date: Optional[datetime] = Field(None, description="End date for historical sync")
    limit: int = Field(1000, description="Maximum number of trades to sync")

class SyncTradesResponse(BaseModel):
    """Response after syncing trades"""
    venue: str
    synced_count: int
    skipped_count: int = 0
    error_count: int = 0
    trades_added: int
    trades_updated: int
    message: str

class PositionInfo(BaseModel):
    """Position information from broker"""
    venue: str
    symbol: str
    size: float
    entry_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    leverage: Optional[float] = None
    position_value: Optional[float] = None

class AccountPositionsResponse(BaseModel):
    """Account positions across all connected brokers"""
    venue: str
    positions: List[PositionInfo]
    account_value: Optional[float] = None
    margin_used: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

