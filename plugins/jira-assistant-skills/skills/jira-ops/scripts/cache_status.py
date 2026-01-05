#!/usr/bin/env python3
"""
Display JIRA cache statistics and status.

Shows cache size, entry counts, hit rates, and breakdown by category.

Usage:
    python cache_status.py
    python cache_status.py --json
    python cache_status.py --profile production

Output:
    Cache Statistics:
      Total Size: 12.5 MB / 100 MB
      Entries: 1,234
      Hit Rate: 78%

    By Category:
      issue: 800 entries, 8 MB
      project: 50 entries, 1 MB
      user: 200 entries, 2 MB
      field: 184 entries, 1.5 MB
"""

import argparse
import json
import sys
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(
    Path(__file__).parent.parent.parent / "shared" / "scripts" / "lib"
)
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import JiraCache


def format_bytes(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Display JIRA cache statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python cache_status.py              # Show cache status
    python cache_status.py --json       # Output as JSON
        """,
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="JIRA profile (for future multi-profile cache support)",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=None, help="Custom cache directory"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args(argv)

    try:
        cache = JiraCache(cache_dir=args.cache_dir)
        stats = cache.get_stats()

        if args.json:
            output = {
                "total_size_bytes": stats.total_size_bytes,
                "max_size_bytes": cache.max_size,
                "entry_count": stats.entry_count,
                "hits": stats.hits,
                "misses": stats.misses,
                "hit_rate": stats.hit_rate,
                "by_category": stats.by_category,
            }
            print(json.dumps(output, indent=2))
        else:
            print("\nCache Statistics:")
            print(
                f"  Total Size: {format_bytes(stats.total_size_bytes)} / {format_bytes(cache.max_size)}"
            )
            print(f"  Entries: {stats.entry_count:,}")

            if stats.hits + stats.misses > 0:
                print(
                    f"  Hit Rate: {stats.hit_rate * 100:.1f}% ({stats.hits:,} hits, {stats.misses:,} misses)"
                )
            else:
                print("  Hit Rate: N/A (no requests)")

            if stats.by_category:
                print("\nBy Category:")
                for category, cat_stats in sorted(stats.by_category.items()):
                    print(
                        f"  {category}: {cat_stats['count']:,} entries, {format_bytes(cat_stats['size_bytes'])}"
                    )
            else:
                print("\nNo cached entries.")

            print()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
