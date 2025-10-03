"""
Trade and journal schemas
"""

from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import json
import math

class TradeBase(BaseModel):
    account: Optional[str] = None
    venue: str
    symbol: str
    side: str
    qty: Decimal
    avg_price: Decimal
    fees: Decimal = Decimal('0')
    pnl: Decimal = Decimal('0')
    submitted_at: Optional[datetime] = None
    filled_at: datetime
    order_ref: Optional[str] = None
    session_id: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None
    chart_image: Optional[str] = None

class TradeCreate(TradeBase):
    pass

class TradeResponse(TradeBase):
    id: str
    user_id: str
    
    @field_validator('qty', 'avg_price', 'fees', 'pnl', mode='before')
    @classmethod
    def validate_numeric_values(cls, v):
        """Convert NaN, Infinity to None for JSON compatibility"""
        if v is None:
            return None
        
        # Convert to float first to check for special values
        try:
            float_val = float(v)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            return Decimal(str(float_val))
        except (ValueError, TypeError):
            return None
    
    @field_validator('raw', mode='before')
    @classmethod
    def parse_raw_json(cls, v):
        """Parse raw field from JSON string to dict"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
    
    class Config:
        from_attributes = True

class JournalEntryBase(BaseModel):
    trade_id: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, str]]] = None

class JournalEntryCreate(JournalEntryBase):
    pass

class JournalEntryResponse(JournalEntryBase):
    id: str
    user_id: str
    ts: datetime
    
    class Config:
        from_attributes = True

class ApiKeyCreate(BaseModel):
    venue: str
    api_key: str
    api_secret: str
    meta: Optional[Dict[str, Any]] = None

class ApiKeyResponse(BaseModel):
    id: str
    venue: str
    created_at: datetime
    
    class Config:
        from_attributes = True
