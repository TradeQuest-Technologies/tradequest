#!/usr/bin/env python3
"""Simple script to clear all trades from database"""

import sqlite3
import os

def clear_trades():
    """Clear all trades from the database"""
    db_path = "tradequest.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count trades before deletion
        cursor.execute("SELECT COUNT(*) FROM trades")
        count_before = cursor.fetchone()[0]
        print(f"Found {count_before} trades in database")
        
        if count_before > 0:
            # Delete all trades
            cursor.execute("DELETE FROM trades")
            conn.commit()
            print(f"Deleted {count_before} trades from database")
        else:
            print("No trades to delete")
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM trades")
        count_after = cursor.fetchone()[0]
        print(f"Trades remaining: {count_after}")
        
        conn.close()
        print("Database cleanup completed successfully!")
        
    except Exception as e:
        print(f"Error clearing database: {e}")

if __name__ == "__main__":
    clear_trades()
