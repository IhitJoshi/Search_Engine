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

        # Detect legacy NOT NULL constraint on password_hash OR missing google_id
        needs_migration = False
        
        # Check password constraint
        password_notnull = any(
            col[1] == 'password_hash' and col[3] == 1  # col[3] is notnull flag
            for col in cols_info
        )
        
        # Check google_id presence
        missing_google_id = 'google_id' not in columns

        if password_notnull or missing_google_id:
            logger.info(f"Database migration needed. Password notnull: {password_notnull}, Missing google_id: {missing_google_id}")
            try:
                cursor.execute("BEGIN TRANSACTION")

                # Create new table with desired schema
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    google_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """) # Use IF NOT EXISTS to be safe, though users_new shouldn't exist ideally.
                # Actually, drop users_new if exists to be clean
                cursor.execute("DROP TABLE IF EXISTS users_new")
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

                # Construct SELECT query based on available columns
                select_cols = ["id", "username", "email", "password_hash", "created_at"]
                
                # Handle google_id specifically
                if missing_google_id:
                    google_id_select = "NULL as google_id"
                else:
                    google_id_select = "google_id"

                query = f"""
                    INSERT INTO users_new (id, username, email, password_hash, created_at, google_id)
                    SELECT {', '.join(select_cols)}, {google_id_select} FROM users
                """
                
                cursor.execute(query)

                # Replace old table
                cursor.execute("DROP TABLE users")
                cursor.execute("ALTER TABLE users_new RENAME TO users")

                cursor.execute("COMMIT")
                logger.info("Successfully migrated users table")
            except Exception as e:
                cursor.execute("ROLLBACK")
                logger.exception(f"Failed to migrate users table: {e}")

        conn.commit()

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
