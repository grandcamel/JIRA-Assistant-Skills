#!/usr/bin/env python3
"""
Update an automation rule configuration.

Updates an existing automation rule's name, description, or configuration.

Usage:
    python update_automation_rule.py RULE_ID --name "New Rule Name"
    python update_automation_rule.py RULE_ID --description "Updated description"
    python update_automation_rule.py RULE_ID --config updated_rule.json
    python update_automation_rule.py RULE_ID --config updated_rule.json --dry-run
    python update_automation_rule.py RULE_ID --name "New Name" --profile development
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    AutomationError,
    JiraError,
    get_automation_client,
    print_error,
)


def update_automation_rule(
    client=None,
    rule_id: str | None = None,
    name: str | None = None,
    description: str | None = None,
    config: dict[str, Any] | None = None,
    dry_run: bool = False,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Update an automation rule configuration.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        rule_id: Rule UUID/ARI to update
        name: New rule name
        description: New description
        config: Full configuration object
        dry_run: If True, preview without updating
        profile: JIRA profile to use

    Returns:
        Updated rule data or dry-run preview

    Raises:
        ValueError: If rule_id not provided or no updates specified
    """
    if client is None:
        client = get_automation_client(profile)

    if not rule_id:
        raise ValueError("rule_id is required")

    # Build update config
    rule_config = config or {}
    if name:
        rule_config["name"] = name
    if description:
        rule_config["description"] = description

    if not rule_config:
        raise ValueError(
            "At least one update (--name, --description, or --config) must be provided"
        )

    if dry_run:
        # Get current rule for preview
        current_rule = client.get_rule(rule_id)
        return {
            "dry_run": True,
            "would_update": True,
            "rule_id": rule_id,
            "current_name": current_rule.get("name"),
            "current_description": current_rule.get("description"),
            "updates": rule_config,
        }

    # Update the rule
    return client.update_rule(rule_id, rule_config=rule_config)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Update an automation rule configuration",
        epilog="""
Examples:
    # Update rule name
    python update_automation_rule.py RULE_ID --name "New Rule Name"

    # Update description
    python update_automation_rule.py RULE_ID --description "Updated description"

    # Update multiple fields
    python update_automation_rule.py RULE_ID --name "New Name" --description "New desc"

    # Update from JSON config file
    python update_automation_rule.py RULE_ID --config updated_rule.json

    # Preview without updating
    python update_automation_rule.py RULE_ID --name "New Name" --dry-run

    # Output as JSON
    python update_automation_rule.py RULE_ID --name "New Name" --output json

    # Use specific profile
    python update_automation_rule.py RULE_ID --name "New Name" --profile development
        """,
    )

    parser.add_argument("rule_id", help="Rule ID (UUID/ARI format)")
    parser.add_argument("--name", "-n", help="New rule name")
    parser.add_argument("--description", "-d", dest="desc", help="New description")
    parser.add_argument("--config", "-f", help="JSON config file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without updating"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    # Must have at least one update
    if not any([args.name, args.desc, args.config]):
        parser.error(
            "At least one update (--name, --description, or --config) must be provided"
        )

    try:
        # Load config from file if provided
        config = None
        if args.config:
            with open(args.config) as f:
                config = json.load(f)

        result = update_automation_rule(
            rule_id=args.rule_id,
            name=args.name,
            description=args.desc,
            config=config,
            dry_run=args.dry_run,
            profile=args.profile,
        )

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            if args.dry_run:
                print("\n[DRY RUN] Would update rule:")
                print(f"  Rule ID: {result.get('rule_id')}")
                print(f"  Current Name: {result.get('current_name')}")
                print(f"  Updates: {json.dumps(result.get('updates'), indent=4)}")
            else:
                print("\nRule Updated")
                print("=" * 40)
                print(f"Rule ID: {result.get('id')}")
                print(f"Name: {result.get('name')}")
                if result.get("description"):
                    print(f"Description: {result.get('description')}")
                print("\nSuccess: Rule has been updated.")

    except json.JSONDecodeError as e:
        print(f"\nError: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nError: File not found - {e}", file=sys.stderr)
        sys.exit(1)
    except (JiraError, AutomationError) as e:
        print_error(e)
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
