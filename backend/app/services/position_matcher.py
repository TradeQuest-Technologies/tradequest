"""
Position matching service to track open/closed positions and calculate PnL from fills
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import structlog

logger = structlog.get_logger()

class PositionMatcher:
    """
    Matches fills (trades) to track positions and calculate realized PnL
    
    Works with fills from any venue (Hyperliquid, Kraken, Coinbase, etc.)
    """
    
    def __init__(self):
        # Track positions per symbol: {symbol: position_size}
        # Positive = long, negative = short
        self.positions: Dict[str, float] = defaultdict(float)
        
        # Track entry prices per symbol (FIFO queue)
        self.entry_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def process_fills(self, fills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of fills and calculate PnL for position closes
        
        Args:
            fills: List of fill dicts with 'symbol', 'side', 'qty', 'avg_price', 'filled_at'
            
        Returns:
            Same list of fills, but with 'pnl' field populated for closing trades
        """
        # Sort fills by time
        sorted_fills = sorted(fills, key=lambda f: f.get('filled_at', datetime.min))
        
        processed_fills = []
        
        for fill in sorted_fills:
            symbol = fill.get('symbol')
            side = fill.get('side', 'buy').lower()
            qty = float(fill.get('qty', 0))
            price = float(fill.get('avg_price', 0))
            fees = float(fill.get('fees', 0))
            
            # Determine if opening or closing
            current_position = self.positions[symbol]
            
            # Calculate PnL if closing a position
            realized_pnl = 0.0
            position_change = qty if side == 'buy' else -qty
            
            # Check if this trade closes or reduces a position
            if (current_position > 0 and side == 'sell') or (current_position < 0 and side == 'buy'):
                # Closing trade - calculate PnL
                realized_pnl = self._calculate_closing_pnl(
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    exit_price=price,
                    fees=fees
                )
            else:
                # Opening or adding to position
                self.entry_queue[symbol].append({
                    'qty': qty,
                    'price': price,
                    'filled_at': fill.get('filled_at'),
                    'side': side
                })
            
            # Update position
            self.positions[symbol] += position_change
            
            # Add PnL to fill
            fill['pnl'] = realized_pnl
            fill['position_after'] = self.positions[symbol]
            fill['position_direction'] = 'open' if abs(self.positions[symbol]) > abs(current_position) else 'close'
            
            processed_fills.append(fill)
        
        return processed_fills
    
    def _calculate_closing_pnl(
        self,
        symbol: str,
        side: str,
        qty: float,
        exit_price: float,
        fees: float
    ) -> float:
        """
        Calculate realized PnL for a closing trade using FIFO
        
        Args:
            symbol: Symbol being traded
            side: 'buy' or 'sell'
            qty: Quantity closed
            exit_price: Exit price
            fees: Transaction fees
            
        Returns:
            Realized PnL (positive = profit, negative = loss)
        """
        total_pnl = 0.0
        remaining_qty = qty
        
        # FIFO: Close oldest positions first
        while remaining_qty > 0 and self.entry_queue[symbol]:
            entry = self.entry_queue[symbol][0]
            entry_qty = entry['qty']
            entry_price = entry['price']
            entry_side = entry['side']
            
            # Calculate qty to close from this entry
            close_qty = min(remaining_qty, entry_qty)
            
            # Calculate PnL based on direction
            if entry_side == 'buy' and side == 'sell':
                # Closing long
                pnl = close_qty * (exit_price - entry_price)
            elif entry_side == 'sell' and side == 'buy':
                # Closing short
                pnl = close_qty * (entry_price - exit_price)
            else:
                pnl = 0
            
            total_pnl += pnl
            
            # Update entry queue
            if close_qty >= entry_qty:
                # Fully close this entry
                self.entry_queue[symbol].pop(0)
            else:
                # Partially close
                self.entry_queue[symbol][0]['qty'] -= close_qty
            
            remaining_qty -= close_qty
        
        # Subtract fees from PnL
        total_pnl -= fees
        
        return total_pnl
    
    def get_open_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all current open positions
        
        Returns:
            Dict mapping symbol -> position info
        """
        open_positions = {}
        
        for symbol, position_size in self.positions.items():
            if abs(position_size) > 0.0001:  # Account for floating point precision
                # Calculate average entry price
                total_cost = 0.0
                total_qty = 0.0
                
                for entry in self.entry_queue[symbol]:
                    total_cost += entry['qty'] * entry['price']
                    total_qty += entry['qty']
                
                avg_entry = total_cost / total_qty if total_qty > 0 else 0
                
                open_positions[symbol] = {
                    'size': position_size,
                    'avg_entry_price': avg_entry,
                    'direction': 'long' if position_size > 0 else 'short',
                    'open_qty': abs(position_size)
                }
        
        return open_positions

def match_and_calculate_pnl(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to match trades and calculate PnL
    
    Args:
        trades: List of trade dicts
        
    Returns:
        Same trades with PnL calculated
    """
    matcher = PositionMatcher()
    return matcher.process_fills(trades)

