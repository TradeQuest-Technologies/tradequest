"""
Broker integration endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import structlog
import math
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.trade import ApiKeyCreate, ApiKeyResponse, TradeResponse
from app.models.user import User
from app.models.trade import ApiKey, Trade
from app.services.broker import BrokerService

logger = structlog.get_logger()

def safe_numeric_value(value):
    """Convert numeric value to JSON-safe format, handling NaN/Infinity"""
    if value is None:
        return None
    
    try:
        # Convert to float to check for special values
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            return None
        return float_val
    except (ValueError, TypeError, OverflowError):
        return None

def safe_raw_value(value):
    """Convert raw field to JSON-safe format"""
    if value is None:
        return None
    
    if isinstance(value, str):
        try:
            # Try to parse as JSON and clean any problematic values
            parsed = json.loads(value)
            return json.dumps(parsed)  # Re-serialize to ensure it's clean
        except json.JSONDecodeError:
            return value  # Return as-is if not valid JSON
    return value

router = APIRouter()

@router.post("/connect/{venue}", response_model=ApiKeyResponse)
async def connect_broker(
    venue: str,
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Connect a broker account (read-only)"""
    
    if venue not in ["kraken", "coinbase"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported venue. Supported: kraken, coinbase"
        )
    
    # Check if user already has keys for this venue
    existing_key = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.venue == venue
    ).first()
    
    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already connected to {venue}"
        )
    
    # TODO: Encrypt API keys before storing
    # For now, store as plain text (NEVER do this in production!)
    api_key = ApiKey(
        user_id=current_user.id,
        venue=venue,
        key_enc=api_key_data.api_key,  # TODO: Encrypt
        secret_enc=api_key_data.api_secret,  # TODO: Encrypt
        meta=api_key_data.meta
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    logger.info("Broker connected", user_id=str(current_user.id), venue=venue)
    
    return ApiKeyResponse(
        id=str(api_key.id),
        venue=api_key.venue,
        created_at=api_key.created_at
    )

@router.get("/fills")
async def get_fills(
    venue: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    symbols: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trade fills from connected brokers"""
    
    # Default to last 7 days if no dates provided
    if not end:
        end = datetime.utcnow()
    if not start:
        start = end - timedelta(days=7)
    
    # Build query
    query = db.query(Trade).filter(Trade.user_id == current_user.id)
    
    if venue:
        query = query.filter(Trade.venue == venue.upper())
    
    if symbols:
        symbol_list = [s.strip() for s in symbols.split(",")]
        query = query.filter(Trade.symbol.in_(symbol_list))
    
    query = query.filter(
        Trade.filled_at >= start,
        Trade.filled_at <= end
    ).order_by(Trade.filled_at.desc())
    
    trades = query.all()
    
    # Convert trades to response format, handling NaN/Infinity values
    trade_responses = []
    for trade in trades:
        try:
            trade_dict = {
                'id': trade.id,
                'user_id': trade.user_id,
                'account': trade.account,
                'venue': trade.venue,
                'symbol': trade.symbol,
                'side': trade.side,
                'qty': safe_numeric_value(trade.qty),
                'avg_price': safe_numeric_value(trade.avg_price),
                'fees': safe_numeric_value(trade.fees),
                'pnl': safe_numeric_value(trade.pnl),
                'submitted_at': trade.submitted_at,
                'filled_at': trade.filled_at,
                'order_ref': trade.order_ref,
                'session_id': trade.session_id,
                'raw': safe_raw_value(trade.raw),
                'chart_image': trade.chart_image
            }
            trade_responses.append(TradeResponse(**trade_dict))
        except Exception as e:
            logger.warning("Failed to convert trade to response", trade_id=trade.id, error=str(e))
            continue
    
    # Convert to dicts to ensure JSON serialization works
    result = []
    for trade_response in trade_responses:
        try:
            trade_dict = trade_response.model_dump()
            result.append(trade_dict)
        except Exception as e:
            logger.error("Failed to convert trade_response to dict", error=str(e))
            continue
    
    logger.info(f"Returning {len(result)} broker trades as dicts")
    return result

@router.get("/positions")
async def get_positions(
    venue: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current positions from connected brokers"""
    
    # Get user's API keys
    api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id)
    
    if venue:
        api_keys = api_keys.filter(ApiKey.venue == venue)
    
    positions = {}
    
    for api_key in api_keys.all():
        try:
            broker_service = BrokerService(api_key.venue)
            # TODO: Implement position fetching
            positions[api_key.venue] = {"status": "not_implemented"}
        except Exception as e:
            logger.error("Failed to fetch positions", venue=api_key.venue, error=str(e))
            positions[api_key.venue] = {"error": str(e)}
    
    return positions

@router.post("/sync")
async def sync_trades(
    venue: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually sync trades from connected brokers"""
    
    # Get user's API keys
    api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id)
    
    if venue:
        api_keys = api_keys.filter(ApiKey.venue == venue)
    
    synced_count = 0
    
    for api_key in api_keys.all():
        try:
            broker_service = BrokerService(api_key.venue)
            # TODO: Implement trade syncing
            synced_count += 0  # Placeholder
        except Exception as e:
            logger.error("Failed to sync trades", venue=api_key.venue, error=str(e))
    
    return {"message": f"Synced {synced_count} trades", "venues": [ak.venue for ak in api_keys.all()]}

@router.get("/status")
async def get_broker_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of all connected brokers"""
    
    api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
    
    status_list = []
    for api_key in api_keys:
        try:
            broker_service = BrokerService(api_key.venue)
            # Test connection
            is_connected = True  # TODO: Implement actual connection test
            last_sync = datetime.utcnow() - timedelta(hours=1)  # TODO: Get actual last sync time
            
            status_list.append({
                "venue": api_key.venue,
                "connected": is_connected,
                "last_sync": last_sync.isoformat(),
                "created_at": api_key.created_at.isoformat()
            })
        except Exception as e:
            logger.error("Failed to check broker status", venue=api_key.venue, error=str(e))
            status_list.append({
                "venue": api_key.venue,
                "connected": False,
                "error": str(e),
                "created_at": api_key.created_at.isoformat()
            })
    
    return {"brokers": status_list}

@router.delete("/revoke/{venue}")
async def revoke_broker(
    venue: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke broker connection and delete API keys"""
    
    if venue not in ["kraken", "coinbase"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported venue. Supported: kraken, coinbase"
        )
    
    # Find and delete API key
    api_key = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.venue == venue
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No connection found for {venue}"
        )
    
    db.delete(api_key)
    db.commit()
    
    logger.info("Broker connection revoked", user_id=str(current_user.id), venue=venue)
    
    return {"message": f"Successfully revoked {venue} connection"}
