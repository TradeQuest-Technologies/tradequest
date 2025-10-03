"""
AI-powered CSV converter for different broker formats
"""

import pandas as pd
import json
from typing import Dict, List, Any, Optional
import structlog
from openai import OpenAI
import os
import re
import math
from io import StringIO
from app.core.config import settings

logger = structlog.get_logger()

class AICSVConverter:
    """AI-powered CSV converter that can handle any broker format"""
    
    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured in settings")
        self.client = OpenAI(api_key=api_key)
        
        # Our standardized format
        self.target_format = {
            "venue": "string (e.g., INTERACTIVE_BROKERS, TD_AMERITRADE, BINANCE, KRAKEN)",
            "symbol": "string (e.g., BTC/USDT, AAPL, EUR/USD, GOLD)",
            "side": "string (buy or sell)",
            "qty": "number (quantity traded)",
            "avg_price": "number (average price)",
            "fees": "number (trading fees)",
            "pnl": "number (profit/loss, can be 0)",
            "filled_at": "datetime (ISO format)",
            "order_ref": "string (optional order reference)"
        }
    
    def _parse_currency(self, value: Any) -> float:
        """Parse currency string to float, handling $, commas, parentheses, and letters"""
        if pd.isna(value) or value == "":
            return 0.0
        
        # Convert to string and clean
        str_value = str(value).strip()
        
        # Handle parentheses as negative (e.g., "($252.50)" -> -252.50)
        is_negative = str_value.startswith('(') and str_value.endswith(')')
        if is_negative:
            str_value = str_value[1:-1]  # Remove parentheses
        
        # Remove currency symbols, commas, and letters (like 'S' for shares)
        # Keep only numbers, decimal points, and minus signs
        cleaned = re.sub(r'[$,A-Za-z]', '', str_value)
        
        # If nothing left after cleaning, return 0
        if not cleaned.strip():
            logger.warning("No numeric value found after cleaning", original_value=str(value))
            return 0.0
        
        try:
            result = float(cleaned)
            
            # Check for problematic values that would cause JSON serialization issues
            if math.isnan(result):
                logger.warning("Currency value contains NaN, returning 0", original_value=str(value))
                return 0.0
            elif math.isinf(result):
                logger.warning("Currency value contains Infinity, returning 0", original_value=str(value))
                return 0.0
            
            return -result if is_negative else result
        except (ValueError, TypeError) as e:
            # Log warning and return 0 instead of raising error to prevent corruption
            logger.warning("Cannot parse currency value, returning 0", 
                         original_value=str(value), error=str(e))
            return 0.0
    
    async def convert_csv_with_ai(self, csv_content: str, filename: str, group_positions: bool = True) -> Dict[str, Any]:
        """Convert any CSV format to our standardized format using AI
        
        Args:
            csv_content: The CSV file content as a string
            filename: The filename for logging
            group_positions: If True, group individual trades into position cycles.
                           If False, treat each row as a complete position.
        """
        
        try:
            # Parse the CSV to understand its structure
            try:
                df = pd.read_csv(StringIO(csv_content))
            except pd.errors.ParserError as parse_error:
                # Try parsing with more flexible options
                try:
                    df = pd.read_csv(
                        StringIO(csv_content),
                        on_bad_lines='skip',  # Skip malformed lines
                        engine='python'       # Use Python engine for better error handling
                    )
                    logger.warning("AI CSV parsing had issues, skipped malformed lines", error=str(parse_error))
                except Exception as e:
                    raise ValueError(f"CSV file is malformed and cannot be parsed: {str(e)}")
            
            if df.empty:
                raise ValueError("CSV file is empty or contains no valid data")
            
            # Create a sample of the data for AI analysis (first 25 rows)
            sample_data = df.head(25).to_dict('records')
            columns = list(df.columns)
            
            # Create the AI prompt
            prompt = self._create_conversion_prompt(columns, sample_data, filename)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at converting trading data between different broker formats. You must return valid JSON only."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No valid JSON found in AI response")
            
            conversion_mapping = json.loads(ai_response[json_start:json_end])
            
            # Log the AI's column mapping for debugging
            logger.info("AI column mapping", 
                       broker=conversion_mapping.get("broker_name"),
                       columns=conversion_mapping.get("column_mapping"))
            
            # Apply the conversion mapping and optionally group into positions
            positions = self._apply_conversion_mapping(df, conversion_mapping, group_positions)
            
            logger.info("AI CSV conversion successful", 
                       original_rows=len(df), 
                       positions_created=len(positions),
                       group_positions=group_positions,
                       filename=filename)
            
            return {
                "success": True,
                "positions": positions,
                "original_rows": len(df),
                "positions_created": len(positions),
                "mapping": conversion_mapping,
                "broker_detected": conversion_mapping.get("broker_name", "Unknown")
            }
            
        except Exception as e:
            logger.error("AI CSV conversion failed", error=str(e), filename=filename)
            return {
                "success": False,
                "error": str(e),
                "trades": []
            }
    
    def _create_conversion_prompt(self, columns: List[str], sample_data: List[Dict], filename: str) -> str:
        """Create the AI prompt for CSV conversion"""
        
        target_format_str = json.dumps(self.target_format, indent=2)
        sample_data_str = json.dumps(sample_data, indent=2)
        
        return f"""
I need to analyze a broker CSV file and provide column mapping for a trading journal system. This system creates JOURNAL ENTRIES for completed trading positions, grouping multiple trades into position cycles.

**Source CSV Info:**
- Filename: {filename}
- Columns: {columns}
- Sample data (first 25 rows): {sample_data_str}

**Target Fields We Need:**
For raw trades:
- symbol: Trading pair/symbol (e.g., BTC/USDT, AAPL, EUR/USD)
- side: Buy/Sell/Long/Short direction
- qty: Quantity/amount traded
- price: Price per unit
- fees: Trading fees/commission
- timestamp: Date/time of trade
- order_ref: Order ID or reference (optional)

For complete positions (if available):
- entry_price: Average entry price (also called "Avg Entry", "Open Price", etc.)
- exit_price: Average exit/close price (also called "Avg Close", "Close Price", etc.)
- pnl: Realized profit/loss (also called "Realized PNL", "Profit", etc.)
- open_time: Position open timestamp
- close_time: Position close timestamp

**JOURNAL POSITION LOGIC:**
The system groups trades into completed position cycles:
- Position cycles end when balance reaches zero (all shares sold)
- Each cycle becomes a separate journal entry
- Example: Buy 1000 → Sell 1000 → Buy 1000 → Sell 1000 = 2 separate journal entries
- Peak quantity = maximum shares held during the cycle
- Entry price = weighted average of all buys
- Exit price = weighted average of all sells

**YOUR TASK:**
Analyze the sample data and provide column mapping. Return ONLY valid JSON.

**Required JSON Output:**
```json
{{
  "broker_name": "Detected Broker Name",
  "column_mapping": {{
    "symbol": "Column Name for Symbol",
    "side": "Column Name for Buy/Sell/Long/Short Direction", 
    "qty": "Column Name for Quantity/Amount",
    "price": "Column Name for Price per Unit (if single price)",
    "entry_price": "Column Name for Entry/Open Price (if separate)",
    "exit_price": "Column Name for Exit/Close Price (if separate)",
    "pnl": "Column Name for Realized PNL/Profit",
    "fees": "Column Name for Fees/Commission",
    "timestamp": "Column Name for Date/Time (if single time)",
    "open_time": "Column Name for Open Time (if separate)",
    "close_time": "Column Name for Close Time (if separate)",
    "order_ref": "Column Name for Order ID (optional)"
  }},
  "transformations": {{
    "side": "How to convert side values (e.g., BUY->buy, SELL->sell)",
    "symbol": "How to format symbols (e.g., BTCUSDT->BTC/USDT)",
    "datetime": "Date format conversion needed"
  }},
  "position_logic": {{
    "group_by_symbol": true,
    "dca_detection": "How to identify DCA entries vs separate positions",
    "notes": "Any special considerations for this broker format"
  }}
}}
```

**IMPORTANT**: Return ONLY the JSON object above. No explanations or additional text.
"""
    
    def _apply_conversion_mapping(self, df: pd.DataFrame, mapping: Dict[str, Any], group_positions: bool = True) -> List[Dict[str, Any]]:
        """Apply the AI-generated mapping to convert the data and optionally group into positions
        
        Args:
            df: The DataFrame containing the CSV data
            mapping: The AI-generated column mapping
            group_positions: If True, group trades into position cycles. If False, treat each row as a position.
        """
        
        column_mapping = mapping.get("column_mapping", {})
        transformations = mapping.get("transformations", {})
        broker_name = mapping.get("broker_name", "UNKNOWN")
        
        # First, convert all rows to standardized format
        raw_trades = []
        
        for _, row in df.iterrows():
            try:
                trade = {}
                
                # Map each field
                for target_field, source_column in column_mapping.items():
                    if source_column and source_column in df.columns:
                        value = row[source_column]
                        
                        # Apply transformations
                        if target_field == "side" and transformations.get("side"):
                            value = self._apply_side_transformation(value, transformations["side"])
                        elif target_field == "symbol" and transformations.get("symbol"):
                            value = self._apply_symbol_transformation(value, transformations["symbol"])
                        elif target_field in ["timestamp", "open_time", "close_time"] and transformations.get("datetime"):
                            value = self._apply_datetime_transformation(value, transformations["datetime"])
                        elif target_field in ["qty", "price", "fees", "pnl", "entry_price", "exit_price"]:
                            # Parse currency values for numeric fields
                            value = self._parse_currency(value)
                        
                        trade[target_field] = value
                    else:
                        # Set default values
                        if target_field in ["fees", "pnl"]:
                            trade[target_field] = 0
                        else:
                            trade[target_field] = None
                
                # Ensure required fields have values
                if trade.get("fees") is None:
                    trade["fees"] = 0
                
                raw_trades.append(trade)
                
            except Exception as e:
                logger.warning("Failed to convert trade row", error=str(e), row=row.to_dict())
                continue
        
        # Group trades into positions if requested, otherwise treat each as a position
        if group_positions:
            return self._group_trades_into_positions(raw_trades)
        else:
            # Treat each trade as a complete position - no grouping
            return self._convert_trades_to_positions(raw_trades)
    
    def _convert_trades_to_positions(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert each trade row directly to a position without grouping
        
        This is used when the CSV already contains complete positions (not raw trades).
        For complete positions, we expect entry_price, exit_price, pnl fields to be present.
        """
        positions = []
        
        for trade in trades:
            # Extract the necessary fields
            symbol = trade.get("symbol", "")
            side = trade.get("side", "buy")
            qty = self._parse_currency(trade.get("qty", 0))
            
            # Try to get entry and exit prices (for complete positions)
            entry_price = self._parse_currency(trade.get("entry_price", 0))
            exit_price = self._parse_currency(trade.get("exit_price", 0))
            
            # Fallback to "price" if entry_price not found
            if entry_price == 0:
                entry_price = self._parse_currency(trade.get("price", 0))
            
            fees = self._parse_currency(trade.get("fees", 0))
            pnl = self._parse_currency(trade.get("pnl", 0))
            
            open_time = trade.get("open_time") or trade.get("timestamp")
            close_time = trade.get("close_time") or trade.get("timestamp")
            
            # Normalize side to long/short
            side_lower = str(side).lower()
            if side_lower in ['long', 'buy']:
                normalized_side = 'long'
            elif side_lower in ['short', 'sell']:
                normalized_side = 'short'
            else:
                normalized_side = 'long'  # Default
            
            # For complete positions, use the provided data
            position = {
                "symbol": symbol,
                "side": normalized_side,
                "qty": qty,
                "avg_price": entry_price,  # Use entry price as main price
                "fees": fees,
                "pnl": pnl,
                "filled_at": open_time,
                "submitted_at": close_time,
                "raw": {
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "peak_quantity": qty,
                    "net_quantity": qty,
                    "total_buy_qty": qty if normalized_side == "long" else 0,
                    "total_sell_qty": qty if normalized_side == "short" else 0,
                    "cycle_complete": True,  # Complete position
                    "total_trades": 1,
                    "buy_trades": 1 if normalized_side == "long" else 0,
                    "sell_trades": 1 if normalized_side == "short" else 0,
                    "trades": [trade]
                }
            }
            
            logger.info("Converted position", 
                       symbol=symbol,
                       side=normalized_side,
                       entry=entry_price,
                       exit=exit_price,
                       qty=qty,
                       pnl=pnl)
            
            positions.append(position)
        
        return positions
    
    def _group_trades_into_positions(self, trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group individual trades into positions based on position cycles (balance reaching zero)"""
        
        # Group by symbol
        symbol_groups = {}
        for trade in trades:
            symbol = trade.get("symbol")
            if not symbol:
                continue
                
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(trade)
        
        positions = []
        
        for symbol, symbol_trades in symbol_groups.items():
            # Sort by timestamp
            symbol_trades.sort(key=lambda x: x.get("timestamp", ""))
            
            # Track position cycles (when balance reaches zero)
            position_cycles = self._detect_position_cycles(symbol_trades)
            
            # Create separate position for each cycle
            for cycle_trades in position_cycles:
                if cycle_trades:  # Only create position if there are trades
                    position = self._create_position_from_cycle(symbol, cycle_trades)
                    positions.append(position)
        
        return positions
    
    def _detect_position_cycles(self, trades: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Detect position cycles by tracking running balance"""
        
        cycles = []
        current_cycle = []
        running_balance = 0
        
        for trade in trades:
            side = trade.get("side")
            qty = self._parse_currency(trade.get("qty", 0))
            
            # Update running balance
            if side == "buy":
                running_balance += qty
            elif side == "sell":
                running_balance -= qty
            
            # Add trade to current cycle
            current_cycle.append(trade)
            
            # Check if position cycle is complete (balance reaches zero or goes negative)
            if running_balance <= 0:
                # Position cycle complete - start new cycle
                cycles.append(current_cycle)
                current_cycle = []
                running_balance = 0
        
        # Add any remaining trades as final cycle
        if current_cycle:
            cycles.append(current_cycle)
        
        return cycles
    
    def _create_position_from_cycle(self, symbol: str, cycle_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a journal position from a complete trade cycle (matches manual trade format)"""
        
        # Separate buys and sells in this cycle
        buys = [t for t in cycle_trades if t.get("side") == "buy"]
        sells = [t for t in cycle_trades if t.get("side") == "sell"]
        
        # Calculate total quantities
        total_buy_qty = sum(self._parse_currency(trade.get("qty", 0)) for trade in buys)
        total_sell_qty = sum(self._parse_currency(trade.get("qty", 0)) for trade in sells)
        
        # Calculate weighted average buy price (entry price)
        total_buy_value = 0
        for trade in buys:
            qty = self._parse_currency(trade.get("qty", 0))
            price = self._parse_currency(trade.get("price", 0))
            total_buy_value += qty * price
        
        avg_buy_price = total_buy_value / total_buy_qty if total_buy_qty > 0 else 0
        
        # Calculate weighted average sell price (exit price)
        total_sell_value = 0
        for trade in sells:
            qty = self._parse_currency(trade.get("qty", 0))
            price = self._parse_currency(trade.get("price", 0))
            total_sell_value += qty * price
        
        avg_sell_price = total_sell_value / total_sell_qty if total_sell_qty > 0 else 0
        
        # Calculate total fees
        total_fees = sum(self._parse_currency(trade.get("fees", 0)) for trade in cycle_trades)
        
        # Determine position side based on net direction
        net_qty = total_buy_qty - total_sell_qty
        if net_qty > 0:
            side = "long"
        elif net_qty < 0:
            side = "short"
        else:
            # Equal buy/sell - determine by first trade
            side = "long" if cycle_trades[0].get("side") == "buy" else "short"
        
        # Peak quantity is the maximum quantity held at any point
        peak_qty = self._calculate_peak_quantity(cycle_trades)
        
        # Calculate total PnL
        if total_buy_qty == total_sell_qty:
            # Complete cycle - all bought shares were sold
            total_pnl = total_sell_value - total_buy_value - total_fees
        else:
            # Incomplete cycle - calculate PnL from sold portion
            total_pnl = (avg_sell_price - avg_buy_price) * total_sell_qty - total_fees
        
        # Get open and close times
        open_time = cycle_trades[0].get("timestamp") if cycle_trades else None
        close_time = cycle_trades[-1].get("timestamp") if cycle_trades else None
        
        # Create journal position (matches manual trade format)
        position = {
            "symbol": symbol,
            "side": side,
            "qty": peak_qty,  # Peak quantity held
            "avg_price": avg_buy_price,  # Entry price
            "fees": total_fees,
            "pnl": total_pnl,
            "filled_at": open_time,  # Entry time
            "submitted_at": close_time,  # Exit time
            "raw": {
                "entry_price": avg_buy_price,
                "exit_price": avg_sell_price,
                "peak_quantity": peak_qty,
                "net_quantity": net_qty,
                "total_buy_qty": total_buy_qty,
                "total_sell_qty": total_sell_qty,
                "cycle_complete": total_buy_qty == total_sell_qty,
                "total_trades": len(cycle_trades),
                "buy_trades": len(buys),
                "sell_trades": len(sells),
                "trades": cycle_trades
            }
        }
        
        return position
    
    def _calculate_peak_quantity(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate the peak quantity held during the trade cycle"""
        
        running_balance = 0
        peak_qty = 0
        
        for trade in trades:
            side = trade.get("side")
            qty = self._parse_currency(trade.get("qty", 0))
            
            # Update running balance
            if side == "buy":
                running_balance += qty
            elif side == "sell":
                running_balance -= qty
            
            # Track peak quantity
            peak_qty = max(peak_qty, abs(running_balance))
        
        return peak_qty
    
    def _apply_side_transformation(self, value: Any, transformation: str) -> str:
        """Apply side transformation (e.g., BUY -> buy, LONG -> long, SHORT -> short)"""
        if pd.isna(value):
            return "long"  # default
        
        value_str = str(value).upper().strip()
        
        # Check for long/buy variants
        if "LONG" in value_str or "BUY" in value_str or value_str == "B" or value_str == "L":
            return "long"
        # Check for short/sell variants
        elif "SHORT" in value_str or "SELL" in value_str or value_str == "S":
            return "short"
        else:
            logger.warning("Unknown side value, defaulting to long", value=value_str)
            return "long"  # default
    
    def _apply_symbol_transformation(self, value: Any, transformation: str) -> str:
        """Apply symbol transformation"""
        if pd.isna(value):
            return ""
        
        symbol = str(value).strip()
        
        # Add /USDT if missing and it looks like a crypto symbol
        if "/" not in symbol and len(symbol) <= 10:
            symbol = f"{symbol}/USDT"
        
        return symbol
    
    def _apply_datetime_transformation(self, value: Any, transformation: str) -> str:
        """Apply datetime transformation"""
        if pd.isna(value):
            return pd.Timestamp.now().isoformat()
        
        try:
            # Try to parse with pandas
            dt = pd.to_datetime(value)
            return dt.isoformat()
        except:
            # Fallback to current time
            return pd.Timestamp.now().isoformat()
