"""
Coinbase Advanced Trade API service (using OAuth2 tokens)
Docs: https://docs.cloud.coinbase.com/advanced-trade-api/docs/welcome
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

class CoinbaseService:
    """Service for Coinbase Advanced Trade API"""
    
    API_BASE = "https://api.coinbase.com/api/v3/brokerage"
    
    def __init__(self, access_token: str):
        """
        Initialize Coinbase service with OAuth access token
        
        Args:
            access_token: OAuth2 access token
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts"""
        try:
            response = requests.get(f"{self.API_BASE}/accounts", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get('accounts', [])
        except Exception as e:
            logger.error("Failed to get accounts", error=str(e))
            raise
    
    def get_fills(
        self,
        product_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get order fills (executed trades)
        
        Args:
            product_id: Specific product (e.g., "BTC-USD")
            start_date: Start date filter
            end_date: End date filter
            limit: Max number of fills
            
        Returns:
            List of fill dictionaries
        """
        try:
            params = {}
            if product_id:
                params['product_id'] = product_id
            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            if limit:
                params['limit'] = min(limit, 1000)  # Coinbase max is 1000
            
            response = requests.get(
                f"{self.API_BASE}/orders/historical/fills",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            fills = data.get('fills', [])
            
            # Normalize fills to our format
            normalized = []
            for fill in fills:
                normalized.append(self._normalize_fill(fill))
            
            return normalized
            
        except Exception as e:
            logger.error("Failed to get fills", error=str(e))
            raise
    
    def _normalize_fill(self, fill: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Coinbase fill to our trade format
        
        Coinbase fill structure:
        {
            "entry_id": "22222-fccfb",
            "trade_id": "1111",
            "order_id": "0000-000000-000000",
            "trade_time": "2021-05-31T09:59:59Z",
            "trade_type": "FILL",
            "price": "10000.00",
            "size": "0.001",
            "commission": "1.25",
            "product_id": "BTC-USD",
            "sequence_timestamp": "2021-05-31T09:58:59Z",
            "liquidity_indicator": "UNKNOWN_LIQUIDITY_INDICATOR",
            "size_in_quote": false,
            "user_id": "1111-000000-000000",
            "side": "BUY" or "SELL"
        }
        """
        side_map = {'BUY': 'buy', 'SELL': 'sell'}
        
        return {
            'venue': 'COINBASE',
            'symbol': fill.get('product_id', '').replace('-', '/'),  # BTC-USD -> BTC/USD
            'side': side_map.get(fill.get('side', 'BUY'), 'buy'),
            'qty': float(fill.get('size', 0)),
            'avg_price': float(fill.get('price', 0)),
            'fees': float(fill.get('commission', 0)),
            'pnl': 0,  # Coinbase doesn't provide PnL directly
            'filled_at': datetime.fromisoformat(fill.get('trade_time', '').replace('Z', '+00:00')),
            'submitted_at': datetime.fromisoformat(fill.get('sequence_timestamp', '').replace('Z', '+00:00')),
            'order_ref': fill.get('order_id'),
            'raw': fill,
            'meta': {
                'trade_id': fill.get('trade_id'),
                'entry_id': fill.get('entry_id'),
                'liquidity': fill.get('liquidity_indicator')
            }
        }

