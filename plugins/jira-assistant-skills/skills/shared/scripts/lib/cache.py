"""
Caching layer for JIRA API responses.

Provides persistent caching with TTL support, LRU eviction,
pattern-based invalidation, and thread-safe access.

Features:
- SQLite-based persistence for durability
- Category-based TTL defaults (issue: 5min, project: 1hr, user: 1hr, field: 1day)
- LRU eviction when cache size limit is reached
- Pattern-based key invalidation (glob patterns with SQL LIKE optimization)
- Thread-safe concurrent access
- Cache hit/miss statistics
"""

import os
import json
import sqlite3
import hashlib
import threading
import fnmatch
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, NamedTuple, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class CacheStats:
    """Cache statistics container."""
    entry_count: int = 0
    total_size_bytes: int = 0
    hits: int = 0
    misses: int = 0
    by_category: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


def is_simple_glob_pattern(pattern: str) -> bool:
    """
    Check if a glob pattern is simple enough to convert to SQL LIKE.

    Simple patterns only use:
    - * for any characters (converted to %)
    - ? for single character (converted to _)
    - No character classes like [abc]
    - No nested patterns

    Args:
        pattern: Glob pattern to check

    Returns:
        True if pattern can be converted to SQL LIKE
    """
    # Patterns with character classes are not simple
    if '[' in pattern or ']' in pattern:
        return False

    # Patterns with special glob syntax are not simple
    if '{' in pattern or '}' in pattern:
        return False

    # Patterns with ** (recursive) need special handling
    if '**' in pattern:
        # **/ can be handled as % in SQL
        return True

    return True


def glob_to_sql_like(pattern: str) -> Tuple[str, bool]:
    """
    Convert a glob pattern to SQL LIKE pattern if possible.

    Args:
        pattern: Glob pattern (e.g., "PROJ-*", "issue:*:detail")

    Returns:
        Tuple of (sql_pattern, is_converted) where:
        - sql_pattern: The SQL LIKE pattern if converted, else original
        - is_converted: True if successfully converted to SQL LIKE
    """
    if not is_simple_glob_pattern(pattern):
        return pattern, False

    # Escape SQL LIKE special characters that aren't glob chars
    sql_pattern = pattern

    # Escape % and _ that are literal in glob but special in SQL
    sql_pattern = sql_pattern.replace('%', r'\%')
    sql_pattern = sql_pattern.replace('_', r'\_')

    # Convert glob wildcards to SQL LIKE
    # ** matches any path including /
    sql_pattern = sql_pattern.replace('**/', '%')
    sql_pattern = sql_pattern.replace('**', '%')
    # * matches any characters except /
    sql_pattern = sql_pattern.replace('*', '%')
    # ? matches single character
    sql_pattern = sql_pattern.replace('?', '_')

    return sql_pattern, True


class JiraCache:
    """
    Caching layer for JIRA API responses.

    Provides persistent caching with configurable TTLs per category,
    LRU eviction, and pattern-based invalidation.
    """

    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: float = 100):
        """
        Initialize cache.

        SECURITY NOTE: The cache may contain sensitive data including:
        - Issue details (potentially confidential project information)
        - User information (account IDs, emails, display names)
        - API response data with project/company details

        The cache directory is created with restrictive permissions (0700)
        to ensure only the owner can access cached data.

        Args:
            cache_dir: Directory for cache storage (default: ~/.jira-skills/cache)
            max_size_mb: Maximum cache size in megabytes (default: 100 MB)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".jira-skills" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Ensure restrictive permissions even if directory already exists
        # This protects against directory created with default permissions
        os.chmod(self.cache_dir, 0o700)

        self.max_size = int(max_size_mb * 1024 * 1024)  # Convert to bytes
        self.db_path = self.cache_dir / "cache.db"

        # TTL defaults by category
        self.ttl_defaults = {
            "issue": timedelta(minutes=5),
            "project": timedelta(hours=1),
            "user": timedelta(hours=1),
            "field": timedelta(days=1),
            "search": timedelta(minutes=1),
            "default": timedelta(minutes=5),
        }

        # Thread-safe access
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0

        # Initialize database
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database for cache storage."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT NOT NULL,
                    category TEXT NOT NULL,
                    value TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    last_accessed_at REAL NOT NULL,
                    PRIMARY KEY (key, category)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_category ON cache_entries(category)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_lru ON cache_entries(last_accessed_at)
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get thread-safe database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get(self, key: str, category: str = "default") -> Optional[Any]:
        """
        Get cached value if not expired.

        Args:
            key: Cache key
            category: Cache category (affects default TTL)

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            now = time.time()

            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT value, expires_at FROM cache_entries
                    WHERE key = ? AND category = ?
                """, (key, category))
                row = cursor.fetchone()

                if row is None:
                    self._misses += 1
                    return None

                if row["expires_at"] < now:
                    # Entry expired, delete it
                    conn.execute("""
                        DELETE FROM cache_entries WHERE key = ? AND category = ?
                    """, (key, category))
                    conn.commit()
                    self._misses += 1
                    return None

                # Update last accessed time for LRU
                conn.execute("""
                    UPDATE cache_entries SET last_accessed_at = ?
                    WHERE key = ? AND category = ?
                """, (now, key, category))
                conn.commit()

                self._hits += 1
                return json.loads(row["value"])

    def set(self, key: str, value: Any, category: str = "default",
            ttl: Optional[timedelta] = None) -> None:
        """
        Set cache value with optional custom TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            category: Cache category (affects default TTL)
            ttl: Custom TTL (default: category default)
        """
        with self._lock:
            if ttl is None:
                ttl = self.ttl_defaults.get(category, self.ttl_defaults["default"])

            now = time.time()
            expires_at = now + ttl.total_seconds()
            value_json = json.dumps(value)
            size_bytes = len(value_json.encode('utf-8'))

            # Validate single entry is not larger than max cache size
            if size_bytes > self.max_size:
                raise ValueError(
                    f"Cache entry size ({size_bytes} bytes) exceeds maximum cache size "
                    f"({self.max_size} bytes). Consider increasing max_size_mb or caching smaller data."
                )

            # Check if we need to evict entries
            self._evict_if_needed(size_bytes)

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries
                    (key, category, value, size_bytes, created_at, expires_at, last_accessed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (key, category, value_json, size_bytes, now, expires_at, now))
                conn.commit()

    def _evict_if_needed(self, new_entry_size: int) -> None:
        """Evict entries if adding new entry would exceed size limit."""
        with self._get_connection() as conn:
            # Get current total size
            cursor = conn.execute("SELECT COALESCE(SUM(size_bytes), 0) as total FROM cache_entries")
            current_size = cursor.fetchone()["total"]

            # If we're within limit, no eviction needed
            if current_size + new_entry_size <= self.max_size:
                return

            # Calculate how much space we need to free
            space_needed = current_size + new_entry_size - self.max_size

            # Delete expired entries first
            now = time.time()
            conn.execute("DELETE FROM cache_entries WHERE expires_at < ?", (now,))

            # Check if that freed enough space
            cursor = conn.execute("SELECT COALESCE(SUM(size_bytes), 0) as total FROM cache_entries")
            current_size = cursor.fetchone()["total"]

            if current_size + new_entry_size <= self.max_size:
                conn.commit()
                return

            # Evict LRU entries until we have enough space
            space_needed = current_size + new_entry_size - self.max_size
            freed = 0

            cursor = conn.execute("""
                SELECT key, category, size_bytes FROM cache_entries
                ORDER BY last_accessed_at ASC
            """)

            entries_to_delete = []
            for row in cursor:
                if freed >= space_needed:
                    break
                entries_to_delete.append((row["key"], row["category"]))
                freed += row["size_bytes"]

            for key, category in entries_to_delete:
                conn.execute("""
                    DELETE FROM cache_entries WHERE key = ? AND category = ?
                """, (key, category))

            conn.commit()

    def invalidate(self, key: Optional[str] = None, pattern: Optional[str] = None,
                   category: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Uses SQL LIKE for simple glob patterns (containing only * and ?)
        for better performance on large caches. Falls back to Python
        fnmatch for complex patterns with character classes.

        Args:
            key: Specific key to invalidate
            pattern: Glob pattern for keys to invalidate (e.g., "PROJ-*")
            category: Category to invalidate (all keys in category if no key/pattern)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            with self._get_connection() as conn:
                if key is not None and category is not None:
                    # Invalidate specific key in category
                    cursor = conn.execute("""
                        DELETE FROM cache_entries WHERE key = ? AND category = ?
                    """, (key, category))
                    conn.commit()
                    return cursor.rowcount

                elif pattern is not None:
                    # Try to use SQL LIKE for simple patterns (performance optimization)
                    sql_pattern, can_use_like = glob_to_sql_like(pattern)

                    if can_use_like:
                        # Use SQL LIKE directly - much faster for large caches
                        if category is not None:
                            cursor = conn.execute("""
                                DELETE FROM cache_entries
                                WHERE key LIKE ? ESCAPE '\\' AND category = ?
                            """, (sql_pattern, category))
                        else:
                            cursor = conn.execute("""
                                DELETE FROM cache_entries
                                WHERE key LIKE ? ESCAPE '\\'
                            """, (sql_pattern,))
                        conn.commit()
                        return cursor.rowcount
                    else:
                        # Fall back to Python fnmatch for complex patterns
                        if category is not None:
                            cursor = conn.execute("""
                                SELECT key FROM cache_entries WHERE category = ?
                            """, (category,))
                        else:
                            cursor = conn.execute("SELECT key, category FROM cache_entries")

                        to_delete = []
                        for row in cursor:
                            if fnmatch.fnmatch(row["key"], pattern):
                                if category is not None:
                                    to_delete.append((row["key"], category))
                                else:
                                    to_delete.append((row["key"], row["category"]))

                        for k, cat in to_delete:
                            conn.execute("""
                                DELETE FROM cache_entries WHERE key = ? AND category = ?
                            """, (k, cat))

                        conn.commit()
                        return len(to_delete)

                elif category is not None:
                    # Invalidate entire category
                    cursor = conn.execute("""
                        DELETE FROM cache_entries WHERE category = ?
                    """, (category,))
                    conn.commit()
                    return cursor.rowcount

                return 0

    def clear(self) -> int:
        """
        Clear entire cache.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as count FROM cache_entries")
                count = cursor.fetchone()["count"]
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
                return count

    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats object with current statistics
        """
        with self._lock:
            stats = CacheStats(hits=self._hits, misses=self._misses)

            with self._get_connection() as conn:
                # Total count and size
                cursor = conn.execute("""
                    SELECT COUNT(*) as count, COALESCE(SUM(size_bytes), 0) as total_size
                    FROM cache_entries
                """)
                row = cursor.fetchone()
                stats.entry_count = row["count"]
                stats.total_size_bytes = row["total_size"]

                # Stats by category
                cursor = conn.execute("""
                    SELECT category, COUNT(*) as count, SUM(size_bytes) as size
                    FROM cache_entries
                    GROUP BY category
                """)
                for row in cursor:
                    stats.by_category[row["category"]] = {
                        "count": row["count"],
                        "size_bytes": row["size"]
                    }

            return stats

    def generate_key(self, category: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            category: Cache category
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Generated cache key
        """
        # Build key components
        components = [category]
        components.extend(str(arg) for arg in args)

        # Sort kwargs for consistent key generation
        for key in sorted(kwargs.keys()):
            components.append(f"{key}={kwargs[key]}")

        # Create key string
        key_str = ":".join(components)

        # For long keys, use a hash
        if len(key_str) > 200:
            hash_suffix = hashlib.md5(key_str.encode()).hexdigest()[:16]
            key_str = f"{category}:{hash_suffix}"

        return key_str

    def close(self) -> None:
        """Close cache (flush any pending operations)."""
        # SQLite connections are closed per-operation, nothing to do
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def get_cache(cache_dir: Optional[str] = None, max_size_mb: float = 100) -> JiraCache:
    """
    Get or create a cache instance.

    Args:
        cache_dir: Optional custom cache directory
        max_size_mb: Maximum cache size in MB

    Returns:
        JiraCache instance
    """
    return JiraCache(cache_dir=cache_dir, max_size_mb=max_size_mb)
