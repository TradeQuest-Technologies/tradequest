"""
Market data service using CCXT
"""

import ccxt
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()

class MarketDataService:
    """Service for fetching market data from various exchanges"""
    
    def __init__(self):
        self.exchanges = {
            'kraken': ccxt.kraken(),
            'coinbase': ccxt.coinbasepro(),
            'binance': ccxt.binance(),  # For additional data sources
        }
    
    async def get_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 1000) -> List[List]:
        """Get OHLCV data for a symbol"""
        
        # Try exchanges in order of preference
        for exchange_name, exchange in self.exchanges.items():
            try:
                if symbol in exchange.markets:
                    # Fetch OHLCV data
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    
                    # Convert to list of dictionaries for easier handling
                    candles = []
                    for candle in ohlcv:
                        candles.append({
                            "timestamp": candle[0],
                            "open": candle[1],
                            "high": candle[2],
                            "low": candle[3],
                            "close": candle[4],
                            "volume": candle[5]
                        })
                    
                    logger.info("OHLCV fetched", symbol=symbol, timeframe=timeframe, count=len(candles), exchange=exchange_name)
                    return candles
                    
            except Exception as e:
                logger.warning("Failed to fetch from exchange", exchange=exchange_name, symbol=symbol, error=str(e))
                continue
        
        raise Exception(f"Failed to fetch OHLCV data for {symbol} from any exchange")
    
    async def get_ohlcv_range(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get OHLCV data for a specific time range"""
        
        # Calculate number of candles needed
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        total_minutes = int((end_time - start_time).total_seconds() / 60)
        limit = min(total_minutes // timeframe_minutes + 10, 1000)  # Add buffer, cap at 1000
        
        # Get OHLCV data
        candles = await self.get_ohlcv(symbol, timeframe, limit)
        
        # Filter by time range
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        filtered_candles = [
            candle for candle in candles
            if start_timestamp <= candle["timestamp"] <= end_timestamp
        ]
        
        return filtered_candles
    
    async def get_symbols(self, venue: Optional[str] = None) -> List[str]:
        """Get available trading symbols"""
        
        if venue and venue in self.exchanges:
            exchange = self.exchanges[venue]
            return list(exchange.markets.keys())
        
        # Return symbols from all exchanges (deduplicated)
        all_symbols = set()
        for exchange in self.exchanges.values():
            all_symbols.update(exchange.markets.keys())
        
        return sorted(list(all_symbols))
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes"""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440,
        }
        return timeframe_map.get(timeframe, 1)
