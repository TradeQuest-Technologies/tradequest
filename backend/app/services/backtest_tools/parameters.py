"""
Parameter Tools for Backtest Copilot
Tools for modifying backtest parameters and settings.
"""

from typing import Dict, Any, Optional
from pydantic import ValidationError

from app.schemas.backtest_copilot import ParameterUpdate
import structlog

logger = structlog.get_logger()


class ParameterTools:
    """Tools for modifying backtest parameters"""
    
    def __init__(self):
        self.pending_updates = {}  # Store pending parameter changes
    
    def update_leverage(self, run_id: str, leverage: float) -> Dict[str, Any]:
        """
        Update leverage setting.
        
        Args:
        - leverage: Value between 1-10x
        
        Returns dict with:
        - parameter: 'leverage'
        - old_value: previous value
        - new_value: new value
        - requires_approval: True
        """
        if not (1 <= leverage <= 10):
            raise ValueError("Leverage must be between 1 and 10")
        
        if run_id not in self.pending_updates:
            self.pending_updates[run_id] = {}
        
        old_value = self.pending_updates[run_id].get('leverage', 1)
        self.pending_updates[run_id]['leverage'] = leverage
        
        return {
            "parameter": "leverage",
            "old_value": old_value,
            "new_value": leverage,
            "requires_approval": True,
            "impact": f"All trade P&L will be multiplied by {leverage}x"
        }
    
    def update_position_sizing(self, run_id: str, position_size_percent: float) -> Dict[str, Any]:
        """
        Update position size percentage.
        
        Args:
        - position_size_percent: Value between 1-100%
        """
        if not (1 <= position_size_percent <= 100):
            raise ValueError("Position size must be between 1 and 100%")
        
        if run_id not in self.pending_updates:
            self.pending_updates[run_id] = {}
        
        old_value = self.pending_updates[run_id].get('position_size_percent', 100)
        self.pending_updates[run_id]['position_size_percent'] = position_size_percent
        
        return {
            "parameter": "position_size_percent",
            "old_value": old_value,
            "new_value": position_size_percent,
            "requires_approval": True,
            "impact": f"Trade sizes will be scaled to {position_size_percent}% of original"
        }
    
    def update_stop_loss(
        self,
        run_id: str,
        stop_loss_percent: Optional[float]
    ) -> Dict[str, Any]:
        """
        Set/modify stop loss percentage.
        
        Args:
        - stop_loss_percent: Value between 0-100%, or None to disable
        """
        if stop_loss_percent is not None and not (0 <= stop_loss_percent <= 100):
            raise ValueError("Stop loss must be between 0 and 100%")
        
        if run_id not in self.pending_updates:
            self.pending_updates[run_id] = {}
        
        old_value = self.pending_updates[run_id].get('stop_loss_percent')
        self.pending_updates[run_id]['stop_loss_percent'] = stop_loss_percent
        
        impact = "Stop loss disabled" if stop_loss_percent is None else \
                 f"Losses will be capped at {stop_loss_percent}%"
        
        return {
            "parameter": "stop_loss_percent",
            "old_value": old_value,
            "new_value": stop_loss_percent,
            "requires_approval": True,
            "impact": impact
        }
    
    def update_take_profit(
        self,
        run_id: str,
        take_profit_percent: Optional[float]
    ) -> Dict[str, Any]:
        """
        Set/modify take profit percentage.
        
        Args:
        - take_profit_percent: Value between 0-100%, or None to disable
        """
        if take_profit_percent is not None and not (0 <= take_profit_percent <= 100):
            raise ValueError("Take profit must be between 0 and 100%")
        
        if run_id not in self.pending_updates:
            self.pending_updates[run_id] = {}
        
        old_value = self.pending_updates[run_id].get('take_profit_percent')
        self.pending_updates[run_id]['take_profit_percent'] = take_profit_percent
        
        impact = "Take profit disabled" if take_profit_percent is None else \
                 f"Profits will be capped at {take_profit_percent}%"
        
        return {
            "parameter": "take_profit_percent",
            "old_value": old_value,
            "new_value": take_profit_percent,
            "requires_approval": True,
            "impact": impact
        }
    
    def update_holding_time(
        self,
        run_id: str,
        min_holding_hours: Optional[float] = None,
        max_holding_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Set min/max holding time filters.
        
        Args:
        - min_holding_hours: Minimum hours to hold, or None
        - max_holding_hours: Maximum hours to hold, or None
        """
        if min_holding_hours is not None and min_holding_hours < 0:
            raise ValueError("Min holding hours cannot be negative")
        
        if max_holding_hours is not None and max_holding_hours < 0:
            raise ValueError("Max holding hours cannot be negative")
        
        if (min_holding_hours is not None and max_holding_hours is not None and
            min_holding_hours > max_holding_hours):
            raise ValueError("Min holding hours cannot exceed max holding hours")
        
        if run_id not in self.pending_updates:
            self.pending_updates[run_id] = {}
        
        self.pending_updates[run_id]['min_holding_hours'] = min_holding_hours
        self.pending_updates[run_id]['max_holding_hours'] = max_holding_hours
        
        impact_parts = []
        if min_holding_hours is not None:
            impact_parts.append(f"Trades shorter than {min_holding_hours}h will be filtered out")
        if max_holding_hours is not None:
            impact_parts.append(f"Trades longer than {max_holding_hours}h will be filtered out")
        
        return {
            "parameter": "holding_time",
            "old_value": {
                "min": self.pending_updates[run_id].get('min_holding_hours'),
                "max": self.pending_updates[run_id].get('max_holding_hours')
            },
            "new_value": {
                "min": min_holding_hours,
                "max": max_holding_hours
            },
            "requires_approval": True,
            "impact": ". ".join(impact_parts) if impact_parts else "No holding time filters"
        }
    
    def update_trade_filters(
        self,
        run_id: str,
        filter_losers: Optional[bool] = None,
        filter_winners: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Enable/disable winner/loser filters.
        
        Args:
        - filter_losers: If True, exclude losing trades
        - filter_winners: If True, exclude winning trades
        """
        if run_id not in self.pending_updates:
            self.pending_updates[run_id] = {}
        
        if filter_losers is not None:
            self.pending_updates[run_id]['filter_losers'] = filter_losers
        if filter_winners is not None:
            self.pending_updates[run_id]['filter_winners'] = filter_winners
        
        impact_parts = []
        if filter_losers:
            impact_parts.append("Losing trades will be excluded")
        if filter_winners:
            impact_parts.append("Winning trades will be excluded")
        
        return {
            "parameter": "trade_filters",
            "old_value": {
                "filter_losers": self.pending_updates[run_id].get('filter_losers', False),
                "filter_winners": self.pending_updates[run_id].get('filter_winners', False)
            },
            "new_value": {
                "filter_losers": filter_losers,
                "filter_winners": filter_winners
            },
            "requires_approval": True,
            "impact": ". ".join(impact_parts) if impact_parts else "No trade filters applied"
        }
    
    def batch_update_parameters(
        self,
        run_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update multiple parameters at once.
        
        Args:
        - updates: Dict with parameter names and values
        
        Returns summary of all changes.
        """
        results = []
        
        if 'leverage' in updates:
            results.append(self.update_leverage(run_id, updates['leverage']))
        
        if 'position_size_percent' in updates:
            results.append(self.update_position_sizing(run_id, updates['position_size_percent']))
        
        if 'stop_loss_percent' in updates:
            results.append(self.update_stop_loss(run_id, updates.get('stop_loss_percent')))
        
        if 'take_profit_percent' in updates:
            results.append(self.update_take_profit(run_id, updates.get('take_profit_percent')))
        
        if 'min_holding_hours' in updates or 'max_holding_hours' in updates:
            results.append(self.update_holding_time(
                run_id,
                updates.get('min_holding_hours'),
                updates.get('max_holding_hours')
            ))
        
        if 'filter_losers' in updates or 'filter_winners' in updates:
            results.append(self.update_trade_filters(
                run_id,
                updates.get('filter_losers'),
                updates.get('filter_winners')
            ))
        
        return {
            "updates": results,
            "requires_approval": True,
            "total_parameters_updated": len(results)
        }
    
    def get_pending_updates(self, run_id: str) -> Dict[str, Any]:
        """Get all pending parameter updates for a run"""
        return self.pending_updates.get(run_id, {})
    
    def clear_pending_updates(self, run_id: str):
        """Clear all pending updates for a run"""
        if run_id in self.pending_updates:
            del self.pending_updates[run_id]
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate a parameter set"""
        try:
            ParameterUpdate(**params)
            return True
        except ValidationError as e:
            logger.error(f"Parameter validation failed: {e}")
            return False

