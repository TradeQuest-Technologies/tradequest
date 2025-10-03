"""
Database utilities for PostgreSQL compatibility
"""

import os
from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB

def get_json_column_type():
    """
    Return the appropriate JSON column type based on the database backend.
    Uses JSONB for PostgreSQL, JSON for SQLite and other databases.
    """
    database_url = os.getenv('DATABASE_URL', '')
    
    if database_url.startswith('postgresql'):
        return JSONB
    else:
        return JSON

def create_json_column(*args, **kwargs):
    """
    Create a JSON column with the appropriate type for the current database.
    """
    json_type = get_json_column_type()
    return Column(json_type, *args, **kwargs)
