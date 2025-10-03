"""
Risk management blocks
"""

from typing import List
import pandas as pd
import numpy as np
from .base import BlockExecutor, BlockContext, BlockOutput


class StopTakeBlock(BlockExecutor):
    """Stop loss and take profit levels"""
    
    def _validate_params(self):
        self.params.setdefault("stop_atr_mult", 2.0)
        self.params.setdefault("take_atr_mult", 3.0)
        self.params.setdefault("atr_feature", "atr")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.positions is None:
                return self._create_output(context, error="No positions in context")
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            stop_mult = self.params["stop_atr_mult"]
            take_mult = self.params["take_atr_mult"]
            atr_feat = self.params["atr_feature"]
            
            # Get ATR using integer indexing to avoid pandas string issues
            if context.features is not None:
                available_cols = list(context.features.columns)
                if atr_feat in available_cols:
                    col_idx = available_cols.index(atr_feat)
                    atr = context.features.iloc[:, col_idx]
                else:
                    atr = None
            else:
                atr = None
            
            if atr is None:
                # Calculate ATR if not available
                high = context.ohlcv['high']
                low = context.ohlcv['low']
                close = context.ohlcv['close']
                
                high_low = high - low
                high_close = np.abs(high - close.shift())
                low_close = np.abs(low - close.shift())
                
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                atr = true_range.rolling(window=14).mean()
            
            # Calculate stop and take levels
            close = context.ohlcv['close']
            
            stop_distance = atr * stop_mult
            take_distance = atr * take_mult
            
            # Store in context for order execution
            context.custom["stop_distance"] = stop_distance
            context.custom["take_distance"] = take_distance
            context.custom["has_stops"] = True
            
            return self._create_output(
                context,
                data={
                    "stop_atr_mult": stop_mult,
                    "take_atr_mult": take_mult,
                    "avg_stop_distance": float(stop_distance.mean()),
                    "avg_take_distance": float(take_distance.mean())
                }
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Stop/take error: {str(e)}")


class TrailingStopBlock(BlockExecutor):
    """Trailing stop loss"""
    
    def _validate_params(self):
        self.params.setdefault("trail_atr_mult", 2.0)
        self.params.setdefault("atr_feature", "atr")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.positions is None:
                return self._create_output(context, error="No positions in context")
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            trail_mult = self.params["trail_atr_mult"]
            atr_feat = self.params["atr_feature"]
            
            # Get ATR using integer indexing to avoid pandas string issues
            if context.features is not None:
                available_cols = list(context.features.columns)
                if atr_feat in available_cols:
                    col_idx = available_cols.index(atr_feat)
                    atr = context.features.iloc[:, col_idx]
                else:
                    atr = None
            else:
                atr = None
            
            if atr is None:
                # Calculate ATR if not available
                high = context.ohlcv['high']
                low = context.ohlcv['low']
                close = context.ohlcv['close']
                
                high_low = high - low
                high_close = np.abs(high - close.shift())
                low_close = np.abs(low - close.shift())
                
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                atr = true_range.rolling(window=14).mean()
            
            # Calculate trailing distance
            trail_distance = atr * trail_mult
            
            # Store in context
            context.custom["trail_distance"] = trail_distance
            context.custom["has_trailing"] = True
            
            return self._create_output(
                context,
                data={
                    "trail_atr_mult": trail_mult,
                    "avg_trail_distance": float(trail_distance.mean())
                }
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Trailing stop error: {str(e)}")


class TimeStopBlock(BlockExecutor):
    """Time-based stop (exit after N bars)"""
    
    def _validate_params(self):
        if "max_bars" not in self.params:
            raise ValueError("Missing required parameter: max_bars")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.positions is None:
                return self._create_output(context, error="No positions in context")
            
            max_bars = self.params["max_bars"]
            
            # Store in context
            context.custom["max_holding_bars"] = max_bars
            context.custom["has_time_stop"] = True
            
            return self._create_output(
                context,
                data={"max_bars": max_bars}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Time stop error: {str(e)}")

