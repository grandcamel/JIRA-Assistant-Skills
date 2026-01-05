#!/usr/bin/env python3
"""
Find blocker chain for a JIRA issue.

WHEN TO USE THIS SCRIPT:
- Sprint planning: Identify all blockers before committing to work
- Daily standups: Review blockers for current sprint issues
- Critical path analysis: Use --recursive to find full dependency chains
- Impact analysis: Use --direction outward to find issues THIS issue blocks
- Vs. link_stats.py: Use this for dependency chains; use link_stats for patterns/metrics
- Vs. get_dependencies.py: Use this for blockers only; use dependencies for visualization

Usage:
    python get_blockers.py PROJ-123
    python get_blockers.py PROJ-123 --recursive
    python get_blockers.py PROJ-123 --recursive --depth 3
    python get_blockers.py PROJ-123 --output tree
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def extract_blockers(links: list, direction: str = "inward") -> list:
    """
    Extract blocker issues from links.

    Args:
        links: List of issue links
        direction: 'inward' for issues blocking this, 'outward' for issues this blocks

    Returns:
        List of blocker issue info dicts

    Note on JIRA link semantics:
        When fetching links for issue B where "A blocks B":
        - The link has outwardIssue=A (A is on the "blocks" side)
        - The link has NO inwardIssue because B itself is the inward issue

        Therefore:
        - To find issues blocking us (inward): look for outwardIssue
        - To find issues we block (outward): look for inwardIssue
    """
    blockers = []
    for link in links:
        if link["type"]["name"] != "Blocks":
            continue

        if direction == "inward" and "outwardIssue" in link:
            # Issues that block this issue - they appear as outwardIssue
            # because this issue is on the "is blocked by" (inward) side
            issue = link["outwardIssue"]
            blockers.append(
                {
                    "key": issue["key"],
                    "summary": issue.get("fields", {}).get("summary", ""),
                    "status": issue.get("fields", {})
                    .get("status", {})
                    .get("name", "Unknown"),
                    "link_id": link["id"],
                }
            )
        elif direction == "outward" and "inwardIssue" in link:
            # Issues that this issue blocks - they appear as inwardIssue
            # because this issue is on the "blocks" (outward) side
            issue = link["inwardIssue"]
            blockers.append(
                {
                    "key": issue["key"],
                    "summary": issue.get("fields", {}).get("summary", ""),
                    "status": issue.get("fields", {})
                    .get("status", {})
                    .get("name", "Unknown"),
                    "link_id": link["id"],
                }
            )

    return blockers


def get_blockers_recursive(
    client,
    issue_key: str,
    direction: str,
    visited: set[str],
    max_depth: int,
    current_depth: int,
) -> dict[str, Any]:
    """
    Recursively get blockers.

    Args:
        client: JIRA client
        issue_key: Current issue key
        direction: 'inward' or 'outward'
        visited: Set of already visited issue keys
        max_depth: Maximum recursion depth
        current_depth: Current depth

    Returns:
        Dict with blocker tree info
    """
    if issue_key in visited:
        return {"key": issue_key, "circular": True, "blockers": []}

    if max_depth > 0 and current_depth >= max_depth:
        return {"key": issue_key, "depth_limited": True, "blockers": []}

    visited.add(issue_key)

    links = client.get_issue_links(issue_key)
    direct_blockers = extract_blockers(links, direction)

    result = {"key": issue_key, "blockers": []}

    for blocker in direct_blockers:
        blocker_info = get_blockers_recursive(
            client, blocker["key"], direction, visited, max_depth, current_depth + 1
        )
        blocker_info["summary"] = blocker["summary"]
        blocker_info["status"] = blocker["status"]
        result["blockers"].append(blocker_info)

    return result


def flatten_blockers(tree: dict[str, Any], all_blockers: list[dict], seen: set[str]):
    """Flatten blocker tree into list."""
    for blocker in tree.get("blockers", []):
        if blocker["key"] not in seen:
            seen.add(blocker["key"])
            all_blockers.append(
                {
                    "key": blocker["key"],
                    "summary": blocker.get("summary", ""),
                    "status": blocker.get("status", "Unknown"),
                    "circular": blocker.get("circular", False),
                }
            )
            flatten_blockers(blocker, all_blockers, seen)


def get_blockers(
    issue_key: str,
    direction: str = "inward",
    recursive: bool = False,
    max_depth: int = 0,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Get blockers for an issue.

    Args:
        issue_key: Issue key
        direction: 'inward' (blocking this) or 'outward' (this blocks)
        recursive: Follow blocker chain
        max_depth: Max recursion depth (0 = unlimited)
        profile: JIRA profile

    Returns:
        Dict with blockers info
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)

    try:
        if recursive:
            visited: set[str] = set()
            tree = get_blockers_recursive(
                client, issue_key, direction, visited, max_depth, 0
            )

            # Flatten for easy access
            all_blockers: list[dict] = []
            seen: set[str] = set()
            flatten_blockers(tree, all_blockers, seen)

            # Check for circular
            has_circular = any(b.get("circular", False) for b in all_blockers)

            return {
                "issue_key": issue_key,
                "direction": direction,
                "recursive": True,
                "blockers": tree.get("blockers", []),
                "all_blockers": all_blockers,
                "circular": has_circular,
                "total": len(all_blockers),
            }
        else:
            links = client.get_issue_links(issue_key)
            blockers = extract_blockers(links, direction)

            return {
                "issue_key": issue_key,
                "direction": direction,
                "recursive": False,
                "blockers": blockers,
                "total": len(blockers),
            }
    finally:
        client.close()


def format_tree(blockers: list, indent: int = 0) -> str:
    """Format blockers as tree."""
    lines = []
    prefix = "    " * indent

    for i, blocker in enumerate(blockers):
        is_last = i == len(blockers) - 1
        connector = "└── " if is_last else "├── "

        status_mark = "✓" if blocker.get("status") == "Done" else ""
        circular_mark = " [CIRCULAR]" if blocker.get("circular") else ""

        line = f"{prefix}{connector}{blocker['key']} [{blocker.get('status', '?')}] {blocker.get('summary', '')[:40]}{status_mark}{circular_mark}"
        lines.append(line)

        # Recurse for nested blockers
        if blocker.get("blockers"):
            child_lines = format_tree(blocker["blockers"], indent + 1)
            lines.append(child_lines)

    return "\n".join(lines)


def format_blockers(result: dict[str, Any], output_format: str = "text") -> str:
    """
    Format blockers for output.

    Args:
        result: Blockers result dict
        output_format: 'text', 'tree', or 'json'

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(result, indent=2)

    issue_key = result["issue_key"]
    blockers = result.get("blockers", [])
    direction = result.get("direction", "inward")

    if not blockers:
        if direction == "inward":
            return f"No issues are blocking {issue_key}"
        else:
            return f"{issue_key} is not blocking any issues"

    lines = []

    if direction == "inward":
        lines.append(f"Issues blocking {issue_key}:")
    else:
        lines.append(f"Issues blocked by {issue_key}:")

    lines.append("")

    if output_format == "tree" and result.get("recursive"):
        lines.append(format_tree(blockers))
    else:
        for blocker in blockers:
            status = blocker.get("status", "Unknown")
            summary = blocker.get("summary", "")[:50]
            status_mark = " ✓" if status == "Done" else ""
            lines.append(f"  {blocker['key']} [{status}] {summary}{status_mark}")

    lines.append("")

    # Summary
    total = result.get("total", len(blockers))
    if result.get("recursive"):
        all_blockers = result.get("all_blockers", [])
        done_count = sum(1 for b in all_blockers if b.get("status") == "Done")
        lines.append(
            f"Total: {total} blocker(s) ({done_count} resolved, {total - done_count} unresolved)"
        )

        if result.get("circular"):
            lines.append("⚠️  Circular dependency detected!")
    else:
        lines.append(f"Total: {total} direct blocker(s)")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Find blocker chain for a JIRA issue",
        epilog="Example: python get_blockers.py PROJ-123 --recursive",
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")

    parser.add_argument(
        "--direction",
        "-d",
        choices=["inward", "outward"],
        default="inward",
        help="inward=issues blocking this, outward=issues this blocks (default: inward)",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Follow blocker chain recursively",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="Maximum recursion depth (0=unlimited, default: 0)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "tree", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        result = get_blockers(
            issue_key=args.issue_key,
            direction=args.direction,
            recursive=args.recursive,
            max_depth=args.depth,
            profile=args.profile,
        )
        output = format_blockers(result, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
