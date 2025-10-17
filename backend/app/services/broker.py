"""
Broker integration services
"""

import ccxt
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from app.services.hyperliquid_service import HyperliquidService
from app.services.coinbase_service import CoinbaseService

logger = structlog.get_logger()

class BrokerService:
    """Service for interacting with broker APIs"""
    
    def __init__(self, venue: str, api_key: str = None, api_secret: str = None, wallet_address: str = None, oauth_token: str = None):
        self.venue = venue.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.wallet_address = wallet_address
        self.oauth_token = oauth_token
        self.exchange = None
        self.hyperliquid = None
        self.coinbase = None
        
        if api_key or wallet_address or oauth_token:
            self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize exchange client (CCXT for CEXes, native SDK for Hyperliquid)"""
        try:
            if self.venue == "hyperliquid":
                # Hyperliquid uses wallet address, not traditional API keys
                self.hyperliquid = HyperliquidService(
                    api_key=self.api_key,
                    wallet_address=self.wallet_address
                )
                logger.info("Initialized Hyperliquid service", wallet=self.wallet_address)
                
            elif self.venue == "kraken":
                self.exchange = ccxt.kraken({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'sandbox': False,
                    'rateLimit': 1000,
                })
            elif self.venue == "coinbase":
                # Coinbase uses OAuth2, not API keys
                if self.oauth_token:
                    self.coinbase = CoinbaseService(access_token=self.oauth_token)
                    logger.info("Initialized Coinbase OAuth service")
                else:
                    raise ValueError("Coinbase requires OAuth2 token. Use OAuth flow.")
            else:
                raise ValueError(f"Unsupported venue: {self.venue}")
                
        except Exception as e:
            logger.error("Failed to initialize exchange", venue=self.venue, error=str(e))
            raise
    
    def get_trades(self, symbol: str = None, since: datetime = None, until: datetime = None, limit: int = 1000, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch trades from broker
        
        Args:
            symbol: Single symbol to filter (legacy parameter)
            since: Start date filter
            until: End date filter
            limit: Maximum number of trades
            symbols: List of symbols to filter (for multi-symbol queries)
            
        Returns:
            List of normalized trades
        """
        try:
            # Hyperliquid uses native SDK
            if self.venue == "hyperliquid":
                if not self.hyperliquid:
                    raise ValueError("Hyperliquid service not initialized")
                
                # If specific symbols requested, use symbol-based query
                if symbols:
                    fills_by_symbol = self.hyperliquid.get_user_fills_by_symbol(
                        symbols=symbols,
                        start_time=since,
                        end_time=until,
                        limit_per_symbol=limit
                    )
                    # Flatten the dict of lists into a single list
                    all_fills = []
                    for symbol_fills in fills_by_symbol.values():
                        all_fills.extend(symbol_fills)
                    return all_fills[:limit]  # Limit total results
                else:
                    # Get all fills
                    return self.hyperliquid.get_user_fills(
                        start_time=since,
                        end_time=until,
                        limit=limit
                    )
            
            # Coinbase uses OAuth and native API
            if self.venue == "coinbase":
                if not self.coinbase:
                    raise ValueError("Coinbase service not initialized")
                
                # Get fills for specific symbol or all
                all_fills = []
                if symbols:
                    for sym in symbols:
                        # Convert BTC/USD to BTC-USD (Coinbase format)
                        product_id = sym.replace('/', '-')
                        fills = self.coinbase.get_fills(
                            product_id=product_id,
                            start_date=since,
                            end_date=until,
                            limit=limit
                        )
                        all_fills.extend(fills)
                else:
                    all_fills = self.coinbase.get_fills(
                        start_date=since,
                        end_date=until,
                        limit=limit
                    )
                
                return all_fills[:limit]
            
            # CCXT exchanges (Kraken, etc.)
            if not self.exchange:
                raise ValueError("Exchange not initialized")
            
            # Convert datetime to timestamp
            since_timestamp = int(since.timestamp() * 1000) if since else None
            
            # Fetch trades
            trades = self.exchange.fetch_my_trades(
                symbol=symbol,
                since=since_timestamp,
                limit=limit
            )
            
            # Normalize trades to our format
            normalized_trades = []
            for trade in trades:
                normalized_trade = {
                    "venue": self.venue.upper(),
                    "symbol": trade.get("symbol"),
                    "side": trade.get("side"),
                    "qty": trade.get("amount"),
                    "avg_price": trade.get("price"),
                    "fees": trade.get("fee", {}).get("cost", 0),
                    "filled_at": datetime.fromtimestamp(trade.get("timestamp") / 1000) if trade.get("timestamp") else None,
                    "submitted_at": datetime.fromtimestamp(trade.get("timestamp") / 1000) if trade.get("timestamp") else None,
                    "order_ref": trade.get("order"),
                    "raw": trade
                }
                normalized_trades.append(normalized_trade)
            
            return normalized_trades
            
        except Exception as e:
            logger.error("Failed to fetch trades", venue=self.venue, error=str(e))
            raise
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        try:
            # Hyperliquid positions
            if self.venue == "hyperliquid":
                if not self.hyperliquid:
                    raise ValueError("Hyperliquid service not initialized")
                return self.hyperliquid.get_positions()
            
            # Coinbase positions via OAuth
            if self.venue == "coinbase":
                if not self.coinbase:
                    raise ValueError("Coinbase service not initialized")
                
                # Get accounts and build position dict
                accounts = self.coinbase.get_accounts()
                positions = {}
                for account in accounts:
                    currency = account.get('currency')
                    available_balance = float(account.get('available_balance', {}).get('value', 0))
                    if available_balance > 0:
                        positions[currency] = {
                            'free': available_balance,
                            'used': 0,  # Coinbase doesn't provide this in OAuth API
                            'total': available_balance
                        }
                return positions
            
            # CCXT exchanges (Kraken)
            if not self.exchange:
                raise ValueError("Exchange not initialized")
            
            # Fetch balance/positions
            balance = self.exchange.fetch_balance()
            
            # Extract positions (non-zero balances)
            positions = {}
            for currency, amount in balance.get("free", {}).items():
                if amount > 0:
                    positions[currency] = {
                        "free": amount,
                        "used": balance.get("used", {}).get(currency, 0),
                        "total": balance.get("total", {}).get(currency, 0)
                    }
            
            return positions
            
        except Exception as e:
            logger.error("Failed to fetch positions", venue=self.venue, error=str(e))
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return connection info"""
        try:
            # Hyperliquid connection test
            if self.venue == "hyperliquid":
                if not self.hyperliquid:
                    return {'connected': False, 'error': 'Service not initialized'}
                return self.hyperliquid.test_connection(self.wallet_address)
            
            # Coinbase OAuth connection test
            if self.venue == "coinbase":
                if not self.coinbase:
                    return {'connected': False, 'error': 'Service not initialized'}
                try:
                    accounts = self.coinbase.get_accounts()
                    return {
                        'connected': True,
                        'venue': 'coinbase',
                        'accounts_count': len(accounts)
                    }
                except Exception as e:
                    return {'connected': False, 'error': str(e)}
            
            # CCXT exchanges (Kraken)
            if not self.exchange:
                return {'connected': False, 'error': 'Exchange not initialized'}
            
            # Try to fetch account info
            balance = self.exchange.fetch_balance()
            return {
                'connected': True,
                'venue': self.venue,
                'total_value': sum(balance.get('total', {}).values()),
                'currencies': len([c for c, v in balance.get('total', {}).items() if v > 0])
            }
            
        except Exception as e:
            logger.error("Connection test failed", venue=self.venue, error=str(e))
            return {'connected': False, 'error': str(e)}
