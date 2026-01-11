#!/usr/bin/env python3
"""
Analyze link statistics for JIRA issues.

WHEN TO USE THIS SCRIPT:
- Dependency audits: Review linking patterns across a project
- Find orphans: Identify issues with no links (--project PROJ)
- Find hubs/bottlenecks: Identify most-connected issues (--top 10)
- Process metrics: Generate link distribution stats for retrospectives
- Health checks: Single issue link breakdown (PROJ-123)
- Vs. get_blockers.py: Use this for patterns/metrics; use blockers for dependency chains
- Vs. get_dependencies.py: Use this for statistics; use dependencies for visualization

Usage:
    python link_stats.py PROJ-123
    python link_stats.py --project PROJ
    python link_stats.py --jql "project = PROJ AND type = Epic"
    python link_stats.py --project PROJ --top 10
"""

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    validate_issue_key,
    validate_jql,
)


def get_issue_link_stats(issue_key: str) -> dict[str, Any]:
    """
    Get link statistics for a single issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)

    Returns:
        Dict with link stats for the issue
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        links = client.get_issue_links(issue_key)
    finally:
        client.close()

    stats = {
        "issue_key": issue_key,
        "total_links": len(links),
        "by_type": defaultdict(int),
        "by_direction": {"inward": 0, "outward": 0},
        "linked_issues": [],
        "by_status": defaultdict(int),
    }

    for link in links:
        link_type = link["type"]["name"]
        stats["by_type"][link_type] += 1

        if "outwardIssue" in link:
            stats["by_direction"]["inward"] += 1
            issue = link["outwardIssue"]
        else:
            stats["by_direction"]["outward"] += 1
            issue = link["inwardIssue"]

        status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        stats["by_status"][status] += 1
        stats["linked_issues"].append(
            {"key": issue["key"], "status": status, "link_type": link_type}
        )

    # Convert defaultdicts to regular dicts for JSON serialization
    stats["by_type"] = dict(stats["by_type"])
    stats["by_status"] = dict(stats["by_status"])

    return stats


def get_project_link_stats(jql: str, max_results: int = 500) -> dict[str, Any]:
    """
    Get link statistics for issues matching a JQL query.

    Args:
        jql: JQL query to find issues
        max_results: Maximum issues to analyze

    Returns:
        Dict with aggregate link stats
    """
    jql = validate_jql(jql)

    client = get_jira_client()

    # Search for issues
    results = client.search_issues(
        jql, fields=["key", "summary", "issuelinks", "status"], max_results=max_results
    )

    issues = results.get("issues", [])
    total_issues = results.get("total", 0)

    stats = {
        "jql": jql,
        "issues_analyzed": len(issues),
        "total_matching": total_issues,
        "total_links": 0,
        "by_type": defaultdict(int),
        "by_direction": {"inward": 0, "outward": 0},
        "orphaned_count": 0,
        "orphaned_issues": [],
        "most_connected": [],
        "by_status": defaultdict(int),
    }

    issue_link_counts = []

    for issue in issues:
        issue_key = issue["key"]
        links = issue.get("fields", {}).get("issuelinks", [])
        link_count = len(links)

        stats["total_links"] += link_count

        if link_count == 0:
            stats["orphaned_count"] += 1
            stats["orphaned_issues"].append(
                {
                    "key": issue_key,
                    "summary": issue.get("fields", {}).get("summary", "")[:50],
                }
            )
        else:
            issue_link_counts.append(
                {
                    "key": issue_key,
                    "summary": issue.get("fields", {}).get("summary", "")[:50],
                    "link_count": link_count,
                }
            )

        for link in links:
            link_type = link["type"]["name"]
            stats["by_type"][link_type] += 1

            if "outwardIssue" in link:
                stats["by_direction"]["inward"] += 1
                linked_issue = link["outwardIssue"]
            else:
                stats["by_direction"]["outward"] += 1
                linked_issue = link["inwardIssue"]

            status = (
                linked_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
            )
            stats["by_status"][status] += 1

    # Sort by link count descending
    issue_link_counts.sort(key=lambda x: x["link_count"], reverse=True)
    stats["most_connected"] = issue_link_counts[:20]

    # Convert defaultdicts
    stats["by_type"] = dict(stats["by_type"])
    stats["by_status"] = dict(stats["by_status"])

    client.close()
    return stats


def format_single_issue_stats(stats: dict[str, Any]) -> str:
    """Format stats for a single issue."""
    lines = []
    lines.append(f"Link Statistics for {stats['issue_key']}")
    lines.append("=" * 40)
    lines.append("")

    lines.append(f"Total Links: {stats['total_links']}")
    lines.append(f"  Outward (this issue links to): {stats['by_direction']['outward']}")
    lines.append(f"  Inward (linked to this issue): {stats['by_direction']['inward']}")
    lines.append("")

    if stats["by_type"]:
        lines.append("By Link Type:")
        for link_type, count in sorted(stats["by_type"].items()):
            lines.append(f"  {link_type}: {count}")
        lines.append("")

    if stats["by_status"]:
        lines.append("Linked Issues by Status:")
        for status, count in sorted(stats["by_status"].items()):
            lines.append(f"  {status}: {count}")
        lines.append("")

    if stats["linked_issues"]:
        lines.append("Linked Issues:")
        for linked in stats["linked_issues"]:
            lines.append(
                f"  {linked['key']} [{linked['status']}] ({linked['link_type']})"
            )

    return "\n".join(lines)


def format_project_stats(stats: dict[str, Any], top: int = 10) -> str:
    """Format stats for multiple issues."""
    lines = []
    lines.append("Link Statistics Report")
    lines.append("=" * 50)
    lines.append("")

    lines.append(f"Query: {stats['jql']}")
    lines.append(
        f"Issues Analyzed: {stats['issues_analyzed']} of {stats['total_matching']}"
    )
    lines.append(f"Total Links: {stats['total_links']}")
    lines.append("")

    # Direction breakdown
    lines.append("Link Direction:")
    lines.append(f"  Outward: {stats['by_direction']['outward']}")
    lines.append(f"  Inward: {stats['by_direction']['inward']}")
    lines.append("")

    # By type
    if stats["by_type"]:
        lines.append("Links by Type:")
        for link_type, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
            lines.append(f"  {link_type}: {count}")
        lines.append("")

    # Orphaned issues
    lines.append(f"Orphaned Issues (no links): {stats['orphaned_count']}")
    if stats["orphaned_issues"][:5]:
        for orphan in stats["orphaned_issues"][:5]:
            lines.append(f"  {orphan['key']}: {orphan['summary']}")
        if stats["orphaned_count"] > 5:
            lines.append(f"  ... and {stats['orphaned_count'] - 5} more")
    lines.append("")

    # Most connected
    if stats["most_connected"]:
        lines.append(
            f"Most Connected Issues (top {min(top, len(stats['most_connected']))}):"
        )
        for issue in stats["most_connected"][:top]:
            lines.append(
                f"  {issue['key']} ({issue['link_count']} links): {issue['summary']}"
            )
        lines.append("")

    # By status
    if stats["by_status"]:
        lines.append("Linked Issues by Status:")
        for status, count in sorted(stats["by_status"].items(), key=lambda x: -x[1]):
            lines.append(f"  {status}: {count}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Analyze link statistics for JIRA issues",
        epilog="""
Examples:
  %(prog)s PROJ-123
  %(prog)s --project PROJ
  %(prog)s --jql "project = PROJ AND type = Epic"
  %(prog)s --project PROJ --top 10
  %(prog)s --project PROJ --output json
        """,
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "issue_key", nargs="?", help="Single issue key (e.g., PROJ-123)"
    )
    input_group.add_argument(
        "--project", "-p", help="Project key to analyze all issues"
    )
    input_group.add_argument("--jql", "-j", help="JQL query to find issues to analyze")

    parser.add_argument(
        "--top",
        "-t",
        type=int,
        default=10,
        help="Number of most-connected issues to show (default: 10)",
    )
    parser.add_argument(
        "--max-results",
        "-m",
        type=int,
        default=500,
        help="Maximum issues to analyze for project/JQL (default: 500)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        if args.issue_key:
            # Single issue stats
            stats = get_issue_link_stats(args.issue_key)

            if args.output == "json":
                print(json.dumps(stats, indent=2))
            else:
                print(format_single_issue_stats(stats))

        else:
            # Project or JQL stats
            if args.project:
                jql = f"project = {args.project}"
            else:
                jql = args.jql

            stats = get_project_link_stats(jql, max_results=args.max_results)

            if args.output == "json":
                print(json.dumps(stats, indent=2))
            else:
                print(format_project_stats(stats, top=args.top))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
