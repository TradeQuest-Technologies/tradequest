"""
Position sizing blocks
"""

from typing import List
import pandas as pd
import numpy as np
from .base import BlockExecutor, BlockContext, BlockOutput


class FixedSizeBlock(BlockExecutor):
    """Fixed position size"""
    
    def _validate_params(self):
        self.params.setdefault("position_size", 1.0)
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.signals is None:
                return self._create_output(context, error="No signals in context")
            
            size = self.params["position_size"]
            
            # Apply fixed size to signals
            context.positions = context.signals * size
            
            return self._create_output(
                context,
                data={"position_size": size}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Fixed sizing error: {str(e)}")


class KellyBlock(BlockExecutor):
    """Kelly Criterion position sizing"""
    
    def _validate_params(self):
        self.params.setdefault("win_rate", 0.5)
        self.params.setdefault("win_loss_ratio", 1.5)
        self.params.setdefault("fraction", 0.5)  # Half-Kelly for safety
        self.params.setdefault("max_position", 1.0)
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.signals is None:
                return self._create_output(context, error="No signals in context")
            
            win_rate = self.params["win_rate"]
            wl_ratio = self.params["win_loss_ratio"]
            fraction = self.params["fraction"]
            max_pos = self.params["max_position"]
            
            # Kelly formula: f = (p * b - q) / b
            # where p = win rate, q = 1-p, b = win/loss ratio
            kelly_pct = (win_rate * wl_ratio - (1 - win_rate)) / wl_ratio
            kelly_pct = max(0, min(kelly_pct, 1.0))  # Clamp 0-100%
            
            # Apply fractional Kelly
            position_size = kelly_pct * fraction
            position_size = min(position_size, max_pos)
            
            # Apply to signals
            context.positions = context.signals * position_size
            
            return self._create_output(
                context,
                data={"kelly_pct": kelly_pct, "position_size": position_size}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Kelly sizing error: {str(e)}")


class VolTargetBlock(BlockExecutor):
    """Volatility-targeted position sizing"""
    
    def _validate_params(self):
        self.params.setdefault("target_vol", 0.15)  # 15% annualized
        self.params.setdefault("lookback", 30)
        self.params.setdefault("max_position", 2.0)
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.signals is None:
                return self._create_output(context, error="No signals in context")
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            target_vol = self.params["target_vol"]
            lookback = self.params["lookback"]
            max_pos = self.params["max_position"]
            
            # Calculate rolling volatility
            returns = context.ohlcv['close'].pct_change()
            rolling_vol = returns.rolling(window=lookback).std() * np.sqrt(252)  # Annualized
            
            # Position size = target_vol / realized_vol
            position_sizes = target_vol / rolling_vol
            position_sizes = position_sizes.fillna(1.0)
            position_sizes = np.clip(position_sizes, 0, max_pos)
            
            # Apply to signals
            context.positions = context.signals * position_sizes
            
            avg_vol = rolling_vol.mean()
            avg_size = position_sizes.mean()
            
            return self._create_output(
                context,
                data={
                    "target_vol": target_vol,
                    "avg_realized_vol": float(avg_vol),
                    "avg_position_size": float(avg_size)
                }
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Vol target sizing error: {str(e)}")

