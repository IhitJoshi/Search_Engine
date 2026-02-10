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
    """Initialize the database with required tables and run lightweight migrations."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Base schema (desired state)
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

        # Inspect current schema
        cursor.execute("PRAGMA table_info(users)")
        cols_info = cursor.fetchall()
        columns = [col[1] for col in cols_info]

        # Ensure google_id column exists
        if 'google_id' not in columns:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN google_id TEXT UNIQUE")
                logger.info("Added google_id column to users table")
            except Exception as e:
                logger.warning(f"google_id column may already exist: {e}")

        # Detect legacy NOT NULL constraint on password_hash (breaks OAuth-only users)
        password_notnull = any(
            col[1] == 'password_hash' and col[3] == 1  # col[3] is notnull flag
            for col in cols_info
        )

        if password_notnull:
            logger.info("Migrating users table to allow NULL password_hash for OAuth-only users")
            try:
                cursor.execute("BEGIN TRANSACTION")

                # Create new table with desired nullable password_hash
                cursor.execute("""
                CREATE TABLE users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                # Copy data from old table
                cursor.execute("""
                    INSERT INTO users_new (id, username, email, password_hash, google_id, created_at)
                    SELECT id, username, email, password_hash, google_id, created_at FROM users
                """)

                # Replace old table
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")

                cursor.execute("COMMIT")
                logger.info("Successfully migrated users table to nullable password_hash")
            except Exception as e:
                cursor.execute("ROLLBACK")
                logger.exception(f"Failed to migrate users table for nullable password_hash: {e}")

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
