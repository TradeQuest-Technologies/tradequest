"""
CSV parser for different broker formats
"""

import pandas as pd
from typing import List, Dict, Any, Tuple
from datetime import datetime
import structlog
import re
import math

logger = structlog.get_logger()

class CSVParser:
    """Parser for different broker CSV formats"""
    
    def _validate_numeric_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Validate that numeric columns don't contain corrupted data that would cause JSON serialization issues"""
        try:
            # Check for NaN, Infinity, or other problematic values in numeric columns
            numeric_columns = []
            
            # Find columns that might contain numeric data
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['price', 'amount', 'qty', 'quantity', 'fee', 'pnl', 'profit', 'loss', 'value', 'cost']):
                    numeric_columns.append(col)
            
            for col in numeric_columns:
                if col in df.columns:
                    for idx, value in df[col].items():
                        if pd.isna(value):
                            continue  # Skip NaN values, they're handled elsewhere
                        
                        try:
                            # Try to convert to float
                            float_val = float(value)
                            
                            # Check for problematic values
                            if math.isnan(float_val):
                                return False, f"Row {idx + 1}, Column '{col}': Contains NaN value that cannot be serialized"
                            elif math.isinf(float_val):
                                return False, f"Row {idx + 1}, Column '{col}': Contains Infinity value that cannot be serialized"
                            
                        except (ValueError, TypeError, OverflowError):
                            # If it's not a number, that's okay - it might be text
                            continue
            
            return True, "Data validation passed"
            
        except Exception as e:
            return False, f"Data validation failed: {str(e)}"
    
    def _parse_currency(self, value: Any) -> float:
        """Parse currency string to float, handling $, commas, parentheses, and letters"""
        if pd.isna(value) or value == "":
            return 0.0
        
        # Convert to string and clean
        str_value = str(value).strip()
        
        # Skip if it looks like a date (contains slashes or dashes)
        if '/' in str_value or '-' in str_value:
            logger.warning("Skipping date value in currency parser", value=str(value))
            return 0.0
        
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
    
    def parse_trades(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse trades from DataFrame"""
        
        # Validate data first to prevent corruption
        is_valid, error_message = self._validate_numeric_data(df)
        if not is_valid:
            raise ValueError(f"CSV contains corrupted data that cannot be processed: {error_message}")
        
        # Detect broker format
        broker_format = self._detect_format(df)
        
        if broker_format == "binance":
            return self._parse_binance(df)
        elif broker_format == "kraken":
            return self._parse_kraken(df)
        elif broker_format == "coinbase":
            return self._parse_coinbase(df)
        elif broker_format == "bybit":
            return self._parse_bybit(df)
        else:
            return self._parse_generic(df)
    
    def _detect_format(self, df: pd.DataFrame) -> str:
        """Detect broker format from column names"""
        
        columns = [col.lower() for col in df.columns]
        
        if any("binance" in col for col in columns) or "trade id" in columns:
            return "binance"
        elif any("kraken" in col for col in columns) or "txid" in columns:
            return "kraken"
        elif any("coinbase" in col for col in columns) or "portfolio" in columns:
            return "coinbase"
        elif any("bybit" in col for col in columns) or "order id" in columns:
            return "bybit"
        else:
            return "generic"
    
    def _parse_binance(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse Binance format"""
        trades = []
        
        for _, row in df.iterrows():
            try:
                trade = {
                    "symbol": row.get("Symbol", ""),
                    "side": "buy" if row.get("Side") == "BUY" else "sell",
                    "qty": self._parse_currency(row.get("Executed Qty", 0)),
                    "avg_price": self._parse_currency(row.get("Price", 0)),
                    "fees": self._parse_currency(row.get("Commission", 0)),
                    "filled_at": pd.to_datetime(row.get("Date", "")),
                    "order_ref": str(row.get("Order ID", "")),
                    "raw": row.to_dict()
                }
                trades.append(trade)
            except Exception as e:
                logger.warning("Failed to parse Binance trade", error=str(e), row=row.to_dict())
                continue
        
        return trades
    
    def _parse_kraken(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse Kraken format"""
        trades = []
        
        for _, row in df.iterrows():
            try:
                trade = {
                    "symbol": row.get("pair", ""),
                    "side": "buy" if row.get("type") == "buy" else "sell",
                    "qty": self._parse_currency(row.get("vol", 0)),
                    "avg_price": self._parse_currency(row.get("price", 0)),
                    "fees": self._parse_currency(row.get("fee", 0)),
                    "filled_at": pd.to_datetime(row.get("time", "")),
                    "order_ref": str(row.get("ordertxid", "")),
                    "raw": row.to_dict()
                }
                trades.append(trade)
            except Exception as e:
                logger.warning("Failed to parse Kraken trade", error=str(e), row=row.to_dict())
                continue
        
        return trades
    
    def _parse_coinbase(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse Coinbase format"""
        trades = []
        
        for _, row in df.iterrows():
            try:
                trade = {
                    "symbol": row.get("Product", ""),
                    "side": "buy" if row.get("Side") == "BUY" else "sell",
                    "qty": self._parse_currency(row.get("Size", 0)),
                    "avg_price": self._parse_currency(row.get("Price", 0)),
                    "fees": self._parse_currency(row.get("Fee", 0)),
                    "filled_at": pd.to_datetime(row.get("Created At", "")),
                    "order_ref": str(row.get("Order ID", "")),
                    "raw": row.to_dict()
                }
                trades.append(trade)
            except Exception as e:
                logger.warning("Failed to parse Coinbase trade", error=str(e), row=row.to_dict())
                continue
        
        return trades
    
    def _parse_bybit(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse Bybit format"""
        trades = []
        
        for _, row in df.iterrows():
            try:
                trade = {
                    "symbol": row.get("Symbol", ""),
                    "side": "buy" if row.get("Side") == "Buy" else "sell",
                    "qty": self._parse_currency(row.get("Size", 0)),
                    "avg_price": self._parse_currency(row.get("Price", 0)),
                    "fees": self._parse_currency(row.get("Fee", 0)),
                    "filled_at": pd.to_datetime(row.get("Time", "")),
                    "order_ref": str(row.get("Order ID", "")),
                    "raw": row.to_dict()
                }
                trades.append(trade)
            except Exception as e:
                logger.warning("Failed to parse Bybit trade", error=str(e), row=row.to_dict())
                continue
        
        return trades
    
    def _parse_generic(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Parse generic format (try to map common column names)"""
        trades = []
        
        # Common column mappings
        column_mappings = {
            "symbol": ["symbol", "pair", "market", "product", "instrument"],
            "side": ["side", "type", "direction", "trans code"],
            "qty": ["qty", "quantity", "size", "vol"],
            "price": ["price", "avg_price", "rate"],
            "fees": ["fee", "fees", "commission"],
            "timestamp": ["timestamp", "time", "date", "created_at", "filled_at", "activity date"]
        }
        
        # Map columns
        mapped_columns = {}
        for target, possible_names in column_mappings.items():
            for col in df.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    mapped_columns[target] = col
                    break
        
        for _, row in df.iterrows():
            try:
                # Skip rows that don't look like trades (e.g., subscription fees)
                symbol = str(row.get(mapped_columns.get("symbol", ""), "")).strip()
                if not symbol or symbol.lower() in ["nan", "none", ""]:
                    continue
                
                # Determine side
                side_value = str(row.get(mapped_columns.get("side", ""), "")).lower()
                side = "buy" if side_value in ["buy", "b", "purchase"] else "sell"
                
                # Parse timestamp separately (not currency)
                timestamp_value = row.get(mapped_columns.get("timestamp", ""), "")
                filled_at = pd.to_datetime(timestamp_value) if timestamp_value else None
                
                trade = {
                    "symbol": symbol,
                    "side": side,
                    "qty": self._parse_currency(row.get(mapped_columns.get("qty", 0), 0)),
                    "avg_price": self._parse_currency(row.get(mapped_columns.get("price", 0), 0)),
                    "fees": self._parse_currency(row.get(mapped_columns.get("fees", 0), 0)),
                    "filled_at": filled_at,
                    "raw": row.to_dict()
                }
                trades.append(trade)
            except Exception as e:
                logger.warning("Failed to parse generic trade", error=str(e), row=row.to_dict())
                continue
        
        return trades
