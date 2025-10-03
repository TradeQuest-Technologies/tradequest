"""
OHLCV Service - Fetches historical price data for trades
Uses Polygon.io for stocks and Binance Vision for crypto
"""

import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import ccxt
from app.services.polygon_service import PolygonService
from app.services.polygon_flatfiles_service import PolygonFlatFilesService
from app.services.binance_vision_service import BinanceVisionService
from app.core.config import settings

logger = structlog.get_logger()


class OHLCVService:
    """Service to fetch OHLCV data from Polygon (stocks) and Binance Vision (crypto)"""
    
    def __init__(self):
        # Initialize services
        self.polygon_service = PolygonService()
        self.binance_vision = BinanceVisionService()
        
        # Initialize Polygon flat files if credentials available
        self.polygon_flatfiles = None
        if settings.POLYGON_S3_ACCESS_KEY and settings.POLYGON_S3_SECRET_KEY:
            self.polygon_flatfiles = PolygonFlatFilesService(
                access_key=settings.POLYGON_S3_ACCESS_KEY,
                secret_key=settings.POLYGON_S3_SECRET_KEY
            )
        
        # CCXT as backup for crypto when Binance Vision fails
        self.exchanges = {
            'binance': ccxt.binance(),
            'coinbase': ccxt.coinbasepro(),
            'kraken': ccxt.kraken()
        }
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        exchange: str = "binance",
        asset_type: str = "crypto"
    ) -> List[Dict[str, Any]]:
        """
        Fetch OHLCV data for a symbol using appropriate source
        
        Args:
            symbol: Trading pair (e.g., BTC/USDT for crypto, AAPL for stocks)
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            start_time: Start datetime
            end_time: End datetime
            exchange: Exchange name (binance, polygon, etc.)
            asset_type: 'crypto' or 'stock'
        
        Returns:
            List of OHLCV candles
        """
        
        try:
            # Route based on asset type
            if "/" in symbol or "_" in symbol:
                # Crypto - use Binance Vision, fallback to CCXT
                return await self._fetch_crypto_ohlcv(symbol, timeframe, start_time, end_time)
            else:
                # Stocks/Forex - use Polygon Flat Files
                return await self._fetch_polygon_ohlcv(symbol, timeframe, start_time, end_time)
            
        except Exception as e:
            logger.error("Failed to fetch OHLCV data", 
                        error=str(e), 
                        symbol=symbol, 
                        timeframe=timeframe)
            return []

    async def get_aggtrades(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        exchange: str = "binance",
        asset_type: str = "crypto"
    ) -> List[Dict[str, Any]]:
        """
        Fetch aggregated trades data for more granular analysis
        
        Args:
            symbol: Trading pair (e.g., BTC/USDT for crypto)
            start_time: Start datetime
            end_time: End datetime
            exchange: Exchange name (binance, polygon, etc.)
            asset_type: 'crypto' or 'stock'
        
        Returns:
            List of aggregated trade records
        """
        
        try:
            if "/" in symbol or "_" in symbol:
                # Crypto - use Binance Vision aggtrades
                if self.binance_vision:
                    return await self.binance_vision.get_agg_trades(
                        symbol=symbol,
                        start_time=start_time,
                        end_time=end_time,
                        market_type="futures/um" if symbol.endswith('USDT') else "spot"
                    )
                else:
                    logger.warning("Binance Vision not available for aggtrades")
                    return []
            else:
                # Stocks don't typically have aggtrades data in the same format
                logger.warning("AggTrades not available for stocks", symbol=symbol)
                return []
            
        except Exception as e:
            logger.error("Failed to fetch aggtrades data", 
                        error=str(e), 
                        symbol=symbol)
            return []
    
    async def _fetch_crypto_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Fetch crypto OHLCV: Binance Vision ONLY (no live API calls)"""
        
        if not start_time or not end_time:
            logger.error("Start and end time required for crypto OHLCV")
            return []
        
        # Use Binance Vision (data.binance.vision flat files)
        klines = await self.binance_vision.get_klines(
            symbol=symbol,
            interval=timeframe,
            start_time=start_time,
            end_time=end_time,
            market_type="futures/um"  # USDT-M Perpetual Futures
        )
        
        # If Binance Vision returns data, use it
        if klines:
            result = []
            for kline in klines:
                result.append({
                    "timestamp": datetime.fromtimestamp(kline['open_time'] / 1000).isoformat(),
                    "open": kline['open'],
                    "high": kline['high'],
                    "low": kline['low'],
                    "close": kline['close'],
                    "volume": kline['volume']
                })
            
            logger.info("Fetched Binance Vision OHLCV",
                       symbol=symbol,
                       candles=len(result))
            return result
        
        # No fallback to live API - return empty if data not available
        logger.warning("Binance Vision returned no data (may be future dates or missing symbol)",
                      symbol=symbol,
                      start=start_time.isoformat(),
                      end=end_time.isoformat())
        return []
    
    async def _fetch_polygon_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Fetch from Polygon flat files for all assets (stocks, crypto, forex)"""
        
        if not self.polygon_flatfiles:
            logger.error("Polygon S3 credentials not configured")
            return []
        
        if not start_time or not end_time:
            logger.error("Start and end time required for Polygon flat files")
            return []
        
        try:
            # Detect asset type and convert symbol to Polygon format
            asset_type = "stocks"
            ticker = symbol.upper()
            
            # Convert crypto symbols to Polygon format
            # DOGE_USDT/USDT -> X:DOGEUSD
            # BTC/USDT -> X:BTCUSD
            if "/" in symbol or "_" in symbol:
                asset_type = "crypto"
                # Clean up the symbol
                base = symbol.replace("_USDT/USDT", "").replace("/USDT", "").replace("_USDT", "").replace("/", "")
                ticker = f"X:{base}USD"
            # Forex format: C:EURUSD
            elif symbol.startswith("C:"):
                asset_type = "forex"
            
            # Convert timeframe to Polygon format
            # 1m, 5m, 15m, 30m, 1h, 4h, 1d
            if timeframe.endswith('m'):
                multiplier = int(timeframe[:-1])
                timespan = 'minute'
            elif timeframe.endswith('h'):
                multiplier = int(timeframe[:-1])
                timespan = 'hour'
            elif timeframe.endswith('d'):
                multiplier = int(timeframe[:-1])
                timespan = 'day'
            else:
                logger.warning("Unknown timeframe format", timeframe=timeframe)
                multiplier = 1
                timespan = 'day'
            
            logger.info("Fetching from Polygon", 
                       original_symbol=symbol,
                       ticker=ticker,
                       asset_type=asset_type)
            
            # Fetch aggregates from flat files
            bars = await self.polygon_flatfiles.get_aggregates(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                start_date=start_time,
                end_date=end_time,
                asset_type=asset_type
            )
            
            # Convert to standard format
            result = []
            for bar in bars:
                result.append({
                    "timestamp": bar['timestamp'],
                    "open": bar['open'],
                    "high": bar['high'],
                    "low": bar['low'],
                    "close": bar['close'],
                    "volume": bar['volume']
                })
            
            logger.info("Fetched Polygon flat files OHLCV",
                       symbol=symbol,
                       bars=len(result))
            
            return result
            
        except Exception as e:
            logger.error("Failed to fetch Polygon flat files", error=str(e))
            return []
    
    async def _fetch_ccxt_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        exchange: str
    ) -> List[Dict[str, Any]]:
        """Fallback to CCXT for live data"""
        
        try:
            normalized_symbol = self._normalize_symbol(symbol)
            
            exchange_obj = self.exchanges.get(exchange.lower())
            if not exchange_obj:
                logger.warning("Exchange not supported, defaulting to Binance", exchange=exchange)
                exchange_obj = self.exchanges['binance']
            
            ccxt_timeframe = self._convert_timeframe(timeframe)
            since = int(start_time.timestamp() * 1000) if start_time else None
            
            ohlcv = exchange_obj.fetch_ohlcv(
                normalized_symbol,
                timeframe=ccxt_timeframe,
                since=since,
                limit=1000
            )
            
            if end_time:
                end_timestamp = int(end_time.timestamp() * 1000)
                ohlcv = [candle for candle in ohlcv if candle[0] <= end_timestamp]
            
            result = []
            for candle in ohlcv:
                result.append({
                    "timestamp": datetime.fromtimestamp(candle[0] / 1000).isoformat(),
                    "open": candle[1],
                    "high": candle[2],
                    "low": candle[3],
                    "close": candle[4],
                    "volume": candle[5]
                })
            
            logger.info("Fetched CCXT OHLCV data", 
                       symbol=symbol, 
                       candles=len(result))
            
            return result
            
        except Exception as e:
            logger.error("Failed to fetch CCXT OHLCV", error=str(e))
            return []
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for CCXT"""
        # Common formats: BTCUSDT, BTC-USDT, BTC/USDT
        # CCXT uses BTC/USDT format
        
        symbol = symbol.upper().replace('-', '/').replace('_', '/')
        
        # If no separator, try to split common pairs
        if '/' not in symbol:
            # Common quote currencies
            for quote in ['USDT', 'USD', 'BUSD', 'EUR', 'BTC', 'ETH']:
                if symbol.endswith(quote):
                    base = symbol[:-len(quote)]
                    return f"{base}/{quote}"
        
        return symbol
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to CCXT format"""
        # Map common formats
        timeframe_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1w'
        }
        
        return timeframe_map.get(timeframe.lower(), '5m')

