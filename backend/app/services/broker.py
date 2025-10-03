"""
Broker integration services
"""

import ccxt
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class BrokerService:
    """Service for interacting with broker APIs"""
    
    def __init__(self, venue: str, api_key: str = None, api_secret: str = None):
        self.venue = venue.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        
        if api_key and api_secret:
            self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize CCXT exchange instance"""
        try:
            if self.venue == "kraken":
                self.exchange = ccxt.kraken({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'sandbox': False,  # TODO: Make configurable
                    'rateLimit': 1000,
                })
            elif self.venue == "coinbase":
                self.exchange = ccxt.coinbasepro({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'password': '',  # Coinbase Pro passphrase
                    'sandbox': False,  # TODO: Make configurable
                    'rateLimit': 1000,
                })
            else:
                raise ValueError(f"Unsupported venue: {self.venue}")
                
        except Exception as e:
            logger.error("Failed to initialize exchange", venue=self.venue, error=str(e))
            raise
    
    def get_trades(self, symbol: str = None, since: datetime = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch trades from broker"""
        if not self.exchange:
            raise ValueError("Exchange not initialized")
        
        try:
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
                    "filled_at": trade.get("timestamp"),
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
        if not self.exchange:
            raise ValueError("Exchange not initialized")
        
        try:
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
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            if not self.exchange:
                return False
            
            # Try to fetch account info
            self.exchange.fetch_balance()
            return True
            
        except Exception as e:
            logger.error("Connection test failed", venue=self.venue, error=str(e))
            return False
