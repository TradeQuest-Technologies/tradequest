"""
Polygon.io market data service for stocks, crypto, forex, and options
"""

from polygon import RESTClient
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
from app.core.config import settings

logger = structlog.get_logger()

class PolygonService:
    """Service for fetching market data from Polygon.io"""
    
    def __init__(self):
        api_key = settings.POLYGON_API_KEY
        if not api_key:
            logger.warning("POLYGON_API_KEY not configured")
            self.client = None
        else:
            self.client = RESTClient(api_key)
    
    async def get_stock_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock ticker data using previous close"""
        if not self.client:
            return None
            
        try:
            # Get previous close - returns an object
            prev_close_data = list(self.client.get_previous_close_agg(symbol))
            
            if not prev_close_data or len(prev_close_data) == 0:
                logger.warning("No data returned for stock", symbol=symbol)
                return None
            
            data = prev_close_data[0]
            
            # Polygon returns PreviousCloseAgg objects - convert to dict
            close_price = float(data.close) if hasattr(data, 'close') else 0
            open_price = float(data.open) if hasattr(data, 'open') else 0
            high_price = float(data.high) if hasattr(data, 'high') else 0
            low_price = float(data.low) if hasattr(data, 'low') else 0
            volume = float(data.volume) if hasattr(data, 'volume') else 0
            
            change = close_price - open_price
            change_percent = (change / open_price) if open_price > 0 else 0
            
            logger.info("Fetched stock ticker", symbol=symbol, price=close_price)
            
            return {
                "symbol": symbol,
                "name": symbol,
                "price": close_price,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "change24h": change,
                "changePercent24h": change_percent,
                "volume24h": volume,
                "timestamp": int(data.timestamp) if hasattr(data, 'timestamp') else 0
            }
        except Exception as e:
            logger.error("Failed to fetch stock ticker", symbol=symbol, error=str(e))
            return None
    
    async def get_crypto_ticker(self, from_currency: str, to_currency: str = "USD") -> Optional[Dict[str, Any]]:
        """Get current crypto ticker data using previous close"""
        if not self.client:
            return None
            
        try:
            # Get previous close for crypto
            ticker = f"X:{from_currency}{to_currency}"
            prev_close_data = list(self.client.get_previous_close_agg(ticker))
            
            if not prev_close_data or len(prev_close_data) == 0:
                return None
            
            data = prev_close_data[0]
            
            # Access object attributes, not dict keys
            close_price = getattr(data, 'close', 0)
            open_price = getattr(data, 'open', 0)
            high_price = getattr(data, 'high', 0)
            low_price = getattr(data, 'low', 0)
            volume = getattr(data, 'volume', 0)
            
            change = close_price - open_price
            change_percent = (change / open_price) if open_price > 0 else 0
            
            return {
                "symbol": f"{from_currency}/{to_currency}",
                "name": from_currency,
                "price": close_price,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "change24h": change,
                "changePercent24h": change_percent,
                "volume24h": volume,
                "timestamp": getattr(data, 'timestamp', 0)
            }
        except Exception as e:
            logger.error("Failed to fetch crypto ticker", symbol=f"{from_currency}/{to_currency}", error=str(e))
            return None
    
    async def get_popular_tickers(self, market_type: str = "stocks") -> List[Dict[str, Any]]:
        """Get popular tickers (using predefined lists for free tier)
        
        Args:
            market_type: "stocks" or "crypto"
        """
        if not self.client:
            return []
            
        try:
            tickers = []
            
            if market_type == "stocks":
                # Popular stocks
                symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "AMD", "NFLX", "DIS", 
                          "BABA", "PYPL", "INTC", "CSCO", "ADBE", "CRM", "ORCL", "IBM", "QCOM", "TXN"]
            else:  # crypto
                # Popular crypto
                symbols = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK", "UNI", "AAVE", "DOT", "ADA"]
                
            for symbol in symbols:
                ticker_data = await self.get_stock_ticker(symbol) if market_type == "stocks" else await self.get_crypto_ticker(symbol, "USD")
                if ticker_data:
                    tickers.append(ticker_data)
            
            return tickers
        except Exception as e:
            logger.error("Failed to fetch popular tickers", error=str(e))
            return []
    
    async def search_tickers(self, query: str, market_type: str = "stocks", limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tickers using Polygon's server-side search
        
        Args:
            query: Search query
            market_type: "stocks", "crypto", "fx"
            limit: Number of results to return
        """
        if not self.client:
            return []
            
        try:
            # Use Polygon's reference tickers endpoint with search parameter
            results = list(self.client.list_tickers(
                search=query,
                market=market_type,
                active=True,
                limit=limit
            ))
            
            tickers = []
            for result in results:
                tickers.append({
                    "ticker": result.ticker,
                    "symbol": result.ticker,
                    "name": result.name,
                    "market": result.market,
                    "type": getattr(result, 'type', ''),
                    "active": result.active,
                    "exchange": getattr(result, 'primary_exchange', '')
                })
            
            logger.info("Polygon ticker search completed", 
                       query=query, 
                       results_count=len(tickers))
            
            return tickers
        except Exception as e:
            logger.error("Failed to search tickers", error=str(e))
            return []
