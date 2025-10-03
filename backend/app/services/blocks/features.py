"""
Feature blocks: Technical indicators and feature engineering
"""

from typing import List
import pandas as pd
import numpy as np
from .base import BlockExecutor, BlockContext, BlockOutput


class RSIBlock(BlockExecutor):
    """Calculate RSI indicator"""
    
    def _validate_params(self):
        self.params.setdefault("period", 14)
        self.params.setdefault("output_name", "rsi")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            period = self.params["period"]
            output_name = self.params["output_name"]
            
            # Calculate RSI
            delta = context.ohlcv['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Add to features
            if context.features is None:
                context.features = pd.DataFrame(index=context.ohlcv.index)
            
            context.features[output_name] = rsi
            
            return self._create_output(
                context,
                data={"feature": output_name, "mean": float(rsi.mean()), "std": float(rsi.std())}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"RSI error: {str(e)}")


class MACDBlock(BlockExecutor):
    """Calculate MACD indicator"""
    
    def _validate_params(self):
        self.params.setdefault("fast_period", 12)
        self.params.setdefault("slow_period", 26)
        self.params.setdefault("signal_period", 9)
        self.params.setdefault("output_prefix", "macd")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            fast = self.params["fast_period"]
            slow = self.params["slow_period"]
            signal = self.params["signal_period"]
            prefix = self.params["output_prefix"]
            
            # Calculate MACD
            close = context.ohlcv['close']
            ema_fast = close.ewm(span=fast, adjust=False).mean()
            ema_slow = close.ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            
            # Add to features
            if context.features is None:
                context.features = pd.DataFrame(index=context.ohlcv.index)
            
            context.features[f"{prefix}_line"] = macd_line
            context.features[f"{prefix}_signal"] = signal_line
            context.features[f"{prefix}_hist"] = histogram
            
            return self._create_output(
                context,
                data={"features": [f"{prefix}_line", f"{prefix}_signal", f"{prefix}_hist"]}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"MACD error: {str(e)}")


class EMABlock(BlockExecutor):
    """Calculate Exponential Moving Average"""
    
    def _validate_params(self):
        if "period" not in self.params:
            raise ValueError("Missing required parameter: period")
        self.params.setdefault("source", "close")
        self.params.setdefault("output_name", f"ema_{self.params['period']}")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            period = self.params["period"]
            source = self.params["source"]
            output_name = self.params["output_name"]
            
            if source not in context.ohlcv.columns:
                return self._create_output(context, error=f"Source column '{source}' not found")
            
            # Calculate EMA
            ema = context.ohlcv[source].ewm(span=period, adjust=False).mean()
            
            # Add to features
            if context.features is None:
                context.features = pd.DataFrame(index=context.ohlcv.index)
            
            context.features[output_name] = ema
            
            return self._create_output(
                context,
                data={"feature": output_name, "period": period}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"EMA error: {str(e)}")


class ATRBlock(BlockExecutor):
    """Calculate Average True Range"""
    
    def _validate_params(self):
        self.params.setdefault("period", 14)
        self.params.setdefault("output_name", "atr")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            period = self.params["period"]
            output_name = self.params["output_name"]
            
            # Calculate ATR
            high = context.ohlcv['high']
            low = context.ohlcv['low']
            close = context.ohlcv['close']
            
            high_low = high - low
            high_close = np.abs(high - close.shift())
            low_close = np.abs(low - close.shift())
            
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=period).mean()
            
            # Add to features
            if context.features is None:
                context.features = pd.DataFrame(index=context.ohlcv.index)
            
            context.features[output_name] = atr
            
            return self._create_output(
                context,
                data={"feature": output_name, "mean": float(atr.mean())}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"ATR error: {str(e)}")


class VWAPBlock(BlockExecutor):
    """Calculate Volume Weighted Average Price"""
    
    def _validate_params(self):
        self.params.setdefault("output_name", "vwap")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            output_name = self.params["output_name"]
            
            # Calculate VWAP
            typical_price = (context.ohlcv['high'] + context.ohlcv['low'] + context.ohlcv['close']) / 3
            vwap = (typical_price * context.ohlcv['volume']).cumsum() / context.ohlcv['volume'].cumsum()
            
            # Add to features
            if context.features is None:
                context.features = pd.DataFrame(index=context.ohlcv.index)
            
            context.features[output_name] = vwap
            
            return self._create_output(
                context,
                data={"feature": output_name}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"VWAP error: {str(e)}")


class CustomFeatureBlock(BlockExecutor):
    """Calculate custom feature from formula"""
    
    def _validate_params(self):
        if "formula" not in self.params:
            raise ValueError("Missing required parameter: formula")
        self.params.setdefault("output_name", "custom_feature")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            formula = self.params["formula"]
            output_name = self.params["output_name"]
            
            # Build evaluation context
            eval_ctx = {
                'df': context.ohlcv,
                'features': context.features,
                'pd': pd,
                'np': np
            }
            
            # Add OHLCV columns to context
            for col in context.ohlcv.columns:
                eval_ctx[col] = context.ohlcv[col]
            
            # Add existing features using integer indexing
            if context.features is not None:
                for idx, col in enumerate(context.features.columns):
                    eval_ctx[col] = context.features.iloc[:, idx]
            
            # Evaluate formula
            try:
                result = eval(formula, {"__builtins__": {}}, eval_ctx)
            except Exception as e:
                return self._create_output(context, error=f"Formula evaluation error: {str(e)}")
            
            # Add to features
            if context.features is None:
                context.features = pd.DataFrame(index=context.ohlcv.index)
            
            context.features[output_name] = result
            
            return self._create_output(
                context,
                data={"feature": output_name, "formula": formula}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Custom feature error: {str(e)}")

