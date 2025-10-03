"""
Base classes for block execution
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class BlockContext:
    """Execution context passed between blocks"""
    # Data
    ohlcv: Optional[pd.DataFrame] = None
    features: Optional[pd.DataFrame] = None
    signals: Optional[pd.Series] = None
    positions: Optional[pd.Series] = None
    orders: Optional[List[Dict[str, Any]]] = None
    
    # Metadata
    symbol: str = ""
    timeframe: str = ""
    initial_capital: float = 10000.0
    
    # State
    current_position: float = 0.0
    current_equity: float = 10000.0
    trades: List[Dict[str, Any]] = None
    
    # ML
    ml_models: Dict[str, Any] = None
    ml_predictions: Optional[pd.Series] = None
    
    # Custom data
    custom: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.trades is None:
            self.trades = []
        if self.ml_models is None:
            self.ml_models = {}
        if self.custom is None:
            self.custom = {}


@dataclass
class BlockOutput:
    """Output from block execution"""
    success: bool
    context: BlockContext
    data: Optional[Any] = None
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class BlockExecutor(ABC):
    """
    Base class for all block executors
    
    Each block type implements execute() to transform the context
    """
    
    def __init__(self, node_id: str, params: Dict[str, Any]):
        self.node_id = node_id
        self.params = params
        self._validate_params()
    
    def _validate_params(self):
        """Validate parameters (override in subclasses)"""
        pass
    
    @abstractmethod
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        """
        Execute block logic
        
        Args:
            context: Current execution context
            inputs: Outputs from upstream blocks
            
        Returns:
            BlockOutput with updated context
        """
        pass
    
    def _merge_contexts(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockContext:
        """Merge context from multiple inputs"""
        if not inputs:
            return context
        
        # Start with current context
        merged = context
        
        # Merge data from inputs
        for inp in inputs:
            if inp.success and inp.context:
                # Merge dataframes
                if inp.context.ohlcv is not None and merged.ohlcv is None:
                    merged.ohlcv = inp.context.ohlcv
                if inp.context.features is not None:
                    if merged.features is None:
                        merged.features = inp.context.features
                    else:
                        # Merge feature columns
                        merged.features = pd.concat([merged.features, inp.context.features], axis=1)
                
                # Update signals and positions
                if inp.context.signals is not None:
                    merged.signals = inp.context.signals
                if inp.context.positions is not None:
                    merged.positions = inp.context.positions
                
                # Merge orders and trades
                if inp.context.orders:
                    if merged.orders is None:
                        merged.orders = []
                    merged.orders.extend(inp.context.orders)
                if inp.context.trades:
                    merged.trades.extend(inp.context.trades)
                
                # Update state
                merged.current_position = inp.context.current_position
                merged.current_equity = inp.context.current_equity
                
                # Merge ML
                if inp.context.ml_models:
                    merged.ml_models.update(inp.context.ml_models)
                if inp.context.ml_predictions is not None:
                    merged.ml_predictions = inp.context.ml_predictions
                
                # Merge custom
                if inp.context.custom:
                    merged.custom.update(inp.context.custom)
        
        return merged
    
    def _create_output(self, context: BlockContext, data: Any = None, error: Optional[str] = None, warnings: List[str] = None) -> BlockOutput:
        """Helper to create BlockOutput"""
        return BlockOutput(
            success=error is None,
            context=context,
            data=data,
            error=error,
            warnings=warnings or []
        )

