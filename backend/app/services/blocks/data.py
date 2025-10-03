"""
Data blocks: Loading, resampling, splitting
"""

from typing import List
import pandas as pd
from .base import BlockExecutor, BlockContext, BlockOutput
from app.services.ohlcv_service import OHLCVService
from datetime import datetime


class DataLoaderBlock(BlockExecutor):
    """Load OHLCV data"""
    
    def _validate_params(self):
        required = ["symbol", "timeframe", "start_date", "end_date"]
        for param in required:
            if param not in self.params:
                raise ValueError(f"Missing required parameter: {param}")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            symbol = self.params["symbol"]
            timeframe = self.params["timeframe"]
            start_date = self.params["start_date"]
            end_date = self.params["end_date"]
            
            # Convert string dates to datetime if needed
            from datetime import datetime
            if isinstance(start_date, str):
                # Handle various date formats
                try:
                    start_date = datetime.fromisoformat(start_date)
                except ValueError:
                    # Try parsing as just a date
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
            
            if isinstance(end_date, str):
                try:
                    end_date = datetime.fromisoformat(end_date)
                except ValueError:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Ensure we have datetime objects
            if not isinstance(start_date, datetime):
                return self._create_output(context, error=f"Invalid start_date type: {type(start_date)}")
            if not isinstance(end_date, datetime):
                return self._create_output(context, error=f"Invalid end_date type: {type(end_date)}")
            
            # Fetch data
            ohlcv_service = OHLCVService()
            data = await ohlcv_service.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_date,
                end_time=end_date
            )
            
            if not data:
                return self._create_output(context, error="No data returned from OHLCV service")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Handle timestamp conversion - could be ms, datetime string, or already datetime
            if 'timestamp' in df.columns:
                try:
                    # Try as milliseconds first (most common for crypto)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                except (ValueError, TypeError):
                    # Fall back to general datetime parsing
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            df = df.set_index('timestamp')
            
            # Ensure required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    return self._create_output(context, error=f"Missing required column: {col}")
            
            # Update context
            context.ohlcv = df
            context.symbol = symbol
            context.timeframe = timeframe
            
            return self._create_output(
                context,
                data={"rows": len(df), "start": str(df.index[0]), "end": str(df.index[-1])}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Data loader error: {str(e)}")


class DataResamplerBlock(BlockExecutor):
    """Resample OHLCV to different timeframe"""
    
    def _validate_params(self):
        if "target_timeframe" not in self.params:
            raise ValueError("Missing required parameter: target_timeframe")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            target_tf = self.params["target_timeframe"]
            
            # Map timeframe string to pandas offset
            tf_map = {
                "1m": "1T", "5m": "5T", "15m": "15T", "30m": "30T",
                "1h": "1H", "4h": "4H", "1d": "1D", "1w": "1W"
            }
            
            if target_tf not in tf_map:
                return self._create_output(context, error=f"Invalid timeframe: {target_tf}")
            
            offset = tf_map[target_tf]
            
            # Resample
            resampled = context.ohlcv.resample(offset).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            context.ohlcv = resampled
            context.timeframe = target_tf
            
            return self._create_output(
                context,
                data={"rows": len(resampled), "timeframe": target_tf}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Resampler error: {str(e)}")


class DataSplitterBlock(BlockExecutor):
    """Split data into train/test for walk-forward"""
    
    def _validate_params(self):
        if "split_date" not in self.params and "split_ratio" not in self.params:
            raise ValueError("Need either split_date or split_ratio")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            df = context.ohlcv
            
            if "split_date" in self.params:
                split_date = pd.to_datetime(self.params["split_date"])
                train_df = df[df.index < split_date]
                test_df = df[df.index >= split_date]
            else:
                split_ratio = self.params["split_ratio"]
                split_idx = int(len(df) * split_ratio)
                train_df = df.iloc[:split_idx]
                test_df = df.iloc[split_idx:]
            
            # Store in custom context
            context.custom["train_data"] = train_df
            context.custom["test_data"] = test_df
            context.custom["is_split"] = True
            
            return self._create_output(
                context,
                data={
                    "train_rows": len(train_df),
                    "test_rows": len(test_df),
                    "train_start": str(train_df.index[0]) if len(train_df) > 0 else None,
                    "train_end": str(train_df.index[-1]) if len(train_df) > 0 else None,
                    "test_start": str(test_df.index[0]) if len(test_df) > 0 else None,
                    "test_end": str(test_df.index[-1]) if len(test_df) > 0 else None
                }
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Splitter error: {str(e)}")

