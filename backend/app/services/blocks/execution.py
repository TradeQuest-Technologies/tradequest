"""
Order execution blocks
"""

from typing import List
import pandas as pd
import numpy as np
from .base import BlockExecutor, BlockContext, BlockOutput


class MarketOrderBlock(BlockExecutor):
    """Execute market orders with slippage and fees"""
    
    def _validate_params(self):
        self.params.setdefault("slippage_bps", 5.0)
        self.params.setdefault("fee_bps", 2.0)
        self.params.setdefault("slippage_model", "fixed")  # fixed, atr_pct, volume_impact
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.positions is None:
                return self._create_output(context, error="No positions in context")
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            slippage_bps = self.params["slippage_bps"]
            fee_bps = self.params["fee_bps"]
            slippage_model = self.params["slippage_model"]
            
            # Generate orders from position changes
            position_changes = context.positions.diff().fillna(context.positions)
            
            orders = []
            trades = []
            
            current_position = 0.0
            entry_price = 0.0
            entry_time = None
            peak_pnl = 0.0
            trough_pnl = 0.0
            
            for idx, pos_change in position_changes.items():
                if pos_change == 0:
                    continue
                
                price = context.ohlcv.loc[idx, 'close']
                
                # Calculate slippage
                if slippage_model == "fixed":
                    slippage = price * (slippage_bps / 10000)
                elif slippage_model == "atr_pct":
                    atr = context.features.loc[idx, 'atr'] if 'atr' in context.features.columns else price * 0.01
                    slippage = atr * (slippage_bps / 100)
                else:
                    slippage = price * (slippage_bps / 10000)
                
                # Apply slippage direction
                if pos_change > 0:  # Buy
                    execution_price = price + slippage
                else:  # Sell
                    execution_price = price - slippage
                
                # Calculate fees
                notional = abs(pos_change) * execution_price
                fees = notional * (fee_bps / 10000)
                
                # Create order
                order = {
                    "timestamp": idx,
                    "side": "buy" if pos_change > 0 else "sell",
                    "quantity": abs(pos_change),
                    "price": price,
                    "execution_price": execution_price,
                    "slippage": abs(execution_price - price),
                    "fees": fees
                }
                orders.append(order)
                
                # Track trades (entry -> exit pairs)
                new_position = current_position + pos_change
                
                # Opening a position
                if current_position == 0 and new_position != 0:
                    entry_price = execution_price
                    entry_time = idx
                    current_position = new_position
                    peak_pnl = 0.0
                    trough_pnl = 0.0
                
                # Closing a position
                elif current_position != 0 and new_position == 0:
                    exit_price = execution_price
                    exit_time = idx
                    
                    # Calculate P&L
                    if current_position > 0:  # Long
                        pnl = (exit_price - entry_price) * abs(current_position)
                    else:  # Short
                        pnl = (entry_price - exit_price) * abs(current_position)
                    
                    # Subtract costs
                    total_fees = fees + order.get("entry_fees", 0)
                    pnl -= total_fees
                    
                    # Calculate holding time
                    holding_time = (exit_time - entry_time).total_seconds() / 3600  # hours
                    
                    trade = {
                        "entry_time": str(entry_time),
                        "exit_time": str(exit_time),
                        "side": "long" if current_position > 0 else "short",
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "quantity": abs(current_position),
                        "pnl": pnl,
                        "pnl_pct": (pnl / (entry_price * abs(current_position))) * 100,
                        "fees": total_fees,
                        "slippage": order["slippage"],
                        "mfe": peak_pnl,  # Maximum favorable excursion
                        "mae": trough_pnl,  # Maximum adverse excursion
                        "holding_time_hours": holding_time
                    }
                    trades.append(trade)
                    
                    current_position = 0.0
                    entry_price = 0.0
                    entry_time = None
                
                # Adjusting position
                else:
                    current_position = new_position
                
                # Track MFE/MAE for open positions
                if current_position != 0 and entry_price > 0:
                    if current_position > 0:  # Long
                        unrealized_pnl = (price - entry_price) * abs(current_position)
                    else:  # Short
                        unrealized_pnl = (entry_price - price) * abs(current_position)
                    
                    peak_pnl = max(peak_pnl, unrealized_pnl)
                    trough_pnl = min(trough_pnl, unrealized_pnl)
            
            # Store results
            context.orders = orders
            context.trades.extend(trades)
            
            total_fees = sum(o["fees"] for o in orders)
            total_slippage = sum(o["slippage"] * o["quantity"] for o in orders)
            
            return self._create_output(
                context,
                data={
                    "total_orders": len(orders),
                    "total_trades": len(trades),
                    "total_fees": total_fees,
                    "total_slippage": total_slippage
                }
            )
            
        except Exception as e:
            return self._create_output(context, error=f"Market order error: {str(e)}")


class LimitOrderBlock(BlockExecutor):
    """Execute limit orders (simplified)"""
    
    def _validate_params(self):
        self.params.setdefault("limit_offset_bps", 10.0)
        self.params.setdefault("fee_bps", 2.0)
        self.params.setdefault("fill_probability", 0.7)
    
    async def execute(self, context: BlockContext, inputs: List[BlockOutput]) -> BlockOutput:
        try:
            context = self._merge_contexts(context, inputs)
            
            if context.positions is None:
                return self._create_output(context, error="No positions in context")
            if context.ohlcv is None:
                return self._create_output(context, error="No OHLCV data in context")
            
            # Simplified limit order execution
            # In reality, this would check if limit price was hit
            # For now, just add limit offset to reduce slippage
            
            offset_bps = self.params["limit_offset_bps"]
            fee_bps = self.params["fee_bps"]
            fill_prob = self.params["fill_probability"]
            
            # Similar to market order but with better prices
            slippage_bps = -offset_bps  # Negative = favorable
            
            # Use market order logic with adjusted slippage
            temp_params = {
                "slippage_bps": slippage_bps,
                "fee_bps": fee_bps,
                "slippage_model": "fixed"
            }
            
            market_block = MarketOrderBlock(self.node_id, temp_params)
            result = await market_block.execute(context, [])
            
            # Apply fill probability (some orders don't fill)
            if result.success:
                filled_orders = int(len(context.orders) * fill_prob)
                result.data["filled_orders"] = filled_orders
                result.data["missed_orders"] = len(context.orders) - filled_orders
            
            return result
            
        except Exception as e:
            return self._create_output(context, error=f"Limit order error: {str(e)}")

