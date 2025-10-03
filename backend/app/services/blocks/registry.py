"""
Block registry - maps block types to their executors
"""

from typing import Dict, Type
from .base import BlockExecutor
from .data import DataLoaderBlock, DataResamplerBlock, DataSplitterBlock
from .features import RSIBlock, MACDBlock, EMABlock, ATRBlock, VWAPBlock, CustomFeatureBlock
from .signals import RuleSignalBlock, CrossoverBlock, ThresholdBlock, MLSignalBlock
from .sizing import FixedSizeBlock, KellyBlock, VolTargetBlock
from .risk import StopTakeBlock, TrailingStopBlock, TimeStopBlock
from .execution import MarketOrderBlock, LimitOrderBlock


class BlockRegistry:
    """Registry of all available block types"""
    
    _registry: Dict[str, Type[BlockExecutor]] = {}
    
    @classmethod
    def register(cls, block_type: str, executor_class: Type[BlockExecutor]):
        """Register a block executor"""
        cls._registry[block_type] = executor_class
    
    @classmethod
    def get(cls, block_type: str) -> Type[BlockExecutor]:
        """Get executor class for block type"""
        if block_type not in cls._registry:
            raise ValueError(f"Unknown block type: {block_type}")
        return cls._registry[block_type]
    
    @classmethod
    def create(cls, block_type: str, node_id: str, params: Dict) -> BlockExecutor:
        """Create an executor instance"""
        executor_class = cls.get(block_type)
        return executor_class(node_id, params)
    
    @classmethod
    def list_blocks(cls) -> Dict[str, Dict]:
        """List all available blocks with metadata"""
        return {
            block_type: {
                "class": executor_class.__name__,
                "category": block_type.split(".")[0],
                "name": block_type.split(".")[1]
            }
            for block_type, executor_class in cls._registry.items()
        }


# Register all blocks
def _register_all():
    """Register all available blocks"""
    
    # Data blocks
    BlockRegistry.register("data.loader", DataLoaderBlock)
    BlockRegistry.register("data.resampler", DataResamplerBlock)
    BlockRegistry.register("data.splitter", DataSplitterBlock)
    
    # Feature blocks
    BlockRegistry.register("feature.rsi", RSIBlock)
    BlockRegistry.register("feature.macd", MACDBlock)
    BlockRegistry.register("feature.ema", EMABlock)
    BlockRegistry.register("feature.atr", ATRBlock)
    BlockRegistry.register("feature.vwap", VWAPBlock)
    BlockRegistry.register("feature.custom", CustomFeatureBlock)
    
    # Signal blocks
    BlockRegistry.register("signal.rule", RuleSignalBlock)
    BlockRegistry.register("signal.crossover", CrossoverBlock)
    BlockRegistry.register("signal.threshold", ThresholdBlock)
    BlockRegistry.register("signal.ml", MLSignalBlock)
    
    # Sizing blocks
    BlockRegistry.register("sizing.fixed", FixedSizeBlock)
    BlockRegistry.register("sizing.kelly", KellyBlock)
    BlockRegistry.register("sizing.vol_target", VolTargetBlock)
    
    # Risk blocks
    BlockRegistry.register("risk.stop_take", StopTakeBlock)
    BlockRegistry.register("risk.trailing", TrailingStopBlock)
    BlockRegistry.register("risk.time_stop", TimeStopBlock)
    
    # Execution blocks
    BlockRegistry.register("exec.market", MarketOrderBlock)
    BlockRegistry.register("exec.limit", LimitOrderBlock)


# Auto-register on import
_register_all()

