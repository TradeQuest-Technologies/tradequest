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
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.trade import TradeResponse
from app.schemas.broker import (
    BrokerConnectionRequest,
    BrokerConnectionResponse,
    BrokerConnectionInfo,
    SyncTradesRequest,
    SyncTradesResponse
)
from app.models.user import User
from app.models.trade import Trade
from app.models.api_key import ApiKey
from app.services.broker import BrokerService
from app.services.encryption_service import encryption_service
from app.services.position_matcher import match_and_calculate_pnl

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

@router.get("/list")
async def get_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all broker connections for the current user"""
    
    api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
    
    connections = []
    for api_key in api_keys:
        # Get trade count for this venue
        trade_count = db.query(Trade).filter(
            Trade.user_id == current_user.id,
            Trade.venue == api_key.venue.upper()
        ).count()
        
        # Decrypt and mask API key for display
        try:
            decrypted_key = encryption_service.decrypt(api_key.key_enc)
            api_key_masked = encryption_service.mask_api_key(decrypted_key)
        except:
            api_key_masked = "****"
        
        # Extract last sync from meta
        last_sync_str = api_key.meta.get('last_sync') if api_key.meta else None
        last_sync = datetime.fromisoformat(last_sync_str) if last_sync_str else None
        
        connection_dict = {
            "id": api_key.id,
            "venue": api_key.venue,
            "wallet_address": api_key.meta.get('wallet_address') if api_key.meta else None,
            "api_key_masked": api_key_masked,
            "status": "connected",
            "last_sync": last_sync.isoformat() if last_sync else None,
            "trade_count": trade_count,
            "created_at": api_key.created_at.isoformat(),
            "meta": api_key.meta
        }
        connections.append(connection_dict)
    
    return connections

@router.post("/connect", response_model=BrokerConnectionResponse)
async def connect_broker(
    request: BrokerConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect a broker account and store encrypted credentials
    
    Supported venues:
    - hyperliquid: Requires wallet_address (read-only) or wallet_address + private_key (trading)
    - kraken: Requires api_key + api_secret
    - coinbase: Use OAuth2 flow instead (call /broker/oauth/coinbase/authorize first)
    
    Note: For Coinbase, use the OAuth2 flow endpoints instead of this direct connection.
    """
    venue = request.venue.lower()
    
    # Validate venue
    supported_venues = ['hyperliquid', 'kraken']  # Coinbase uses OAuth
    if venue not in supported_venues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported venue. Supported: {', '.join(supported_venues)}. For Coinbase, use OAuth2 flow."
        )
    
    # Check if already connected
    existing = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.venue == venue
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already connected to {venue}. Disconnect first to reconnect."
        )
    
    # Validate credentials based on venue
    if venue == 'hyperliquid':
        if not request.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="wallet_address is required for Hyperliquid"
            )
        # Test connection
        broker_service = BrokerService(
            venue=venue,
            api_key=request.private_key,
            wallet_address=request.wallet_address
        )
        
    elif venue == 'kraken':
        # Kraken API keys
        if not request.api_key or not request.api_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="api_key and api_secret are required for Kraken"
            )
        broker_service = BrokerService(
            venue=venue,
            api_key=request.api_key,
            api_secret=request.api_secret
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid venue configuration"
        )
    
    # Test connection
    connection_test = broker_service.test_connection()
    if not connection_test.get('connected'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection test failed: {connection_test.get('error', 'Unknown error')}"
        )
    
    # Store encrypted credentials
    api_key_id = str(uuid.uuid4())
    
    # Encrypt credentials
    if venue == 'hyperliquid':
        key_enc = encryption_service.encrypt(request.wallet_address)
        secret_enc = encryption_service.encrypt(request.private_key or "")  # Empty if read-only
        api_key_masked = encryption_service.mask_api_key(request.wallet_address, show_chars=6)
    else:
        key_enc = encryption_service.encrypt(request.api_key)
        secret_enc = encryption_service.encrypt(request.api_secret)
        api_key_masked = encryption_service.mask_api_key(request.api_key)
    
    # Create API key record
    new_api_key = ApiKey(
        id=api_key_id,
        user_id=current_user.id,
        venue=venue,
        key_enc=key_enc,
        secret_enc=secret_enc,
        meta={
            'wallet_address': request.wallet_address if venue == 'hyperliquid' else None,
            'auto_sync': request.auto_sync,
            'sync_interval_minutes': request.sync_interval_minutes,
            'connection_test': connection_test
        }
    )
    
    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)
    
    logger.info("Broker connected", user_id=current_user.id, venue=venue)
    
    return BrokerConnectionResponse(
        id=api_key_id,
        venue=venue,
        status='connected',
        wallet_address=request.wallet_address if venue == 'hyperliquid' else None,
        api_key_masked=api_key_masked,
        account_value=connection_test.get('account_value'),
        positions_count=connection_test.get('positions_count'),
        message=f"Successfully connected to {venue.title()}"
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

@router.post("/sync", response_model=List[SyncTradesResponse])
async def sync_trades(
    request: SyncTradesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually sync trades from connected brokers
    
    Supports filtering by:
    - venue: Specific exchange to sync from
    - symbols: List of symbols to import
    - start_date/end_date: Date range for historical import
    - limit: Maximum number of trades to import
    """
    
    # Get user's API keys
    api_keys_query = db.query(ApiKey).filter(ApiKey.user_id == current_user.id)
    
    if request.venue:
        api_keys_query = api_keys_query.filter(ApiKey.venue == request.venue.lower())
    
    api_keys = api_keys_query.all()
    
    if not api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connected brokers found"
        )
    
    sync_results = []
    
    for api_key in api_keys:
        try:
            # Decrypt credentials
            decrypted_key = encryption_service.decrypt(api_key.key_enc)
            decrypted_secret = encryption_service.decrypt(api_key.secret_enc)
            
            # Initialize broker service based on auth method
            if api_key.venue == 'hyperliquid':
                wallet_address = api_key.meta.get('wallet_address') or decrypted_key
                broker_service = BrokerService(
                    venue=api_key.venue,
                    api_key=decrypted_secret if decrypted_secret else None,
                    wallet_address=wallet_address
                )
            elif api_key.venue == 'coinbase':
                # Coinbase uses OAuth - decrypted_key is access_token
                broker_service = BrokerService(
                    venue=api_key.venue,
                    oauth_token=decrypted_key
                )
            else:
                # Kraken and others use API keys
                broker_service = BrokerService(
                    venue=api_key.venue,
                    api_key=decrypted_key,
                    api_secret=decrypted_secret
                )
            
            # Fetch trades from broker
            broker_trades = broker_service.get_trades(
                since=request.start_date,
                until=request.end_date,
                limit=request.limit,
                symbols=request.symbols
            )
            
            logger.info(f"Fetched {len(broker_trades)} trades from {api_key.venue}")
            
            # Match positions and calculate PnL if not already provided
            if broker_trades:
                broker_trades = match_and_calculate_pnl(broker_trades)
            
            # Import trades into database
            trades_added = 0
            trades_updated = 0
            trades_skipped = 0
            trades_errors = 0
            
            for broker_trade in broker_trades:
                try:
                    # Check if trade already exists (by order_ref and venue)
                    existing_trade = None
                    if broker_trade.get('order_ref'):
                        existing_trade = db.query(Trade).filter(
                            Trade.user_id == current_user.id,
                            Trade.order_ref == broker_trade['order_ref'],
                            Trade.venue == broker_trade['venue']
                        ).first()
                    
                    if existing_trade:
                        trades_skipped += 1
                        continue
                    
                    # Create new trade
                    new_trade = Trade(
                        id=str(uuid.uuid4()),
                        user_id=current_user.id,
                        account=api_key.venue,
                        venue=broker_trade['venue'],
                        symbol=broker_trade['symbol'],
                        side=broker_trade['side'],
                        qty=broker_trade['qty'],
                        avg_price=broker_trade['avg_price'],
                        fees=broker_trade.get('fees', 0),
                        pnl=broker_trade.get('pnl', 0),
                        filled_at=broker_trade['filled_at'],
                        submitted_at=broker_trade.get('submitted_at', broker_trade['filled_at']),
                        order_ref=broker_trade.get('order_ref'),
                        raw=broker_trade.get('raw')
                    )
                    
                    db.add(new_trade)
                    trades_added += 1
                    
                except Exception as e:
                    logger.error("Failed to import trade", error=str(e))
                    trades_errors += 1
            
            db.commit()
            
            # Update last sync time in metadata
            if not api_key.meta:
                api_key.meta = {}
            api_key.meta['last_sync'] = datetime.utcnow().isoformat()
            db.commit()
            
            sync_results.append(SyncTradesResponse(
                venue=api_key.venue,
                synced_count=len(broker_trades),
                skipped_count=trades_skipped,
                error_count=trades_errors,
                trades_added=trades_added,
                trades_updated=trades_updated,
                message=f"Synced {trades_added} new trades from {api_key.venue}"
            ))
            
        except Exception as e:
            logger.error("Failed to sync trades from venue", venue=api_key.venue, error=str(e), exc_info=True)
            sync_results.append(SyncTradesResponse(
                venue=api_key.venue,
                synced_count=0,
                skipped_count=0,
                error_count=0,
                trades_added=0,
                trades_updated=0,
                message=f"Error: {str(e)}"
            ))
    
    return sync_results

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

@router.delete("/connections/{connection_id}")
async def disconnect_broker(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect and delete a broker connection"""
    
    # Find API key
    api_key = db.query(ApiKey).filter(
        ApiKey.id == connection_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    venue = api_key.venue
    db.delete(api_key)
    db.commit()
    
    logger.info("Broker connection deleted", user_id=str(current_user.id), venue=venue, connection_id=connection_id)
    
    return {"message": f"Successfully disconnected from {venue}"}
