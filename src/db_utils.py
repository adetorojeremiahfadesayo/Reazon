"""
Database utilities for connection management and safe query execution.
Provides context managers and wrappers to ensure connections are properly closed
and exceptions are logged, preventing resource leaks.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generator
from src.config import DB_PATH

# Configure logging
logger = logging.getLogger(__name__)

T = TypeVar("T")


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Ensures connection is properly closed even if an exception occurs.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
    
    Yields:
        sqlite3.Connection: Database connection
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


@contextmanager
def get_db_transaction() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database transactions.
    Automatically commits on success, rolls back on exception.
    
    Usage:
        with get_db_transaction() as conn:
            conn.execute("INSERT INTO table VALUES (...)")
            # Auto-commits on exit
    
    Yields:
        sqlite3.Connection: Database connection with transaction handling
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database transaction error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def execute_query(
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = True
) -> Optional[Any]:
    """
    Safe wrapper for executing SELECT queries.
    Handles connection management and error logging.
    
    Args:
        query: SQL SELECT query string
        params: Query parameters (tuple)
        fetch_one: If True, returns a single row
        fetch_all: If True, returns all rows (default)
    
    Returns:
        Query result or None if no results
        
    Example:
        result = execute_query("SELECT * FROM table WHERE id = ?", (1,), fetch_one=True)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return None
    except sqlite3.Error as e:
        logger.error(f"Query execution error: {e}. Query: {query}")
        raise


def execute_update(
    query: str,
    params: tuple = ()
) -> int:
    """
    Safe wrapper for executing INSERT, UPDATE, DELETE queries.
    Handles connection management, transaction, and error logging.
    
    Args:
        query: SQL INSERT/UPDATE/DELETE query string
        params: Query parameters (tuple)
    
    Returns:
        Number of rows affected
        
    Example:
        rows_affected = execute_update("UPDATE table SET col = ? WHERE id = ?", ("value", 1))
    """
    try:
        with get_db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
    except sqlite3.Error as e:
        logger.error(f"Update execution error: {e}. Query: {query}")
        raise


def execute_many(
    query: str,
    params_list: List[tuple]
) -> int:
    """
    Safe wrapper for batch operations (INSERT, UPDATE, DELETE).
    Handles connection, transaction, and error logging.
    
    Args:
        query: SQL query string with placeholders
        params_list: List of parameter tuples
    
    Returns:
        Total number of rows affected
        
    Example:
        rows = execute_many(
            "INSERT INTO table (col1, col2) VALUES (?, ?)",
            [("val1", "val2"), ("val3", "val4")]
        )
    """
    try:
        with get_db_transaction() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    except sqlite3.Error as e:
        logger.error(f"Batch execution error: {e}. Query: {query}")
        raise


def execute_script(script: str) -> None:
    """
    Safe wrapper for executing SQL scripts (multiple statements).
    Handles connection, transaction, and error logging.
    
    Args:
        script: SQL script with multiple statements
        
    Example:
        execute_script('''
            CREATE TABLE IF NOT EXISTS table1 (...);
            CREATE TABLE IF NOT EXISTS table2 (...);
        ''')
    """
    try:
        with get_db_transaction() as conn:
            conn.executescript(script)
    except sqlite3.Error as e:
        logger.error(f"Script execution error: {e}")
        raise


def init_db_tables() -> None:
    """
    Initialize all required database tables.
    Handles connection and error logging.
    """
    schema = """
        CREATE TABLE IF NOT EXISTS ai_call_cache (
            cache_key TEXT PRIMARY KEY,
            call_type TEXT NOT NULL,
            model TEXT NOT NULL,
            request_json TEXT NOT NULL,
            response_json TEXT NOT NULL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS profile_cache (
            cache_key TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            tier TEXT NOT NULL,
            model TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            target_certification TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            hit_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            agent_name TEXT,
            trace_content TEXT
        );

        CREATE TABLE IF NOT EXISTS badges (
            badge_id TEXT PRIMARY KEY,
            learner_id TEXT,
            certification_target TEXT,
            issued_to TEXT,
            score REAL,
            badge_json TEXT
        );
    """
    try:
        execute_script(schema)
        logger.info("Database tables initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise


class DatabasePool:
    """
    Simple connection pooling for improved performance.
    Maintains a pool of reusable connections with min/max limits.
    """

    def __init__(self, min_size: int = 2, max_size: int = 10):
        """
        Initialize connection pool.
        
        Args:
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections to allow
        """
        self.min_size = min_size
        self.max_size = max_size
        self._available: List[sqlite3.Connection] = []
        self._in_use: List[sqlite3.Connection] = []
        
        # Initialize minimum connections
        for _ in range(min_size):
            try:
                conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._available.append(conn)
            except sqlite3.Error as e:
                logger.error(f"Failed to create pooled connection: {e}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a connection from the pool.
        
        Usage:
            pool = DatabasePool()
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        
        Yields:
            sqlite3.Connection: Database connection from pool
        """
        conn = None
        try:
            # Try to get an available connection
            if self._available:
                conn = self._available.pop()
            elif len(self._in_use) < self.max_size:
                # Create a new connection if under max limit
                conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                conn.row_factory = sqlite3.Row
            else:
                # Wait for available connection (blocking)
                raise RuntimeError("Connection pool exhausted")
            
            self._in_use.append(conn)
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Pool connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and conn in self._in_use:
                self._in_use.remove(conn)
                self._available.append(conn)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        for conn in self._available:
            try:
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"Error closing pooled connection: {e}")
        
        for conn in self._in_use:
            try:
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"Error closing in-use connection: {e}")
        
        self._available.clear()
        self._in_use.clear()


# Global pool instance (optional, can be used for better performance)
_db_pool: Optional[DatabasePool] = None


def get_pool(min_size: int = 2, max_size: int = 10) -> DatabasePool:
    """
    Get or create the global database pool.
    
    Args:
        min_size: Minimum connections to maintain
        max_size: Maximum connections to allow
        
    Returns:
        DatabasePool: Global pool instance
    """
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool(min_size=min_size, max_size=max_size)
    return _db_pool


def close_pool() -> None:
    """Close all connections in the global pool."""
    global _db_pool
    if _db_pool:
        _db_pool.close_all()
        _db_pool = None
