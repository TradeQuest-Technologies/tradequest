"""
Broker websocket endpoints for real-time trade sync
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
import structlog
import asyncio
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.auth import verify_token
from app.models.user import User
from app.models.api_key import ApiKey
from app.models.trade import Trade
from app.services.hyperliquid_service import HyperliquidService
from app.services.encryption_service import encryption_service

logger = structlog.get_logger()

router = APIRouter()

@router.websocket("/live/{venue}")
async def live_trade_sync(
    websocket: WebSocket,
    venue: str,
    token: str
):
    """
    WebSocket endpoint for real-time trade synchronization
    
    Usage:
    1. Connect to ws://api/v1/broker/live/{venue}?token={access_token}
    2. Receive real-time trade updates as they execute on the exchange
    3. Trades are automatically saved to the database
    """
    await websocket.accept()
    
    try:
        # Authenticate user
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Verify token
            payload = verify_token(token)
            user_email = payload.get("sub")
            if not user_email:
                raise ValueError("Invalid token")
            
            # Get user
            user = db.query(User).filter(User.email == user_email).first()
            if not user:
                raise ValueError("User not found")
                
        except Exception as e:
            await websocket.send_json({'error': 'Authentication failed', 'detail': str(e)})
            await websocket.close()
            return
        
        # Find API key for this venue
        api_key = db.query(ApiKey).filter(
            ApiKey.user_id == user.id,
            ApiKey.venue == venue.lower()
        ).first()
        
        if not api_key:
            await websocket.send_json({'error': f'No connection found for {venue}'})
            await websocket.close()
            return
        
        # Currently only Hyperliquid supports websocket
        if venue.lower() != 'hyperliquid':
            await websocket.send_json({'error': 'Live sync only available for Hyperliquid'})
            await websocket.close()
            return
        
        # Decrypt credentials
        decrypted_key = encryption_service.decrypt(api_key.key_enc)
        decrypted_secret = encryption_service.decrypt(api_key.secret_enc) if api_key.secret_enc else None
        wallet_address = api_key.meta.get('wallet_address') or decrypted_key
        
        # Initialize Hyperliquid service
        hl_service = HyperliquidService(
            api_key=decrypted_secret,
            wallet_address=wallet_address
        )
        
        logger.info("Starting live trade sync", user_id=user.id, venue=venue, wallet=wallet_address)
        
        # Send confirmation
        await websocket.send_json({
            'type': 'connected',
            'venue': venue,
            'wallet': wallet_address,
            'message': 'Live trade sync started'
        })
        
        # Callback for new fills
        async def on_new_fill(fill: dict):
            """Handle new fill from websocket"""
            try:
                # Check if trade already exists
                existing = db.query(Trade).filter(
                    Trade.user_id == user.id,
                    Trade.order_ref == fill.get('order_ref'),
                    Trade.venue == 'HYPERLIQUID'
                ).first()
                
                if existing:
                    logger.debug("Trade already exists, skipping", order_ref=fill.get('order_ref'))
                    return
                
                # Create new trade
                new_trade = Trade(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    account=venue,
                    venue='HYPERLIQUID',
                    symbol=fill['symbol'],
                    side=fill['side'],
                    qty=fill['qty'],
                    avg_price=fill['avg_price'],
                    fees=fill.get('fees', 0),
                    pnl=fill.get('pnl', 0),
                    filled_at=fill['filled_at'],
                    submitted_at=fill.get('submitted_at', fill['filled_at']),
                    order_ref=fill.get('order_ref'),
                    raw=fill.get('raw')
                )
                
                db.add(new_trade)
                db.commit()
                
                logger.info("New trade added via live sync", symbol=fill['symbol'], side=fill['side'])
                
                # Send confirmation to frontend
                await websocket.send_json({
                    'type': 'trade_added',
                    'trade': {
                        'id': new_trade.id,
                        'symbol': new_trade.symbol,
                        'side': new_trade.side,
                        'qty': float(new_trade.qty),
                        'price': float(new_trade.avg_price),
                        'pnl': float(new_trade.pnl),
                        'filled_at': new_trade.filled_at.isoformat()
                    }
                })
                
            except Exception as e:
                logger.error("Failed to process live fill", error=str(e), exc_info=True)
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Failed to process trade: {str(e)}'
                })
        
        # Subscribe to live fills
        await hl_service.subscribe_to_user_fills(wallet_address, on_new_fill)
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", user_id=user.id if 'user' in locals() else None)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), exc_info=True)
        try:
            await websocket.send_json({'error': 'Internal error', 'detail': str(e)})
        except:
            pass
    finally:
        if 'db' in locals():
            db.close()

