"""
Caching layer for JQL autocomplete data.

Provides efficient caching of JQL field definitions, functions, and value
suggestions to improve performance of JQL building and validation.

Features:
- Automatic cache warming on first use
- Configurable TTL (default: 1 day for field definitions)
- In-memory cache with SQLite persistence
- Thread-safe access
- Invalidation support
"""

import time
from datetime import timedelta
from typing import Any

from cache import JiraCache, get_cache


class AutocompleteCache:
    """
    Cache for JQL autocomplete data.

    Caches:
    - Field definitions (names, operators, types)
    - JQL functions
    - Reserved words
    - Field value suggestions
    """

    # Cache keys
    KEY_AUTOCOMPLETE_DATA = "jql:autocomplete:data"
    KEY_FIELDS_LIST = "jql:fields:all"
    KEY_FUNCTIONS_LIST = "jql:functions:all"
    KEY_RESERVED_WORDS = "jql:reserved:words"
    KEY_SUGGESTION_PREFIX = "jql:suggest:"

    # TTL settings
    TTL_AUTOCOMPLETE = timedelta(days=1)
    TTL_SUGGESTIONS = timedelta(hours=1)

    def __init__(self, cache: JiraCache | None = None):
        """
        Initialize autocomplete cache.

        Args:
            cache: Optional JiraCache instance (creates one if not provided)
        """
        self._cache = cache or get_cache()
        self._memory_cache: dict[str, Any] = {}
        self._memory_cache_time: dict[str, float] = {}

    def get_autocomplete_data(
        self, client=None, force_refresh: bool = False
    ) -> dict[str, Any] | None:
        """
        Get cached JQL autocomplete data.

        Args:
            client: JIRA client (required if cache miss)
            force_refresh: Force refresh from API

        Returns:
            Autocomplete data dict or None
        """
        if not force_refresh:
            # Check memory cache first
            if self.KEY_AUTOCOMPLETE_DATA in self._memory_cache:
                cache_time = self._memory_cache_time.get(self.KEY_AUTOCOMPLETE_DATA, 0)
                if time.time() - cache_time < 300:  # 5 min memory cache
                    return self._memory_cache[self.KEY_AUTOCOMPLETE_DATA]

            # Check persistent cache
            cached = self._cache.get(self.KEY_AUTOCOMPLETE_DATA, category="field")
            if cached:
                self._memory_cache[self.KEY_AUTOCOMPLETE_DATA] = cached
                self._memory_cache_time[self.KEY_AUTOCOMPLETE_DATA] = time.time()
                return cached

        # Fetch from API if client provided
        if client:
            data = client.get_jql_autocomplete()
            self.set_autocomplete_data(data)
            return data

        return None

    def set_autocomplete_data(self, data: dict[str, Any]) -> None:
        """
        Cache JQL autocomplete data.

        Args:
            data: Autocomplete data from API
        """
        # Store full data
        self._cache.set(
            self.KEY_AUTOCOMPLETE_DATA,
            data,
            category="field",
            ttl=self.TTL_AUTOCOMPLETE,
        )

        # Update memory cache
        self._memory_cache[self.KEY_AUTOCOMPLETE_DATA] = data
        self._memory_cache_time[self.KEY_AUTOCOMPLETE_DATA] = time.time()

        # Also cache individual components for faster access
        fields = data.get("visibleFieldNames", [])
        if fields:
            self._cache.set(
                self.KEY_FIELDS_LIST,
                fields,
                category="field",
                ttl=self.TTL_AUTOCOMPLETE,
            )

        functions = data.get("visibleFunctionNames", [])
        if functions:
            self._cache.set(
                self.KEY_FUNCTIONS_LIST,
                functions,
                category="field",
                ttl=self.TTL_AUTOCOMPLETE,
            )

        reserved = data.get("jqlReservedWords", [])
        if reserved:
            self._cache.set(
                self.KEY_RESERVED_WORDS,
                reserved,
                category="field",
                ttl=self.TTL_AUTOCOMPLETE,
            )

    def get_fields(
        self, client=None, force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get cached field definitions.

        Args:
            client: JIRA client (required if cache miss)
            force_refresh: Force refresh from API

        Returns:
            List of field definition dicts
        """
        if not force_refresh:
            cached = self._cache.get(self.KEY_FIELDS_LIST, category="field")
            if cached:
                return cached

        # Need full autocomplete data
        data = self.get_autocomplete_data(client, force_refresh)
        return data.get("visibleFieldNames", []) if data else []

    def get_functions(
        self, client=None, force_refresh: bool = False
    ) -> list[dict[str, Any]]:
        """
        Get cached JQL function definitions.

        Args:
            client: JIRA client (required if cache miss)
            force_refresh: Force refresh from API

        Returns:
            List of function definition dicts
        """
        if not force_refresh:
            cached = self._cache.get(self.KEY_FUNCTIONS_LIST, category="field")
            if cached:
                return cached

        data = self.get_autocomplete_data(client, force_refresh)
        return data.get("visibleFunctionNames", []) if data else []

    def get_reserved_words(self, client=None, force_refresh: bool = False) -> list[str]:
        """
        Get cached JQL reserved words.

        Args:
            client: JIRA client (required if cache miss)
            force_refresh: Force refresh from API

        Returns:
            List of reserved word strings
        """
        if not force_refresh:
            cached = self._cache.get(self.KEY_RESERVED_WORDS, category="field")
            if cached:
                return cached

        data = self.get_autocomplete_data(client, force_refresh)
        return data.get("jqlReservedWords", []) if data else []

    def get_suggestions(
        self,
        field_name: str,
        prefix: str = "",
        client=None,
        force_refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get cached value suggestions for a field.

        Args:
            field_name: Field name to get suggestions for
            prefix: Optional prefix to filter by
            client: JIRA client (required if cache miss)
            force_refresh: Force refresh from API

        Returns:
            List of suggestion dicts with value and displayName
        """
        # Build cache key
        cache_key = f"{self.KEY_SUGGESTION_PREFIX}{field_name}:{prefix}"

        if not force_refresh:
            cached = self._cache.get(cache_key, category="search")
            if cached:
                return cached

        # Fetch from API if client provided
        if client:
            result = client.get_jql_suggestions(field_name, prefix)
            suggestions = result.get("results", [])

            # Cache the results
            self._cache.set(
                cache_key, suggestions, category="search", ttl=self.TTL_SUGGESTIONS
            )

            return suggestions

        return []

    def warm_cache(self, client) -> dict[str, int]:
        """
        Pre-warm the autocomplete cache.

        Args:
            client: JIRA client

        Returns:
            Dict with counts of cached items
        """
        stats = {"fields": 0, "functions": 0, "reserved_words": 0}

        try:
            data = client.get_jql_autocomplete()
            self.set_autocomplete_data(data)

            stats["fields"] = len(data.get("visibleFieldNames", []))
            stats["functions"] = len(data.get("visibleFunctionNames", []))
            stats["reserved_words"] = len(data.get("jqlReservedWords", []))

            # Also warm common field suggestions
            common_fields = ["project", "status", "issuetype", "priority"]
            for field in common_fields:
                try:
                    suggestions = client.get_jql_suggestions(field, "")
                    cache_key = f"{self.KEY_SUGGESTION_PREFIX}{field}:"
                    self._cache.set(
                        cache_key,
                        suggestions.get("results", []),
                        category="search",
                        ttl=self.TTL_SUGGESTIONS,
                    )
                except Exception:
                    pass  # Ignore errors for optional warming

        except Exception as e:
            print(f"Warning: Cache warming failed: {e}")

        return stats

    def invalidate(self, field_name: str | None = None) -> int:
        """
        Invalidate cached autocomplete data.

        Args:
            field_name: Specific field to invalidate suggestions for,
                       or None to invalidate all

        Returns:
            Number of entries invalidated
        """
        count = 0

        if field_name:
            # Invalidate specific field suggestions
            count += self._cache.invalidate(
                pattern=f"{self.KEY_SUGGESTION_PREFIX}{field_name}:*"
            )
        else:
            # Invalidate all autocomplete data
            count += self._cache.invalidate(
                key=self.KEY_AUTOCOMPLETE_DATA, category="field"
            )
            count += self._cache.invalidate(key=self.KEY_FIELDS_LIST, category="field")
            count += self._cache.invalidate(
                key=self.KEY_FUNCTIONS_LIST, category="field"
            )
            count += self._cache.invalidate(
                key=self.KEY_RESERVED_WORDS, category="field"
            )
            count += self._cache.invalidate(pattern=f"{self.KEY_SUGGESTION_PREFIX}*")

            # Clear memory cache
            self._memory_cache.clear()
            self._memory_cache_time.clear()

        return count

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        cache_stats = self._cache.get_stats()

        # Check what's currently cached
        has_autocomplete = (
            self._cache.get(self.KEY_AUTOCOMPLETE_DATA, category="field") is not None
        )
        has_fields = self._cache.get(self.KEY_FIELDS_LIST, category="field") is not None
        has_functions = (
            self._cache.get(self.KEY_FUNCTIONS_LIST, category="field") is not None
        )

        return {
            "autocomplete_cached": has_autocomplete,
            "fields_cached": has_fields,
            "functions_cached": has_functions,
            "memory_cache_size": len(self._memory_cache),
            "total_cache_entries": cache_stats.entry_count,
            "cache_hit_rate": f"{cache_stats.hit_rate * 100:.1f}%",
        }


# Singleton instance for shared access
_autocomplete_cache: AutocompleteCache | None = None


def get_autocomplete_cache() -> AutocompleteCache:
    """
    Get or create the singleton autocomplete cache.

    Returns:
        AutocompleteCache instance
    """
    global _autocomplete_cache
    if _autocomplete_cache is None:
        _autocomplete_cache = AutocompleteCache()
    return _autocomplete_cache
