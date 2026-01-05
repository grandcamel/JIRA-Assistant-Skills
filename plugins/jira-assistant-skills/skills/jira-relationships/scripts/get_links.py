#!/usr/bin/env python3
"""
View issue links for a JIRA issue.

Usage:
    python get_links.py PROJ-123
    python get_links.py PROJ-123 --inward
    python get_links.py PROJ-123 --type blocks
    python get_links.py PROJ-123 --output json
"""

import argparse
import json
import sys

from jira_assistant_skills_lib import (
    JiraError,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def get_links(
    issue_key: str,
    direction: str | None = None,
    link_type: str | None = None,
    profile: str | None = None,
) -> list:
    """
    Get links for an issue.

    Args:
        issue_key: Issue key (e.g., PROJ-123)
        direction: Filter by 'inward' or 'outward'
        link_type: Filter by link type name
        profile: JIRA profile to use

    Returns:
        List of issue links
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)
    try:
        links = client.get_issue_links(issue_key)
    finally:
        client.close()

    # Filter by direction
    # When 'inwardIssue' is in the response, the queried issue is the OUTWARD one
    # When 'outwardIssue' is in the response, the queried issue is the INWARD one
    if direction == "outward":
        # Keep links where queried issue is outward (other issue is inward)
        links = [l for l in links if "inwardIssue" in l]
    elif direction == "inward":
        # Keep links where queried issue is inward (other issue is outward)
        links = [l for l in links if "outwardIssue" in l]

    # Filter by link type
    if link_type:
        type_lower = link_type.lower()
        links = [l for l in links if l["type"]["name"].lower() == type_lower]

    return links


def format_links(links: list, issue_key: str, output_format: str = "text") -> str:
    """
    Format links for output.

    Args:
        links: List of link objects
        issue_key: The issue being queried
        output_format: 'text' or 'json'

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(links, indent=2)

    if not links:
        return f"No links found for {issue_key}"

    lines = []
    lines.append(f"Links for {issue_key}:")
    lines.append("")

    # Separate into outward and inward based on queried issue's role
    # When 'inwardIssue' is present, the queried issue is the OUTWARD one (blocks, duplicates, etc.)
    # When 'outwardIssue' is present, the queried issue is the INWARD one (is blocked by, etc.)
    outward_links = [l for l in links if "inwardIssue" in l]
    inward_links = [l for l in links if "outwardIssue" in l]

    if outward_links:
        lines.append("Outward (this issue...):")
        for link in outward_links:
            link_type = link["type"]
            # For outward links, the OTHER issue is the inwardIssue (the one being affected)
            target = link["inwardIssue"]
            status = target.get("fields", {}).get("status", {}).get("name", "Unknown")
            summary = target.get("fields", {}).get("summary", "")
            # Truncate summary
            if len(summary) > 50:
                summary = summary[:47] + "..."
            lines.append(
                f"  {link_type['outward']} -> {target['key']} [{status}] {summary}"
            )
        lines.append("")

    if inward_links:
        lines.append("Inward (...this issue):")
        for link in inward_links:
            link_type = link["type"]
            # For inward links, the OTHER issue is the outwardIssue (the one doing the action)
            source = link["outwardIssue"]
            status = source.get("fields", {}).get("status", {}).get("name", "Unknown")
            summary = source.get("fields", {}).get("summary", "")
            # Truncate summary
            if len(summary) > 50:
                summary = summary[:47] + "..."
            lines.append(
                f"  {link_type['inward']} <- {source['key']} [{status}] {summary}"
            )
        lines.append("")

    lines.append(f"Total: {len(links)} link(s)")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="View issue links for a JIRA issue",
        epilog="Example: python get_links.py PROJ-123 --type blocks",
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")

    direction_group = parser.add_mutually_exclusive_group()
    direction_group.add_argument(
        "--inward",
        action="store_const",
        const="inward",
        dest="direction",
        help="Show only inward links (issues that link TO this one)",
    )
    direction_group.add_argument(
        "--outward",
        action="store_const",
        const="outward",
        dest="direction",
        help="Show only outward links (issues this one links TO)",
    )

    parser.add_argument(
        "--type",
        "-t",
        dest="link_type",
        help="Filter by link type (e.g., blocks, duplicate)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        links = get_links(
            issue_key=args.issue_key,
            direction=args.direction,
            link_type=args.link_type,
            profile=args.profile,
        )
        output = format_links(links, args.issue_key, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
