"""
Hyperliquid exchange integration service
Official docs: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
Python SDK: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import structlog
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

logger = structlog.get_logger()

class HyperliquidService:
    """Service for interacting with Hyperliquid DEX API"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, wallet_address: str = None):
        """
        Initialize Hyperliquid service
        
        Args:
            api_key: API key (wallet private key for trading)
            api_secret: Not used for Hyperliquid (uses wallet signature)
            wallet_address: User's wallet address for read-only operations
        """
        self.wallet_address = wallet_address
        self.api_key = api_key  # This is the private key for signing
        
        # Initialize Info API (read-only, no auth needed)
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        
        # Initialize Exchange API (requires private key for trading)
        self.exchange = None
        if api_key:
            try:
                self.exchange = Exchange(
                    wallet=None,  # Will use wallet_address for signing
                    base_url=constants.MAINNET_API_URL,
                    account_address=wallet_address
                )
            except Exception as e:
                logger.warning("Could not initialize Exchange API", error=str(e))
    
    def get_user_fills(
        self, 
        wallet_address: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get historical fills (executed trades) for a user
        
        Args:
            wallet_address: Wallet address to query (uses self.wallet_address if not provided)
            start_time: Filter fills after this time
            end_time: Filter fills before this time
            limit: Maximum number of fills to return
            
        Returns:
            List of fill dictionaries with normalized structure
        """
        try:
            address = wallet_address or self.wallet_address
            if not address:
                raise ValueError("wallet_address is required")
            
            # Get user fills from Hyperliquid
            fills = self.info.user_fills(address)
            
            logger.info(f"Retrieved {len(fills)} fills from Hyperliquid", wallet=address)
            
            # Filter by date range if provided
            filtered_fills = []
            for fill in fills:
                fill_time = datetime.fromtimestamp(fill.get('time', 0) / 1000)  # Convert ms to seconds
                
                if start_time and fill_time < start_time:
                    continue
                if end_time and fill_time > end_time:
                    continue
                
                filtered_fills.append(fill)
                
                if len(filtered_fills) >= limit:
                    break
            
            # Normalize fills to our trade format
            normalized_trades = []
            for fill in filtered_fills:
                normalized_trade = self._normalize_fill(fill)
                if normalized_trade:
                    normalized_trades.append(normalized_trade)
            
            logger.info(f"Normalized {len(normalized_trades)} fills after filtering")
            return normalized_trades
            
        except Exception as e:
            logger.error("Failed to fetch Hyperliquid fills", error=str(e), exc_info=True)
            raise
    
    def get_user_fills_by_symbol(
        self,
        symbols: List[str],
        wallet_address: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit_per_symbol: int = 500
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get fills filtered by specific symbols
        
        Returns:
            Dict mapping symbol -> list of fills
        """
        try:
            # Get all fills first
            all_fills = self.get_user_fills(
                wallet_address=wallet_address,
                start_time=start_time,
                end_time=end_time,
                limit=limit_per_symbol * len(symbols)
            )
            
            # Group by symbol
            fills_by_symbol = {symbol: [] for symbol in symbols}
            for fill in all_fills:
                symbol = fill.get('symbol')
                if symbol in fills_by_symbol:
                    fills_by_symbol[symbol].append(fill)
                    if len(fills_by_symbol[symbol]) >= limit_per_symbol:
                        # Check if we've hit the limit for all symbols
                        if all(len(fills) >= limit_per_symbol for fills in fills_by_symbol.values()):
                            break
            
            return fills_by_symbol
            
        except Exception as e:
            logger.error("Failed to fetch fills by symbol", error=str(e))
            raise
    
    def get_positions(self, wallet_address: str = None) -> Dict[str, Any]:
        """
        Get current positions/balances
        
        Returns:
            Dict with asset positions and margin info
        """
        try:
            address = wallet_address or self.wallet_address
            if not address:
                raise ValueError("wallet_address is required")
            
            # Get user state (includes positions and balances)
            user_state = self.info.user_state(address)
            
            positions = {}
            
            # Extract asset positions
            if 'assetPositions' in user_state:
                for position in user_state['assetPositions']:
                    coin = position.get('position', {}).get('coin')
                    if coin:
                        positions[coin] = {
                            'size': float(position.get('position', {}).get('szi', 0)),
                            'entry_px': float(position.get('position', {}).get('entryPx', 0)),
                            'position_value': float(position.get('position', {}).get('positionValue', 0)),
                            'unrealized_pnl': float(position.get('position', {}).get('unrealizedPnl', 0)),
                            'return_on_equity': float(position.get('position', {}).get('returnOnEquity', 0)),
                            'leverage': float(position.get('position', {}).get('leverage', {}).get('value', 1)),
                        }
            
            # Add account value info
            margin_summary = user_state.get('marginSummary', {})
            positions['_account_value'] = float(margin_summary.get('accountValue', 0))
            positions['_total_margin_used'] = float(margin_summary.get('totalMarginUsed', 0))
            positions['_total_ntl_pos'] = float(margin_summary.get('totalNtlPos', 0))
            positions['_total_rawUsd'] = float(margin_summary.get('totalRawUsd', 0))
            
            return positions
            
        except Exception as e:
            logger.error("Failed to fetch Hyperliquid positions", error=str(e))
            raise
    
    def _normalize_fill(self, fill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize a Hyperliquid fill to our trade format
        
        Hyperliquid fill structure:
        {
            "coin": "ETH",
            "px": "1234.56",  # Price
            "sz": "0.5",  # Size
            "side": "B" or "A",  # Buy or Ask (sell)
            "time": 1234567890123,  # Timestamp in ms
            "startPosition": "0.0",
            "dir": "Open Long" | "Close Long" | etc,
            "closedPnl": "12.34",
            "hash": "0x...",
            "oid": 123456,  # Order ID
            "crossed": true,
            "fee": "1.23",
            "tid": 789012,  # Trade ID
            "feeToken": "USDC"
        }
        """
        try:
            # Convert Hyperliquid side to our format
            side_map = {
                'B': 'buy',
                'A': 'sell'
            }
            
            side = side_map.get(fill.get('side', ''), 'buy')
            
            # Calculate PnL (closedPnl is only set when closing a position)
            pnl = float(fill.get('closedPnl', 0)) if fill.get('closedPnl') else 0.0
            
            # Extract time (convert from ms to datetime)
            fill_time_ms = fill.get('time', 0)
            fill_time = datetime.fromtimestamp(fill_time_ms / 1000)
            
            normalized = {
                'venue': 'HYPERLIQUID',
                'symbol': fill.get('coin', 'UNKNOWN'),
                'side': side,
                'qty': abs(float(fill.get('sz', 0))),  # Absolute value of size
                'avg_price': float(fill.get('px', 0)),
                'fees': abs(float(fill.get('fee', 0))),
                'pnl': pnl,
                'filled_at': fill_time,
                'submitted_at': fill_time,  # Hyperliquid doesn't distinguish submission time
                'order_ref': str(fill.get('oid', '')),  # Order ID
                'raw': json.dumps(fill),  # Store full raw data
                'meta': {
                    'trade_id': fill.get('tid'),
                    'tx_hash': fill.get('hash'),
                    'direction': fill.get('dir'),  # "Open Long", "Close Long", etc.
                    'start_position': fill.get('startPosition'),
                    'crossed': fill.get('crossed', False),
                    'fee_token': fill.get('feeToken', 'USDC')
                }
            }
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to normalize Hyperliquid fill", fill=fill, error=str(e))
            return None
    
    async def subscribe_to_user_fills(
        self,
        wallet_address: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to real-time fill updates via WebSocket
        
        Args:
            wallet_address: Wallet to monitor
            callback: Function to call when new fill arrives
        """
        try:
            # Hyperliquid WebSocket for user fills
            from hyperliquid.websocket import Websocket
            
            ws = Websocket(constants.MAINNET_API_URL)
            
            def on_fill(fill_data):
                """Handle incoming fill from websocket"""
                try:
                    normalized = self._normalize_fill(fill_data)
                    if normalized:
                        callback(normalized)
                except Exception as e:
                    logger.error("Error processing websocket fill", error=str(e))
            
            # Subscribe to user fills channel
            subscription = {
                "method": "subscribe",
                "subscription": {
                    "type": "userFills",
                    "user": wallet_address
                }
            }
            
            ws.subscribe(subscription, on_fill)
            
            logger.info("Subscribed to Hyperliquid user fills", wallet=wallet_address)
            
            # Keep connection alive
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error("WebSocket connection error", error=str(e))
            raise
    
    def test_connection(self, wallet_address: str = None) -> Dict[str, Any]:
        """
        Test connection to Hyperliquid API
        
        Returns:
            Dict with connection status and basic account info
        """
        try:
            address = wallet_address or self.wallet_address
            if not address:
                return {
                    'connected': False,
                    'error': 'No wallet address provided'
                }
            
            # Try to fetch user state
            user_state = self.info.user_state(address)
            
            # Extract basic info
            margin_summary = user_state.get('marginSummary', {})
            
            return {
                'connected': True,
                'wallet_address': address,
                'account_value': float(margin_summary.get('accountValue', 0)),
                'positions_count': len(user_state.get('assetPositions', [])),
                'network': 'mainnet'
            }
            
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return {
                'connected': False,
                'error': str(e)
            }

