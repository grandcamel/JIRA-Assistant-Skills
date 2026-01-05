#!/usr/bin/env python3
"""
Bulk link multiple issues to a target issue.

WHEN TO USE THIS SCRIPT:
- Shared dependencies: Many issues blocked by one platform upgrade
- Release tracking: Link all issues in a version to release issue
- Cross-team coordination: Link multiple teams' issues to shared blocker
- Retrospective prep: Link all sprint issues to retrospective

STRATEGIES:
- --jql: Find issues dynamically (e.g., fixVersion, sprint, labels)
- --issues: Explicit list for known issues
- --dry-run: Preview before creating links
- --skip-existing: Avoid duplicating links

Usage:
    python bulk_link.py --issues PROJ-1,PROJ-2,PROJ-3 --blocks PROJ-100
    python bulk_link.py --jql "project=PROJ AND fixVersion=1.0" --relates-to PROJ-RELEASE
    python bulk_link.py --issues PROJ-1,PROJ-2 --blocks PROJ-100 --dry-run
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    AuthenticationError,
    JiraError,
    PermissionError,
    get_jira_client,
    print_error,
    validate_issue_key,
)


def bulk_link(
    issues: list[str] | None = None,
    jql: str | None = None,
    target: str | None = None,
    link_type: str | None = None,
    dry_run: bool = False,
    skip_existing: bool = False,
    show_progress: bool = False,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Bulk link multiple issues to a target.

    Args:
        issues: List of issue keys to link
        jql: JQL query to find issues to link
        target: Target issue key
        link_type: Link type name (e.g., 'Blocks', 'Relates')
        dry_run: If True, don't create links, just report what would be done
        skip_existing: If True, skip issues already linked to target
        show_progress: If True, track progress
        profile: JIRA profile

    Returns:
        Dict with operation results
    """
    target = validate_issue_key(target)

    client = get_jira_client(profile)

    try:
        # Get issues from JQL if specified
        if jql and not issues:
            results = client.search_issues(jql, fields=["key"], max_results=100)
            issues = [issue["key"] for issue in results.get("issues", [])]

        if not issues:
            return {
                "target": target,
                "link_type": link_type,
                "created": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [],
                "dry_run": dry_run,
            }

        # Validate issue keys
        issues = [validate_issue_key(key) for key in issues]

        # Handle dry run
        if dry_run:
            return {
                "target": target,
                "link_type": link_type,
                "issues": issues,
                "dry_run": True,
                "would_create": len(issues),
            }

        # Check for existing links if skip_existing is enabled
        existing_targets = set()
        if skip_existing:
            for issue_key in issues:
                links = client.get_issue_links(issue_key)
                for link in links:
                    if (
                        "outwardIssue" in link and link["outwardIssue"]["key"] == target
                    ) or (
                        "inwardIssue" in link and link["inwardIssue"]["key"] == target
                    ):
                        existing_targets.add(issue_key)

        # Create links
        created = 0
        failed = 0
        skipped = 0
        errors = []
        progress = []

        for _i, issue_key in enumerate(issues):
            if issue_key in existing_targets:
                skipped += 1
                progress.append({"issue": issue_key, "status": "skipped"})
                continue

            try:
                client.create_link(link_type, issue_key, target)
                created += 1
                progress.append({"issue": issue_key, "status": "created"})
            except (JiraError, AuthenticationError, PermissionError) as e:
                failed += 1
                errors.append(f"{issue_key}: {e!s}")
                progress.append(
                    {"issue": issue_key, "status": "failed", "error": str(e)}
                )

        result = {
            "target": target,
            "link_type": link_type,
            "created": created,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "dry_run": False,
        }

        if show_progress:
            result["progress"] = progress

        return result

    finally:
        client.close()


def format_bulk_result(result: dict[str, Any], output_format: str = "text") -> str:
    """
    Format bulk link result for output.

    Args:
        result: Bulk link result dict
        output_format: 'text' or 'json'

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(result, indent=2)

    lines = []

    target = result.get("target", "Unknown")
    link_type = result.get("link_type", "Unknown")

    if result.get("dry_run"):
        lines.append(f"DRY RUN - Would create {result.get('would_create', 0)} links:")
        lines.append(f"  Target: {target}")
        lines.append(f"  Link type: {link_type}")
        issues = result.get("issues", [])
        for issue in issues[:10]:  # Show first 10
            lines.append(f"    {issue} -> {target}")
        if len(issues) > 10:
            lines.append(f"    ... and {len(issues) - 10} more")
    else:
        lines.append(f"Bulk link to {target} ({link_type}):")
        lines.append(f"  Created: {result.get('created', 0)}")
        lines.append(f"  Skipped: {result.get('skipped', 0)}")
        lines.append(f"  Failed:  {result.get('failed', 0)}")

        errors = result.get("errors", [])
        if errors:
            lines.append("")
            lines.append("Errors:")
            for error in errors:
                lines.append(f"  {error}")

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Bulk link multiple issues to a target",
        epilog="Example: python bulk_link.py --issues PROJ-1,PROJ-2 --blocks PROJ-100",
    )

    # Issue sources (mutually exclusive in practice)
    source_group = parser.add_argument_group("Issue sources (choose one)")
    source_group.add_argument(
        "--issues", "-i", help="Comma-separated list of issue keys"
    )
    source_group.add_argument("--jql", "-j", help="JQL query to find issues to link")

    # Link type (semantic flags)
    link_group = parser.add_argument_group("Link type (choose one)")
    link_group.add_argument("--blocks", metavar="TARGET", help="Issues block TARGET")
    link_group.add_argument(
        "--is-blocked-by", metavar="TARGET", help="Issues are blocked by TARGET"
    )
    link_group.add_argument(
        "--relates-to", metavar="TARGET", help="Issues relate to TARGET"
    )
    link_group.add_argument(
        "--duplicates", metavar="TARGET", help="Issues duplicate TARGET"
    )
    link_group.add_argument("--clones", metavar="TARGET", help="Issues clone TARGET")
    link_group.add_argument("--type", dest="link_type", help="Custom link type name")
    link_group.add_argument(
        "--to", metavar="TARGET", help="Target issue (use with --type)"
    )

    # Options
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without creating links"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip issues already linked to target",
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

    # Determine target and link type from semantic flags
    target = None
    link_type = None

    if args.blocks:
        target = args.blocks
        link_type = "Blocks"
    elif args.is_blocked_by:
        target = args.is_blocked_by
        link_type = "Blocks"
        # Note: for is-blocked-by, we swap direction in create_link call
    elif args.relates_to:
        target = args.relates_to
        link_type = "Relates"
    elif args.duplicates:
        target = args.duplicates
        link_type = "Duplicate"
    elif args.clones:
        target = args.clones
        link_type = "Cloners"
    elif args.link_type and args.to:
        link_type = args.link_type
        target = args.to
    else:
        parser.error(
            "Must specify a link type (--blocks, --relates-to, etc.) or --type with --to"
        )

    # Get issues
    issues = None
    if args.issues:
        issues = [k.strip() for k in args.issues.split(",")]

    if not issues and not args.jql:
        parser.error("Must specify --issues or --jql")

    try:
        result = bulk_link(
            issues=issues,
            jql=args.jql,
            target=target,
            link_type=link_type,
            dry_run=args.dry_run,
            skip_existing=args.skip_existing,
            show_progress=False,
            profile=args.profile,
        )

        output = format_bulk_result(result, output_format=args.output)
        print(output)

        # Exit with error if any failed
        if result.get("failed", 0) > 0:
            sys.exit(1)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
