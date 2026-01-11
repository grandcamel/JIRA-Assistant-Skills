#!/usr/bin/env python3
"""
Get detailed automation rule configuration.

Retrieves full details of an automation rule including trigger,
conditions, actions, and connections.

Usage:
    python get_automation_rule.py RULE_ID
    python get_automation_rule.py --name "Rule Name"
    python get_automation_rule.py RULE_ID --output json
    python get_automation_rule.py RULE_ID --show-trigger
    python get_automation_rule.py RULE_ID --show-components
    python get_automation_rule.py RULE_ID
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    AutomationError,
    AutomationNotFoundError,
    JiraError,
    get_automation_client,
    print_error,
)


def get_automation_rule(
    client=None,
    rule_id: str | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """
    Get detailed automation rule configuration.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        rule_id: Rule UUID/ARI to fetch
        name: Rule name to search for (alternative to rule_id)

    Returns:
        Full rule configuration

    Raises:
        AutomationNotFoundError: If rule not found
        ValueError: If neither rule_id nor name provided
    """
    if client is None:
        client = get_automation_client()

    if not rule_id and not name:
        raise ValueError("Either rule_id or name must be provided")

    # If name provided, search for it first
    if name and not rule_id:
        # Search for rule by name
        response = client.search_rules(limit=100)
        rules = response.get("values", [])

        # Find matching rule
        matching_rules = [r for r in rules if r.get("name") == name]

        if not matching_rules:
            # Try partial match
            matching_rules = [
                r for r in rules if name.lower() in r.get("name", "").lower()
            ]

        if not matching_rules:
            raise AutomationNotFoundError("Automation rule", name)

        if len(matching_rules) > 1:
            # Multiple matches - return list of options
            names = [r.get("name") for r in matching_rules]
            raise ValueError(f"Multiple rules match '{name}': {names}")

        rule_id = matching_rules[0].get("id")

    # Fetch full rule details
    return client.get_rule(rule_id)


def format_rule_output(
    rule: dict[str, Any],
    show_trigger: bool = False,
    show_components: bool = False,
    show_all: bool = True,
) -> str:
    """Format rule for human-readable output."""
    lines = []

    lines.append("=" * 80)
    lines.append(f"Rule: {rule.get('name', 'Unnamed')}")
    lines.append("=" * 80)
    lines.append("")

    # Basic info
    lines.append(f"ID: {rule.get('id', 'N/A')}")
    lines.append(f"State: {rule.get('state', 'UNKNOWN')}")

    if rule.get("description"):
        lines.append(f"Description: {rule.get('description')}")

    # Scope
    scope_resources = rule.get("ruleScope", {}).get("resources", [])
    if scope_resources:
        lines.append(f"Scope: Project ({len(scope_resources)} project(s))")
        for resource in scope_resources[:5]:  # Limit display
            lines.append(f"  - {resource}")
    else:
        lines.append("Scope: Global")

    lines.append(f"Can Manage: {rule.get('canManage', False)}")
    lines.append(f"Created: {rule.get('created', 'N/A')}")
    lines.append(f"Updated: {rule.get('updated', 'N/A')}")

    if rule.get("authorAccountId"):
        lines.append(f"Author: {rule.get('authorAccountId')}")

    # Trigger details
    if show_trigger or show_all:
        lines.append("")
        lines.append("-" * 40)
        lines.append("Trigger")
        lines.append("-" * 40)

        trigger = rule.get("trigger", {})
        lines.append(f"Type: {trigger.get('type', 'Unknown')}")

        config = trigger.get("configuration", {})
        if config:
            lines.append("Configuration:")
            for key, value in config.items():
                lines.append(f"  {key}: {value}")

    # Components (actions/conditions)
    if show_components or show_all:
        components = rule.get("components", [])
        if components:
            lines.append("")
            lines.append("-" * 40)
            lines.append(f"Components ({len(components)})")
            lines.append("-" * 40)

            for i, comp in enumerate(components, 1):
                lines.append(f"\n{i}. {comp.get('type', 'Unknown')}")
                if comp.get("value"):
                    lines.append(f"   Value: {comp.get('value')}")
                if comp.get("children"):
                    lines.append(
                        f"   Children: {len(comp.get('children'))} nested component(s)"
                    )

    # Connections
    connections = rule.get("connections", [])
    if connections:
        lines.append("")
        lines.append("-" * 40)
        lines.append(f"Connections ({len(connections)})")
        lines.append("-" * 40)

        for conn in connections:
            lines.append(f"  - {conn}")

    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get detailed automation rule configuration",
        epilog="""
Examples:
    # Get rule by ID
    python get_automation_rule.py "ari:cloud:jira::site/12345..."

    # Get rule by name
    python get_automation_rule.py --name "Auto-assign to lead"

    # Output as JSON
    python get_automation_rule.py RULE_ID --output json

    # Show only trigger info
    python get_automation_rule.py RULE_ID --show-trigger

    # Show only components
    python get_automation_rule.py RULE_ID --show-components

    # Use specific profile
    python get_automation_rule.py RULE_ID
        """,
    )

    parser.add_argument("rule_id", nargs="?", help="Rule ID (UUID/ARI format)")
    parser.add_argument("--name", "-n", help="Rule name to search for")
    parser.add_argument(
        "--show-trigger", action="store_true", help="Show only trigger details"
    )
    parser.add_argument(
        "--show-components", action="store_true", help="Show only components"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    if not args.rule_id and not args.name:
        parser.error("Either rule_id or --name must be provided")

    try:
        rule = get_automation_rule(
            rule_id=args.rule_id, name=args.name
        )

        if args.output == "json":
            print(json.dumps(rule, indent=2))
        else:
            show_all = not (args.show_trigger or args.show_components)
            output = format_rule_output(
                rule,
                show_trigger=args.show_trigger,
                show_components=args.show_components,
                show_all=show_all,
            )
            print(output)

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
