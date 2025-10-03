"""
Binance Vision Service - Downloads historical crypto data from Binance's public data
https://data.binance.vision/
"""

import structlog
import requests
import zipfile
import io
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path

logger = structlog.get_logger()


class BinanceVisionService:
    """
    Service to fetch historical crypto OHLCV data from Binance Vision public datasets
    
    Data available:
    - Klines (candlestick data) - OHLCV
    - AggTrades (aggregated trades)
    
    Format:
    - Daily: Single day ZIP files
    - Monthly: Full month ZIP files
    """
    
    BASE_URL = "https://data.binance.vision/data"
    
    def __init__(self):
        self.cache_dir = Path("data/binance_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: datetime,
        market_type: str = "spot"
    ) -> List[Dict[str, Any]]:
        """
        Get kline/candlestick data for a symbol
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT or BTC/USDT or BTC_USDT/USDT)
            interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            start_time: Start datetime
            end_time: End datetime
            market_type: 'spot' or 'futures' (um = USDT-M futures)
        
        Returns:
            List of kline data with OHLCV
        """
        
        try:
            # Clean symbol format - handle various formats
            # BTC/USDT -> BTCUSDT
            # BTC_USDT/USDT -> BTCUSDT
            # DOGE_USDT/USDT -> DOGEUSDT
            symbol = symbol.upper().replace('/', '').replace('_', '')
            
            # Remove duplicate USDT if present (e.g., USDTUSDT -> USDT)
            if symbol.endswith('USDTUSDT'):
                symbol = symbol[:-4]  # Remove the extra USDT
            
            # Auto-detect market type: if symbol ends with USDT and not a stablecoin, it's likely futures
            if symbol.endswith('USDT') and symbol != 'USDT':
                market_type = "futures/um"  # USDT-M Perpetual futures
            
            # Determine if we need daily or monthly data based on time span and current date
            time_span = (end_time - start_time).days
            current_date = datetime.now().date()
            
            all_klines = []
            
            # Check if any month in the range is incomplete (current month)
            start_month = start_time.replace(day=1).date()
            end_month = end_time.replace(day=1).date()
            
            # If time span is short OR if current month is in range, use daily files
            if time_span <= 31 or current_date.month == start_time.month and current_date.year == start_time.year or current_date.month == end_time.month and current_date.year == end_time.year:
                # Use daily files
                current_date = start_time.date()
                end_date = end_time.date()
                
                while current_date <= end_date:
                    daily_data = await self._fetch_daily_klines(
                        symbol, interval, current_date, market_type
                    )
                    all_klines.extend(daily_data)
                    current_date += timedelta(days=1)
            else:
                # Use monthly files for efficiency (only for completed months)
                current_month = start_time.replace(day=1)
                end_month = end_time.replace(day=1)
                
                while current_month <= end_month:
                    # Skip current month - use daily files for it
                    if current_month.month == current_date.month and current_month.year == current_date.year:
                        # Fetch daily files for current month
                        month_start = current_month
                        month_end = end_time if end_time.month == current_month.month and end_time.year == current_month.year else (current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        
                        daily_date = month_start.date()
                        while daily_date <= month_end.date():
                            daily_data = await self._fetch_daily_klines(
                                symbol, interval, daily_date, market_type
                            )
                            all_klines.extend(daily_data)
                            daily_date += timedelta(days=1)
                    else:
                        # Use monthly file for completed months
                        monthly_data = await self._fetch_monthly_klines(
                            symbol, interval, current_month, market_type
                        )
                        all_klines.extend(monthly_data)
                    
                    # Move to next month
                    if current_month.month == 12:
                        current_month = current_month.replace(year=current_month.year + 1, month=1)
                    else:
                        current_month = current_month.replace(month=current_month.month + 1)
            
            # Filter to exact time range
            filtered_klines = [
                k for k in all_klines
                if start_time <= datetime.fromtimestamp(k['open_time'] / 1000) <= end_time
            ]
            
            # Check for data gaps and attempt to fill them
            if len(filtered_klines) == 0:
                logger.warning("No klines found for time range, checking for missing days", 
                             symbol=symbol, start_time=start_time, end_time=end_time)
                # Try fetching individual days that might have been missed
                current_date = start_time.date()
                end_date = end_time.date()
                while current_date <= end_date:
                    daily_data = await self._fetch_daily_klines(symbol, interval, current_date, "spot")
                    if daily_data:
                        filtered_klines.extend([
                            k for k in daily_data
                            if start_time <= datetime.fromtimestamp(k['open_time'] / 1000) <= end_time
                        ])
                    current_date += timedelta(days=1)
            
            logger.info("Fetched Binance klines",
                       symbol=symbol,
                       interval=interval,
                       count=len(filtered_klines))
            
            return filtered_klines
            
        except Exception as e:
            logger.error("Failed to fetch Binance klines", error=str(e), symbol=symbol)
            return []

    async def get_aggtrades(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetch aggregated trades data from Binance Vision
        
        Args:
            symbol: Trading pair (e.g., BTCUSDT, DOGEUSDT)
            start_time: Start datetime
            end_time: End datetime
            
        Returns:
            List of aggregated trade records
        """
        try:
            # Clean symbol format
            symbol = symbol.upper().replace('/', '').replace('_', '')
            if symbol.endswith('USDTUSDT'):
                symbol = symbol[:-4]
            
            # Auto-detect market type
            market_type = "futures/um" if symbol.endswith('USDT') and symbol != 'USDT' else "spot"
            
            # Determine if we need daily or monthly data
            time_span = (end_time - start_time).days
            current_date = datetime.now().date()
            
            all_aggtrades = []
            
            # Check if any month in the range is incomplete (current month)
            if time_span <= 31 or current_date.month == start_time.month and current_date.year == start_time.year or current_date.month == end_time.month and current_date.year == end_time.year:
                # Use daily files
                current_date = start_time.date()
                end_date = end_time.date()
                
                while current_date <= end_date:
                    daily_data = await self._fetch_daily_aggtrades(symbol, current_date, market_type)
                    all_aggtrades.extend(daily_data)
                    current_date += timedelta(days=1)
            else:
                # Use monthly files for efficiency (only for completed months)
                current_month = start_time.replace(day=1)
                end_month = end_time.replace(day=1)
                
                while current_month <= end_month:
                    # Skip current month - use daily files for it
                    if current_month.month == current_date.month and current_month.year == current_date.year:
                        # Fetch daily files for current month
                        month_start = current_month
                        month_end = end_time if end_time.month == current_month.month and end_time.year == current_month.year else (current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                        
                        daily_date = month_start.date()
                        while daily_date <= month_end.date():
                            daily_data = await self._fetch_daily_aggtrades(symbol, daily_date, market_type)
                            all_aggtrades.extend(daily_data)
                            daily_date += timedelta(days=1)
                    else:
                        # Use monthly file for completed months
                        monthly_data = await self._fetch_monthly_aggtrades(symbol, current_month, market_type)
                        all_aggtrades.extend(monthly_data)
                    
                    # Move to next month
                    if current_month.month == 12:
                        current_month = current_month.replace(year=current_month.year + 1, month=1)
                    else:
                        current_month = current_month.replace(month=current_month.month + 1)
            
            # Filter to exact time range
            filtered_aggtrades = [
                a for a in all_aggtrades
                if start_time <= datetime.fromtimestamp(a['timestamp'] / 1000) <= end_time
            ]
            
            logger.info("Fetched Binance aggtrades",
                       symbol=symbol,
                       count=len(filtered_aggtrades))
            
            return filtered_aggtrades
            
        except Exception as e:
            logger.error("Failed to fetch Binance aggtrades", error=str(e), symbol=symbol)
            return []
    
    async def _fetch_daily_klines(
        self,
        symbol: str,
        interval: str,
        date: Any,
        market_type: str
    ) -> List[Dict[str, Any]]:
        """Fetch klines for a specific day"""
        
        try:
            # Format: data/spot/daily/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01-01.zip
            # Use manual formatting to avoid Windows strftime issues
            date_str = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
            
            if market_type == "futures/um":
                url = f"{self.BASE_URL}/futures/um/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{date_str}.zip"
            else:
                url = f"{self.BASE_URL}/spot/daily/klines/{symbol}/{interval}/{symbol}-{interval}-{date_str}.zip"
            
            # Check cache first
            cache_file = self.cache_dir / f"{symbol}_{interval}_{date_str}.csv"
            if cache_file.exists():
                return self._parse_klines_csv(cache_file)
            
            # Download and extract ZIP
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning("Daily klines not available", url=url, status=response.status_code)
                # Try alternative market type if this failed
                if market_type == "futures/um":
                    logger.info("Retrying with spot market", symbol=symbol, date=date_str)
                    return await self._fetch_daily_klines(symbol, interval, date, "spot")
                return []
            
            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = f"{symbol}-{interval}-{date_str}.csv"
                with z.open(csv_filename) as csv_file:
                    # Save to cache
                    cache_file.write_bytes(csv_file.read())
            
            return self._parse_klines_csv(cache_file)
            
        except Exception as e:
            import traceback
            logger.error("Failed to fetch daily klines", 
                        error=str(e), 
                        symbol=symbol, 
                        date=date,
                        date_str=locals().get('date_str', 'N/A'),
                        traceback=traceback.format_exc())
            return []
    
    async def _fetch_monthly_klines(
        self,
        symbol: str,
        interval: str,
        month: datetime,
        market_type: str
    ) -> List[Dict[str, Any]]:
        """Fetch klines for a full month"""
        
        try:
            # Format: data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip
            # Use manual formatting to avoid Windows strftime issues
            month_str = f"{month.year:04d}-{month.month:02d}"
            
            if market_type == "futures/um":
                url = f"{self.BASE_URL}/futures/um/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{month_str}.zip"
            else:
                url = f"{self.BASE_URL}/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{month_str}.zip"
            
            # Check cache
            cache_file = self.cache_dir / f"{symbol}_{interval}_{month_str}.csv"
            if cache_file.exists():
                return self._parse_klines_csv(cache_file)
            
            # Download and extract
            response = requests.get(url, timeout=60)
            
            if response.status_code != 200:
                logger.warning("Monthly klines not available", url=url, status=response.status_code)
                # Try alternative market type if this failed
                if market_type == "futures/um":
                    logger.info("Retrying monthly with spot market", symbol=symbol, month=month_str)
                    return await self._fetch_monthly_klines(symbol, interval, month, "spot")
                return []
            
            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = f"{symbol}-{interval}-{month_str}.csv"
                with z.open(csv_filename) as csv_file:
                    cache_file.write_bytes(csv_file.read())
            
            return self._parse_klines_csv(cache_file)
            
        except Exception as e:
            logger.error("Failed to fetch monthly klines", error=str(e), symbol=symbol, month=month)
            return []

    async def _fetch_daily_aggtrades(
        self,
        symbol: str,
        date: Any,
        market_type: str
    ) -> List[Dict[str, Any]]:
        """Fetch aggtrades for a specific day"""
        
        try:
            # Format: data/spot/daily/aggtrades/BTCUSDT/BTCUSDT-aggTrades-2024-01-01.zip
            # Use manual formatting to avoid Windows strftime issues
            date_str = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
            
            if market_type == "futures":
                url = f"{self.BASE_URL}/futures/um/daily/aggtrades/{symbol}/{symbol}-aggTrades-{date_str}.zip"
            else:
                url = f"{self.BASE_URL}/spot/daily/aggtrades/{symbol}/{symbol}-aggTrades-{date_str}.zip"
            
            # Check cache first
            cache_file = self.cache_dir / f"{symbol}_aggtrades_{date_str}.csv"
            if cache_file.exists():
                return self._parse_aggtrades_csv(cache_file)
            
            # Download and extract ZIP
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning("Daily aggtrades not available", url=url, status=response.status_code)
                # Try alternative market type if this failed
                if market_type == "futures/um":
                    logger.info("Retrying aggtrades with spot market", symbol=symbol, date=date_str)
                    return await self._fetch_daily_aggtrades(symbol, date, "spot")
                return []
            
            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = f"{symbol}-aggTrades-{date_str}.csv"
                with z.open(csv_filename) as csv_file:
                    # Save to cache
                    cache_file.write_bytes(csv_file.read())
            
            return self._parse_aggtrades_csv(cache_file)
            
        except Exception as e:
            logger.error("Failed to fetch daily aggtrades", error=str(e), symbol=symbol, date=date)
            return []

    async def _fetch_monthly_aggtrades(
        self,
        symbol: str,
        month: datetime,
        market_type: str
    ) -> List[Dict[str, Any]]:
        """Fetch aggtrades for a full month"""
        
        try:
            # Format: data/spot/monthly/aggtrades/BTCUSDT/BTCUSDT-aggTrades-2024-01.zip
            # Use manual formatting to avoid Windows strftime issues
            month_str = f"{month.year:04d}-{month.month:02d}"
            
            if market_type == "futures":
                url = f"{self.BASE_URL}/futures/um/monthly/aggtrades/{symbol}/{symbol}-aggTrades-{month_str}.zip"
            else:
                url = f"{self.BASE_URL}/spot/monthly/aggtrades/{symbol}/{symbol}-aggTrades-{month_str}.zip"
            
            # Check cache
            cache_file = self.cache_dir / f"{symbol}_aggtrades_{month_str}.csv"
            if cache_file.exists():
                return self._parse_aggtrades_csv(cache_file)
            
            # Download and extract
            response = requests.get(url, timeout=60)
            
            if response.status_code != 200:
                logger.warning("Monthly aggtrades not available", url=url, status=response.status_code)
                # Try alternative market type if this failed
                if market_type == "futures":
                    logger.info("Retrying monthly aggtrades with spot market", symbol=symbol, month=month_str)
                    return await self._fetch_monthly_aggtrades(symbol, month, "spot")
                return []
            
            # Extract CSV from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = f"{symbol}-aggTrades-{month_str}.csv"
                with z.open(csv_filename) as csv_file:
                    cache_file.write_bytes(csv_file.read())
            
            return self._parse_aggtrades_csv(cache_file)
            
        except Exception as e:
            logger.error("Failed to fetch monthly aggtrades", error=str(e), symbol=symbol, month=month)
            return []
    
    def _parse_klines_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        Parse Binance klines CSV format
        
        Format:
        open_time, open, high, low, close, volume, close_time, quote_volume,
        count, taker_buy_volume, taker_buy_quote_volume, ignore
        """
        
        klines = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    # Skip header row if present
                    if i == 0 and row[0] == 'open_time':
                        continue
                    
                    if len(row) < 12:
                        continue
                    
                    try:
                        klines.append({
                            'open_time': int(row[0]),
                            'open': float(row[1]),
                            'high': float(row[2]),
                            'low': float(row[3]),
                            'close': float(row[4]),
                            'volume': float(row[5]),
                            'close_time': int(row[6]),
                            'quote_volume': float(row[7]),
                            'trades_count': int(row[8]),
                            'taker_buy_volume': float(row[9]),
                            'taker_buy_quote_volume': float(row[10])
                        })
                    except (ValueError, IndexError):
                        # Skip invalid rows
                        continue
            
            return klines
            
        except Exception as e:
            logger.error("Failed to parse klines CSV", error=str(e), path=str(csv_path))
            return []
    
    async def get_agg_trades(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        market_type: str = "spot"
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated trades data
        
        This provides more granular data than klines but is larger.
        Useful for analyzing exact entry/exit prices and volumes.
        """
        
        try:
            symbol = symbol.upper().replace('/', '')
            time_span = (end_time - start_time).days
            
            all_trades = []
            
            if time_span <= 31:
                # Use daily files
                current_date = start_time.date()
                end_date = end_time.date()
                
                while current_date <= end_date:
                    daily_trades = await self._fetch_daily_aggtrades(
                        symbol, current_date, market_type
                    )
                    all_trades.extend(daily_trades)
                    current_date += timedelta(days=1)
            else:
                # Monthly files not commonly used for aggTrades due to size
                # Stick with daily
                logger.warning("AggTrades requested for >31 days, using daily files", span=time_span)
                current_date = start_time.date()
                end_date = end_time.date()
                
                while current_date <= end_date:
                    daily_trades = await self._fetch_daily_aggtrades(
                        symbol, current_date, market_type
                    )
                    all_trades.extend(daily_trades)
                    current_date += timedelta(days=1)
            
            # Filter to exact time range
            filtered_trades = [
                t for t in all_trades
                if start_time.timestamp() * 1000 <= t['timestamp'] <= end_time.timestamp() * 1000
            ]
            
            logger.info("Fetched Binance aggTrades",
                       symbol=symbol,
                       count=len(filtered_trades))
            
            return filtered_trades
            
        except Exception as e:
            logger.error("Failed to fetch Binance aggTrades", error=str(e), symbol=symbol)
            return []
    
    async def _fetch_daily_aggtrades(
        self,
        symbol: str,
        date: Any,
        market_type: str
    ) -> List[Dict[str, Any]]:
        """Fetch aggTrades for a specific day"""
        
        try:
            # Use manual formatting to avoid Windows strftime issues
            date_str = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
            
            if market_type == "futures":
                url = f"{self.BASE_URL}/futures/um/daily/aggTrades/{symbol}/{symbol}-aggTrades-{date_str}.zip"
            else:
                url = f"{self.BASE_URL}/spot/daily/aggTrades/{symbol}/{symbol}-aggTrades-{date_str}.zip"
            
            cache_file = self.cache_dir / f"{symbol}_aggTrades_{date_str}.csv"
            if cache_file.exists():
                return self._parse_aggtrades_csv(cache_file)
            
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                return []
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                csv_filename = f"{symbol}-aggTrades-{date_str}.csv"
                with z.open(csv_filename) as csv_file:
                    cache_file.write_bytes(csv_file.read())
            
            return self._parse_aggtrades_csv(cache_file)
            
        except Exception as e:
            logger.error("Failed to fetch daily aggTrades", error=str(e))
            return []
    
    def _parse_aggtrades_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        Parse aggTrades CSV format
        
        Format: agg_trade_id, price, quantity, first_trade_id, last_trade_id,
                timestamp, is_buyer_maker, is_best_match
        """
        
        trades = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    # Skip header row if present
                    if i == 0 and (row[0] == 'agg_trade_id' or row[0] == 'id'):
                        continue
                    
                    if len(row) < 8:
                        continue
                    
                    try:
                        trades.append({
                            'agg_trade_id': int(row[0]),
                            'price': float(row[1]),
                            'quantity': float(row[2]),
                            'first_trade_id': int(row[3]),
                            'last_trade_id': int(row[4]),
                            'timestamp': int(row[5]),
                            'is_buyer_maker': row[6] == 'TRUE',
                            'is_best_match': row[7] == 'TRUE'
                        })
                    except (ValueError, IndexError):
                        # Skip invalid rows
                        continue
            
            return trades
            
        except Exception as e:
            logger.error("Failed to parse aggTrades CSV", error=str(e))
            return []

