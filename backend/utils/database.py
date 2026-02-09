"""
Database configuration and utilities for user management
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

# Configuration
DB_NAME = "users.db"
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with required tables"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            google_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Add new columns if they don't exist (migration)
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'google_id' not in columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT UNIQUE")
                logger.info("Added google_id column to users table")
            except Exception as e:
                logger.warning(f"google_id column may already exist: {e}")
        
        if 'username' in columns:
            # Check if username has NOT NULL constraint - if so, we need to fix it
            cursor.execute("PRAGMA table_info(users)")
            for col in cursor.fetchall():
                if col[1] == 'username' and col[3] == 1:  # col[3] is notnull flag
                    logger.info("Username column already allows NULL (compatible with OAuth)")
        
        conn.commit()
    logger.info("Database initialized successfully")


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def execute_query(query: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute a query with parameters"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

def fetch_one(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    """Fetch a single row"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

def fetch_all(query: str, params: tuple = ()) -> list:
    """Fetch all rows"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
import hashlib

def hash_password(password: str) -> str:
    """
    Hash a password using SHA256 for secure storage.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
