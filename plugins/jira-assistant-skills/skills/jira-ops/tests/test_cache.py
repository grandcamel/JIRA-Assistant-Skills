"""
Test suite for JiraCache caching layer.

Tests cover:
- Cache hit/miss behavior
- TTL expiration
- Key invalidation (single, pattern, category)
- Size limits and LRU eviction
- Persistence across sessions
- Thread-safe concurrent access
- Cache statistics
"""

import pytest
import time
import threading
import json
from datetime import timedelta
from pathlib import Path
import sys

# Add shared lib to path (absolute path)
shared_lib_path = str(Path(__file__).resolve().parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import JiraCache, CacheStats


@pytest.mark.ops
@pytest.mark.unit
class TestCacheGetHit:
    """Test cache hit returns cached value."""

    def test_cache_get_hit_returns_value(self, temp_cache_dir, sample_issue_data):
        """Test that cache returns stored value on hit."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue:PROJ-123", sample_issue_data, category="issue")

        result = cache.get("issue:PROJ-123", category="issue")

        assert result is not None
        assert result == sample_issue_data
        assert result["key"] == "PROJ-123"

    def test_cache_get_hit_different_categories(self, temp_cache_dir, sample_issue_data, sample_project_data):
        """Test cache hit works correctly across different categories."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", sample_issue_data, category="issue")
        cache.set("PROJ", sample_project_data, category="project")

        issue_result = cache.get("PROJ-123", category="issue")
        project_result = cache.get("PROJ", category="project")

        assert issue_result["key"] == "PROJ-123"
        assert project_result["key"] == "PROJ"


@pytest.mark.ops
@pytest.mark.unit
class TestCacheGetMiss:
    """Test cache miss returns None."""

    def test_cache_get_miss_returns_none(self, temp_cache_dir):
        """Test that cache returns None for missing keys."""
        cache = JiraCache(cache_dir=temp_cache_dir)

        result = cache.get("nonexistent:key", category="issue")

        assert result is None

    def test_cache_get_miss_wrong_category(self, temp_cache_dir, sample_issue_data):
        """Test that cache miss occurs when category doesn't match."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", sample_issue_data, category="issue")

        result = cache.get("PROJ-123", category="project")

        assert result is None


@pytest.mark.ops
@pytest.mark.unit
class TestCacheSet:
    """Test setting cache values."""

    def test_cache_set_basic(self, temp_cache_dir, sample_issue_data):
        """Test basic cache set operation."""
        cache = JiraCache(cache_dir=temp_cache_dir)

        cache.set("issue:PROJ-123", sample_issue_data, category="issue")
        result = cache.get("issue:PROJ-123", category="issue")

        assert result == sample_issue_data

    def test_cache_set_overwrites_existing(self, temp_cache_dir):
        """Test that set overwrites existing value."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", {"version": 1}, category="issue")
        cache.set("key1", {"version": 2}, category="issue")

        result = cache.get("key1", category="issue")

        assert result["version"] == 2

    def test_cache_set_complex_data(self, temp_cache_dir):
        """Test caching complex nested data structures."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        complex_data = {
            "nested": {"deep": {"value": [1, 2, 3]}},
            "list": [{"a": 1}, {"b": 2}],
            "number": 42,
            "string": "test",
            "boolean": True,
            "null": None
        }

        cache.set("complex", complex_data, category="issue")
        result = cache.get("complex", category="issue")

        assert result == complex_data


@pytest.mark.ops
@pytest.mark.unit
class TestCacheTTLExpiration:
    """Test cache returns None after TTL expires."""

    def test_cache_ttl_expired(self, temp_cache_dir):
        """Test that cache returns None after TTL expires."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        # Use a very short TTL for testing
        cache.set("key", {"value": "test"}, category="issue", ttl=timedelta(milliseconds=50))

        # Value should be available immediately
        assert cache.get("key", category="issue") is not None

        # Wait for TTL to expire
        time.sleep(0.1)

        result = cache.get("key", category="issue")
        assert result is None

    def test_cache_ttl_not_expired(self, temp_cache_dir):
        """Test that cache returns value before TTL expires."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key", {"value": "test"}, category="issue", ttl=timedelta(hours=1))

        result = cache.get("key", category="issue")

        assert result is not None
        assert result["value"] == "test"

    def test_cache_default_ttl_by_category(self, temp_cache_dir):
        """Test that default TTLs are applied by category."""
        cache = JiraCache(cache_dir=temp_cache_dir)

        # Check default TTLs are set
        assert cache.ttl_defaults["issue"] == timedelta(minutes=5)
        assert cache.ttl_defaults["project"] == timedelta(hours=1)
        assert cache.ttl_defaults["user"] == timedelta(hours=1)
        assert cache.ttl_defaults["field"] == timedelta(days=1)
        assert cache.ttl_defaults["search"] == timedelta(minutes=1)


@pytest.mark.ops
@pytest.mark.unit
class TestCacheInvalidateKey:
    """Test invalidating specific cache key."""

    def test_cache_invalidate_single_key(self, temp_cache_dir, sample_issue_data):
        """Test invalidating a single cache key."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", sample_issue_data, category="issue")
        cache.set("PROJ-456", {"key": "PROJ-456"}, category="issue")

        cache.invalidate(key="PROJ-123", category="issue")

        assert cache.get("PROJ-123", category="issue") is None
        assert cache.get("PROJ-456", category="issue") is not None

    def test_cache_invalidate_nonexistent_key(self, temp_cache_dir):
        """Test invalidating a nonexistent key doesn't raise error."""
        cache = JiraCache(cache_dir=temp_cache_dir)

        # Should not raise
        cache.invalidate(key="nonexistent", category="issue")


@pytest.mark.ops
@pytest.mark.unit
class TestCacheInvalidatePattern:
    """Test invalidating keys by pattern."""

    def test_cache_invalidate_pattern_prefix(self, temp_cache_dir):
        """Test invalidating keys by prefix pattern."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", {"key": "PROJ-123"}, category="issue")
        cache.set("PROJ-456", {"key": "PROJ-456"}, category="issue")
        cache.set("OTHER-789", {"key": "OTHER-789"}, category="issue")

        cache.invalidate(pattern="PROJ-*", category="issue")

        assert cache.get("PROJ-123", category="issue") is None
        assert cache.get("PROJ-456", category="issue") is None
        assert cache.get("OTHER-789", category="issue") is not None

    def test_cache_invalidate_pattern_suffix(self, temp_cache_dir):
        """Test invalidating keys by suffix pattern."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue:PROJ-123", {"key": "PROJ-123"}, category="issue")
        cache.set("issue:OTHER-123", {"key": "OTHER-123"}, category="issue")
        cache.set("issue:PROJ-456", {"key": "PROJ-456"}, category="issue")

        cache.invalidate(pattern="*-123", category="issue")

        assert cache.get("issue:PROJ-123", category="issue") is None
        assert cache.get("issue:OTHER-123", category="issue") is None
        assert cache.get("issue:PROJ-456", category="issue") is not None


@pytest.mark.ops
@pytest.mark.unit
class TestCacheInvalidateCategory:
    """Test invalidating entire category."""

    def test_cache_invalidate_category(self, temp_cache_dir):
        """Test invalidating all keys in a category."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", {"key": "PROJ-123"}, category="issue")
        cache.set("PROJ-456", {"key": "PROJ-456"}, category="issue")
        cache.set("PROJ", {"key": "PROJ"}, category="project")

        cache.invalidate(category="issue")

        assert cache.get("PROJ-123", category="issue") is None
        assert cache.get("PROJ-456", category="issue") is None
        assert cache.get("PROJ", category="project") is not None


@pytest.mark.ops
@pytest.mark.unit
class TestCacheClearAll:
    """Test clearing entire cache."""

    def test_cache_clear_all(self, temp_cache_dir):
        """Test clearing all cache entries."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("PROJ-123", {"key": "PROJ-123"}, category="issue")
        cache.set("PROJ", {"key": "PROJ"}, category="project")
        cache.set("user1", {"name": "User"}, category="user")

        cache.clear()

        assert cache.get("PROJ-123", category="issue") is None
        assert cache.get("PROJ", category="project") is None
        assert cache.get("user1", category="user") is None


@pytest.mark.ops
@pytest.mark.unit
class TestCacheSizeLimit:
    """Test cache respects size limit."""

    def test_cache_size_limit_evicts_entries(self, temp_cache_dir):
        """Test that cache evicts entries when size limit is reached."""
        # Create cache with tiny size limit (1 KB)
        cache = JiraCache(cache_dir=temp_cache_dir, max_size_mb=0.001)

        # Add entries that exceed limit
        for i in range(100):
            cache.set(f"key{i}", {"data": "x" * 100, "index": i}, category="issue")

        stats = cache.get_stats()

        # Cache should have evicted some entries to stay under limit
        assert stats.total_size_bytes <= cache.max_size

    def test_cache_size_limit_allows_within_limit(self, temp_cache_dir):
        """Test that cache allows entries within size limit."""
        cache = JiraCache(cache_dir=temp_cache_dir, max_size_mb=10)

        # Add small entries
        for i in range(10):
            cache.set(f"key{i}", {"index": i}, category="issue")

        # All entries should be retrievable
        for i in range(10):
            assert cache.get(f"key{i}", category="issue") is not None


@pytest.mark.ops
@pytest.mark.unit
class TestCacheLRUEviction:
    """Test LRU eviction when cache is full."""

    def test_cache_lru_eviction_removes_least_recently_used(self, temp_cache_dir):
        """Test that LRU eviction removes least recently used entries."""
        # Create cache with tiny size limit
        cache = JiraCache(cache_dir=temp_cache_dir, max_size_mb=0.001)

        # Add initial entries
        cache.set("old1", {"data": "x" * 50}, category="issue")
        cache.set("old2", {"data": "x" * 50}, category="issue")

        # Access old1 to make it more recently used
        cache.get("old1", category="issue")

        # Add more entries to trigger eviction
        for i in range(50):
            cache.set(f"new{i}", {"data": "x" * 50}, category="issue")

        # old2 should be evicted first (least recently used)
        # old1 might still exist since we accessed it
        # Verify LRU eviction occurred
        # old2 should be evicted first (least recently used)
        old2_result = cache.get("old2", category="issue")
        assert old2_result is None, "old2 should have been evicted (LRU)"

        # Verify the cache is respecting size limits
        stats = cache.get_stats()
        assert stats.total_size_bytes <= cache.max_size


@pytest.mark.ops
@pytest.mark.unit
class TestCachePersistence:
    """Test cache persists across sessions."""

    def test_cache_persistence_survives_reload(self, temp_cache_dir, sample_issue_data):
        """Test that cache data persists when cache is reloaded."""
        # Create cache and add data
        cache1 = JiraCache(cache_dir=temp_cache_dir)
        cache1.set("PROJ-123", sample_issue_data, category="issue")
        cache1.close()

        # Create new cache instance (simulating new session)
        cache2 = JiraCache(cache_dir=temp_cache_dir)
        result = cache2.get("PROJ-123", category="issue")

        assert result is not None
        assert result["key"] == "PROJ-123"
        cache2.close()

    def test_cache_persistence_file_exists(self, temp_cache_dir):
        """Test that cache creates persistence file."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", {"value": "test"}, category="issue")
        cache.close()

        cache_path = Path(temp_cache_dir)
        # Should have some files in cache directory
        assert cache_path.exists()
        assert any(cache_path.iterdir())


@pytest.mark.ops
@pytest.mark.unit
class TestCacheConcurrentAccess:
    """Test thread-safe cache access."""

    def test_cache_concurrent_reads(self, temp_cache_dir, sample_issue_data):
        """Test concurrent read operations are thread-safe."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("shared_key", sample_issue_data, category="issue")

        results = []
        errors = []

        def read_cache():
            try:
                for _ in range(100):
                    result = cache.get("shared_key", category="issue")
                    if result:
                        results.append(result["key"])
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=read_cache) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(r == "PROJ-123" for r in results)

    def test_cache_concurrent_writes(self, temp_cache_dir):
        """Test concurrent write operations are thread-safe."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        errors = []

        def write_cache(thread_id):
            try:
                for i in range(50):
                    cache.set(f"key_{thread_id}_{i}", {"thread": thread_id, "index": i}, category="issue")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=write_cache, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

        # Verify some entries exist
        for thread_id in range(5):
            result = cache.get(f"key_{thread_id}_0", category="issue")
            assert result is not None

    def test_cache_concurrent_read_write(self, temp_cache_dir):
        """Test concurrent read and write operations are thread-safe."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("concurrent_key", {"value": 0}, category="issue")
        errors = []

        def reader():
            try:
                for _ in range(100):
                    cache.get("concurrent_key", category="issue")
            except Exception as e:
                errors.append(str(e))

        def writer():
            try:
                for i in range(100):
                    cache.set("concurrent_key", {"value": i}, category="issue")
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


@pytest.mark.ops
@pytest.mark.unit
class TestCacheStats:
    """Test cache statistics."""

    def test_cache_stats_entry_count(self, temp_cache_dir):
        """Test cache tracks entry count."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", {"value": 1}, category="issue")
        cache.set("key2", {"value": 2}, category="issue")
        cache.set("key3", {"value": 3}, category="project")

        stats = cache.get_stats()

        assert stats.entry_count == 3
        assert "issue" in stats.by_category
        assert "project" in stats.by_category

    def test_cache_stats_by_category(self, temp_cache_dir):
        """Test cache tracks stats by category."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("issue1", {"value": 1}, category="issue")
        cache.set("issue2", {"value": 2}, category="issue")
        cache.set("proj1", {"value": 1}, category="project")

        stats = cache.get_stats()

        assert "issue" in stats.by_category
        assert stats.by_category["issue"]["count"] == 2
        assert "project" in stats.by_category
        assert stats.by_category["project"]["count"] == 1

    def test_cache_stats_hit_rate(self, temp_cache_dir, sample_issue_data):
        """Test cache tracks hit rate."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        cache.set("key1", sample_issue_data, category="issue")

        # Generate some hits and misses
        cache.get("key1", category="issue")  # hit
        cache.get("key1", category="issue")  # hit
        cache.get("missing", category="issue")  # miss

        stats = cache.get_stats()

        # Should have ~66% hit rate (2 hits, 1 miss)
        assert stats.hits >= 2
        assert stats.misses >= 1


@pytest.mark.ops
@pytest.mark.unit
class TestCacheKeyGeneration:
    """Test cache key generation helpers."""

    def test_generate_issue_cache_key(self, temp_cache_dir):
        """Test generating cache key for issue."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        key = cache.generate_key("issue", "PROJ-123")

        assert key is not None
        assert "PROJ-123" in key

    def test_generate_search_cache_key(self, temp_cache_dir):
        """Test generating cache key for search results."""
        cache = JiraCache(cache_dir=temp_cache_dir)
        key = cache.generate_key("search", jql="project = PROJ", start_at=0, max_results=50)

        assert key is not None
        # Same params should generate same key
        key2 = cache.generate_key("search", jql="project = PROJ", start_at=0, max_results=50)
        assert key == key2

        # Different params should generate different key
        key3 = cache.generate_key("search", jql="project = PROJ", start_at=50, max_results=50)
        assert key != key3
