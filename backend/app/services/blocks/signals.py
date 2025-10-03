"""
Signal blocks: Generate trading signals
"""

from typing import List
import pandas as pd
import numpy as np
from .base import BlockExecutor, BlockContext, BlockOutput


class RuleSignalBlock(BlockExecutor):
    """Generate signals from rule expression"""
    
    def _validate_params(self):
        if "rule" not in self.params:
            raise ValueError("Missing required parameter: rule")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            rule = self.params["rule"]
            
            # Parse rule (simple format: "rsi<30 -> long; rsi>70 -> short")
            signals = pd.Series(0, index=context.ohlcv.index)
            
            # Build evaluation context
            eval_ctx = {'pd': pd, 'np': np}
            
            # Add OHLCV columns
            for col in context.ohlcv.columns:
                eval_ctx[col] = context.ohlcv[col]
            
            # Add features using integer indexing
            if context.features is not None:
                for idx, col in enumerate(context.features.columns):
                    eval_ctx[col] = context.features.iloc[:, idx]
            
            # Parse and evaluate rules
            for rule_part in rule.split(";"):
                rule_part = rule_part.strip()
                if not rule_part:
                    continue
                
                if "->" not in rule_part:
                    continue
                
                condition, action = rule_part.split("->")
                condition = condition.strip()
                action = action.strip().lower()
                
                try:
                    # Evaluate condition
                    mask = eval(condition, {"__builtins__": {}}, eval_ctx)
                    
                    # Apply action
                    if action in ["long", "buy", "1"]:
                        signals[mask] = 1
                    elif action in ["short", "sell", "-1"]:
                        signals[mask] = -1
                    elif action in ["flat", "close", "0"]:
                        signals[mask] = 0
                        
                except Exception as e:
                    return self._create_output(context, error=f"Rule evaluation error: {str(e)}")
            
            context.signals = signals
            
            # Count signals
            long_signals = (signals == 1).sum()
            short_signals = (signals == -1).sum()
            
            return self._create_output(
                context,
                data={"long_signals": int(long_signals), "short_signals": int(short_signals)}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Rule signal error: {str(e)}")


class CrossoverBlock(BlockExecutor):
    """Generate signals from moving average crossovers"""
    
    def _validate_params(self):
        if "fast_feature" not in self.params or "slow_feature" not in self.params:
            raise ValueError("Missing required parameters: fast_feature, slow_feature")
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.features is None:
                return self._create_output(context, error="No features in context")
            
            fast_feat = self.params["fast_feature"]
            slow_feat = self.params["slow_feature"]
            
            # Use integer indexing to avoid pandas string issues
            available_cols = list(context.features.columns)
            
            if fast_feat not in available_cols:
                return self._create_output(context, error=f"Feature '{fast_feat}' not found")
            if slow_feat not in available_cols:
                return self._create_output(context, error=f"Feature '{slow_feat}' not found")
            
            fast_idx = available_cols.index(fast_feat)
            slow_idx = available_cols.index(slow_feat)
            
            fast = context.features.iloc[:, fast_idx]
            slow = context.features.iloc[:, slow_idx]
            
            # Generate crossover signals
            signals = pd.Series(0, index=fast.index)
            signals[fast > slow] = 1  # Fast above slow = long
            signals[fast < slow] = -1  # Fast below slow = short
            
            context.signals = signals
            
            # Count crossovers
            signal_changes = signals.diff().abs()
            crossovers = (signal_changes == 2).sum()
            
            return self._create_output(
                context,
                data={"crossovers": int(crossovers)}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Crossover error: {str(e)}")


class ThresholdBlock(BlockExecutor):
    """Generate signals from threshold conditions"""
    
    def _validate_params(self):
        if "feature" not in self.params:
            raise ValueError("Missing required parameter: feature")
        self.params.setdefault("upper_threshold", 70)
        self.params.setdefault("lower_threshold", 30)
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.features is None:
                return self._create_output(context, error="No features in context")
            
            # Get feature name and handle if it's a list
            feature_param = self.params["feature"]
            if isinstance(feature_param, list):
                feature_name = feature_param[0] if len(feature_param) > 0 else "rsi"
            else:
                feature_name = str(feature_param).strip()
            
            upper = self.params["upper_threshold"]
            lower = self.params["lower_threshold"]
            
            # Check if feature exists - convert columns to list to avoid pandas iterator issues
            available = list(context.features.columns)
            if feature_name not in available:
                return self._create_output(
                    context, 
                    error=f"Feature '{feature_name}' not found. Available: {available}"
                )
            
            # Get the feature column as a Series using index position to avoid any string issues
            try:
                col_idx = available.index(feature_name)
                feature = context.features.iloc[:, col_idx]
            except (ValueError, IndexError) as e:
                return self._create_output(
                    context, 
                    error=f"Failed to access feature column '{feature_name}': {str(e)}"
                )
            
            # Generate threshold signals
            signals = pd.Series(0, index=feature.index)
            signals[feature < lower] = 1  # Below lower = long (oversold)
            signals[feature > upper] = -1  # Above upper = short (overbought)
            
            context.signals = signals
            
            long_signals = (signals == 1).sum()
            short_signals = (signals == -1).sum()
            
            return self._create_output(
                context,
                data={"long_signals": int(long_signals), "short_signals": int(short_signals)}
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Threshold error: {str(e)}")


class MLSignalBlock(BlockExecutor):
    """Generate signals from ML model predictions"""
    
    def _validate_params(self):
        if "model_id" not in self.params:
            raise ValueError("Missing required parameter: model_id")
        self.params.setdefault("threshold", 0.5)
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.features is None:
                return self._create_output(context, error="No features in context")
            
            model_id = self.params["model_id"]
            threshold = self.params["threshold"]
            
            # Get model from context
            if model_id not in context.ml_models:
                return self._create_output(context, error=f"Model '{model_id}' not found in context")
            
            model = context.ml_models[model_id]
            
            # Get features for prediction using integer indexing
            feature_cols = model.get("features", [])
            available_cols = list(context.features.columns)
            if not all(col in available_cols for col in feature_cols):
                missing = [col for col in feature_cols if col not in available_cols]
                return self._create_output(context, error=f"Missing features for model: {missing}")
            
            # Get column indices and extract features
            col_indices = [available_cols.index(col) for col in feature_cols]
            X = context.features.iloc[:, col_indices].fillna(0)
            
            # Make predictions
            try:
                predictions = model["model"].predict_proba(X)[:, 1]  # Probability of positive class
            except:
                predictions = model["model"].predict(X)
            
            # Convert to signals
            signals = pd.Series(0, index=context.features.index)
            signals[predictions > threshold] = 1
            signals[predictions < (1 - threshold)] = -1
            
            context.signals = signals
            context.ml_predictions = pd.Series(predictions, index=context.features.index)
            
            long_signals = (signals == 1).sum()
            short_signals = (signals == -1).sum()
            
            return self._create_output(
                context,
                data={
                    "long_signals": int(long_signals),
                    "short_signals": int(short_signals),
                    "avg_prediction": float(predictions.mean())
                }
            )
            
        except Exception as e:
            return self._create_output(context, error=f"ML signal error: {str(e)}")

