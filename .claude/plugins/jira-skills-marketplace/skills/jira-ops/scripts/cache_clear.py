#!/usr/bin/env python3
"""
Clear JIRA cache entries.

Supports clearing entire cache, specific categories, or pattern-based clearing.

Usage:
    python cache_clear.py                    # Clear all cache
    python cache_clear.py --category issue   # Clear issue category
    python cache_clear.py --pattern "PROJ-*" # Clear keys matching pattern
    python cache_clear.py --dry-run          # Show what would be cleared

Examples:
    # Clear all cached data
    python cache_clear.py

    # Clear only issue cache (project/field caches remain)
    python cache_clear.py --category issue

    # Clear all entries for a specific project
    python cache_clear.py --pattern "PROJ-*" --category issue
"""

import argparse
import sys
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(Path(__file__).parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from cache import JiraCache


def main():
    parser = argparse.ArgumentParser(
        description="Clear JIRA cache entries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python cache_clear.py                    # Clear all cache
    python cache_clear.py --category issue   # Clear issue category
    python cache_clear.py --pattern "PROJ-*" # Clear keys matching pattern
        """
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=["issue", "project", "user", "field", "search", "default"],
        help="Clear only entries in this category"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Clear keys matching glob pattern (e.g., 'PROJ-*')"
    )
    parser.add_argument(
        "--key",
        type=str,
        help="Clear specific cache key"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleared without actually clearing"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        help="Custom cache directory"
    )

    args = parser.parse_args()

    try:
        cache = JiraCache(cache_dir=args.cache_dir)
        stats_before = cache.get_stats()

        # Describe what will be cleared
        if args.key:
            if args.category:
                description = f"key '{args.key}' in category '{args.category}'"
            else:
                print("Error: --key requires --category", file=sys.stderr)
                sys.exit(1)
        elif args.pattern:
            if args.category:
                description = f"keys matching '{args.pattern}' in category '{args.category}'"
            else:
                description = f"keys matching '{args.pattern}' in all categories"
        elif args.category:
            description = f"all entries in category '{args.category}'"
        else:
            description = "all cache entries"

        if args.dry_run:
            print(f"DRY RUN: Would clear {description}")
            print(f"  Current entries: {stats_before.entry_count:,}")
            print(f"  Current size: {stats_before.total_size_bytes / (1024*1024):.1f} MB")
            return

        # Confirm unless --force
        if not args.force:
            confirm = input(f"Clear {description}? [y/N] ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Cancelled.")
                return

        # Perform clear operation
        if args.key:
            count = cache.invalidate(key=args.key, category=args.category)
        elif args.pattern:
            count = cache.invalidate(pattern=args.pattern, category=args.category)
        elif args.category:
            count = cache.invalidate(category=args.category)
        else:
            count = cache.clear()

        print(f"Cleared {count:,} cache entries.")

        stats_after = cache.get_stats()
        freed = stats_before.total_size_bytes - stats_after.total_size_bytes
        print(f"Freed {freed / (1024*1024):.1f} MB")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
