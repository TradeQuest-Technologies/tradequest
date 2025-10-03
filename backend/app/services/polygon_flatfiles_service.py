"""
Polygon Flat Files Service - Access historical stock data from Polygon's S3 bucket
https://files.polygon.io/
"""

import structlog
import boto3
from botocore import UNSIGNED
from botocore.client import Config
import gzip
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = structlog.get_logger()


class PolygonFlatFilesService:
    """
    Service to fetch historical stock OHLCV data from Polygon's flat files
    
    Access via S3:
    - Endpoint: https://files.polygon.io
    - Bucket: flatfiles
    - Format: Parquet and CSV files
    
    Available data:
    - Trades
    - Quotes  
    - Aggregates (OHLCV bars)
    - Options data
    """
    
    S3_ENDPOINT = "https://files.polygon.io"
    BUCKET_NAME = "flatfiles"
    
    def __init__(self, access_key: str, secret_key: str):
        """
        Initialize with Polygon S3 credentials
        
        Args:
            access_key: Polygon S3 Access Key ID
            secret_key: Polygon S3 Secret Access Key
        """
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.S3_ENDPOINT,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4')
        )
        
        self.cache_dir = Path("data/polygon_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        start_date: datetime,
        end_date: datetime,
        asset_type: str = "stocks"
    ) -> List[Dict[str, Any]]:
        """
        Get aggregate bars (OHLCV) for any asset
        
        Args:
            ticker: Ticker symbol (e.g., AAPL for stocks, X:BTCUSD for crypto, C:EURUSD for forex)
            multiplier: Size of timespan (e.g., 1, 5, 15)
            timespan: Unit (minute, hour, day, week, month, quarter, year)
            start_date: Start date
            end_date: End date
            asset_type: 'stocks', 'crypto', 'forex', 'options', 'indices'
        
        Returns:
            List of OHLCV bars
        
        Examples:
            get_aggregates("AAPL", 5, "minute", start, end, "stocks")
            get_aggregates("X:BTCUSD", 1, "minute", start, end, "crypto")
            get_aggregates("C:EURUSD", 5, "minute", start, end, "forex")
        """
        
        try:
            ticker = ticker.upper()
            
            # Auto-detect asset type from ticker format if not explicitly provided
            if ticker.startswith("X:"):
                asset_type = "crypto"
            elif ticker.startswith("C:"):
                asset_type = "forex"
            elif ticker.startswith("O:"):
                asset_type = "options"
            elif ticker.startswith("I:"):
                asset_type = "indices"
            
            # Determine which files to download based on timespan
            if timespan in ['minute', 'hour']:
                # Minute/hour data stored by date
                return await self._fetch_intraday_aggregates(
                    ticker, multiplier, timespan, start_date, end_date, asset_type
                )
            else:
                # Daily+ data stored differently
                return await self._fetch_daily_aggregates(
                    ticker, start_date, end_date, asset_type
                )
            
        except Exception as e:
            logger.error("Failed to fetch Polygon aggregates", 
                        error=str(e), 
                        ticker=ticker,
                        asset_type=asset_type)
            return []
    
    async def _fetch_intraday_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: str,
        start_date: datetime,
        end_date: datetime,
        asset_type: str = "stocks"
    ) -> List[Dict[str, Any]]:
        """Fetch minute/hour level aggregates for any asset type"""
        
        all_bars = []
        current_date = start_date.date()
        end = end_date.date()
        
        # Map asset types to S3 path prefixes based on Polygon docs
        path_map = {
            "stocks": "us_stocks_sip/minute_aggs_v1",
            "crypto": "us_crypto_sip/minute_aggs_v1",
            "forex": "us_forex_sip/minute_aggs_v1",
            "options": "us_options_opra/minute_aggs_v1",
            "indices": "us_indices_sip/minute_aggs_v1"
        }
        
        path_prefix = path_map.get(asset_type, "us_stocks_sip/minute_aggs_v1")
        
        while current_date <= end:
            # Path format: {prefix}/{year}/{month}/{date}.csv.gz
            year = current_date.year
            month = f"{current_date.month:02d}"
            date_str = current_date.strftime("%Y-%m-%d")
            
            s3_key = f"{path_prefix}/{year}/{month}/{date_str}.csv.gz"
            
            try:
                # Check cache first
                cache_file = self.cache_dir / f"minute_aggs_{date_str}.csv"
                
                if not cache_file.exists():
                    # Download from S3
                    logger.info("Downloading Polygon flat file", key=s3_key)
                    
                    response = self.s3_client.get_object(
                        Bucket=self.BUCKET_NAME,
                        Key=s3_key
                    )
                    
                    # Decompress gzip
                    with gzip.GzipFile(fileobj=io.BytesIO(response['Body'].read())) as gz:
                        cache_file.write_bytes(gz.read())
                
                # Parse CSV and filter for our ticker
                day_bars = self._parse_minute_aggs_csv(cache_file, ticker, multiplier)
                all_bars.extend(day_bars)
                
            except self.s3_client.exceptions.NoSuchKey:
                logger.warning("Flat file not available", key=s3_key)
            except Exception as e:
                logger.error("Failed to fetch daily file", error=str(e), date=date_str)
            
            current_date += timedelta(days=1)
        
        # Filter to exact time range
        filtered_bars = [
            bar for bar in all_bars
            if start_date <= datetime.fromisoformat(bar['timestamp']) <= end_date
        ]
        
        logger.info("Fetched Polygon intraday aggregates", 
                   ticker=ticker,
                   bars=len(filtered_bars))
        
        return filtered_bars
    
    async def _fetch_daily_aggregates(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        asset_type: str = "stocks"
    ) -> List[Dict[str, Any]]:
        """Fetch daily aggregates for any asset type"""
        
        # Map asset types to S3 path prefixes
        path_map = {
            "stocks": "us_stocks_sip/day_aggs_v1",
            "crypto": "us_crypto_sip/day_aggs_v1",
            "forex": "us_forex_sip/day_aggs_v1",
            "options": "us_options_opra/day_aggs_v1",
            "indices": "us_indices_sip/day_aggs_v1"
        }
        
        path_prefix = path_map.get(asset_type, "us_stocks_sip/day_aggs_v1")
        all_bars = []
        
        current_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        
        while current_month <= end_month:
            year = current_month.year
            month = f"{current_month.month:02d}"
            month_str = current_month.strftime("%Y-%m")
            
            s3_key = f"{path_prefix}/{year}/{month}/{month_str}.csv.gz"
            
            try:
                cache_file = self.cache_dir / f"day_aggs_{month_str}.csv"
                
                if not cache_file.exists():
                    logger.info("Downloading Polygon daily flat file", key=s3_key)
                    
                    response = self.s3_client.get_object(
                        Bucket=self.BUCKET_NAME,
                        Key=s3_key
                    )
                    
                    with gzip.GzipFile(fileobj=io.BytesIO(response['Body'].read())) as gz:
                        cache_file.write_bytes(gz.read())
                
                month_bars = self._parse_day_aggs_csv(cache_file, ticker)
                all_bars.extend(month_bars)
                
            except self.s3_client.exceptions.NoSuchKey:
                logger.warning("Daily flat file not available", key=s3_key)
            except Exception as e:
                logger.error("Failed to fetch monthly file", error=str(e), month=month_str)
            
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # Filter to exact date range
        filtered_bars = [
            bar for bar in all_bars
            if start_date.date() <= datetime.fromisoformat(bar['timestamp']).date() <= end_date.date()
        ]
        
        logger.info("Fetched Polygon daily aggregates",
                   ticker=ticker,
                   bars=len(filtered_bars))
        
        return filtered_bars
    
    def _parse_minute_aggs_csv(
        self,
        csv_path: Path,
        ticker: str,
        multiplier: int
    ) -> List[Dict[str, Any]]:
        """
        Parse minute aggregates CSV
        
        Format:
        ticker,window_start,open,high,low,close,volume,vwap,transactions
        """
        
        bars = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Filter for our ticker
                    if row['ticker'].upper() != ticker.upper():
                        continue
                    
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(row['window_start'].replace('Z', '+00:00'))
                    
                    # Apply multiplier filter if needed
                    # (e.g., keep only every 5th minute for 5-minute bars)
                    if multiplier > 1 and timestamp.minute % multiplier != 0:
                        continue
                    
                    bars.append({
                        'timestamp': timestamp.isoformat(),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': int(row['volume']),
                        'vwap': float(row.get('vwap', 0)),
                        'transactions': int(row.get('transactions', 0))
                    })
            
            return bars
            
        except Exception as e:
            logger.error("Failed to parse minute aggs CSV", error=str(e))
            return []
    
    def _parse_day_aggs_csv(
        self,
        csv_path: Path,
        ticker: str
    ) -> List[Dict[str, Any]]:
        """
        Parse daily aggregates CSV
        
        Format:
        ticker,date,open,high,low,close,volume,vwap,transactions
        """
        
        bars = []
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    if row['ticker'].upper() != ticker.upper():
                        continue
                    
                    # Date format: YYYY-MM-DD
                    date_str = row['date']
                    timestamp = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    bars.append({
                        'timestamp': timestamp.isoformat(),
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': int(row['volume']),
                        'vwap': float(row.get('vwap', 0)),
                        'transactions': int(row.get('transactions', 0))
                    })
            
            return bars
            
        except Exception as e:
            logger.error("Failed to parse day aggs CSV", error=str(e))
            return []
    
    async def list_available_dates(self, ticker: str, year: int, month: int) -> List[str]:
        """List available dates for a ticker in a given month"""
        
        try:
            month_str = f"{month:02d}"
            prefix = f"us_stocks_sip/minute_aggs_v1/{year}/{month_str}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.BUCKET_NAME,
                Prefix=prefix
            )
            
            dates = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Extract date from filename
                    filename = key.split('/')[-1]
                    if filename.endswith('.csv.gz'):
                        date_str = filename.replace('.csv.gz', '')
                        dates.append(date_str)
            
            return sorted(dates)
            
        except Exception as e:
            logger.error("Failed to list available dates", error=str(e))
            return []

