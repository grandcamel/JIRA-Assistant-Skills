#!/usr/bin/env python3
"""
Invoke a manual automation rule.

Triggers a manual automation rule on a specific issue.

Usage:
    python invoke_manual_rule.py RULE_ID --issue PROJ-123
    python invoke_manual_rule.py RULE_ID --issue PROJ-123 --property '{"key": "value"}'
    python invoke_manual_rule.py RULE_ID --issue PROJ-123 --dry-run
    python invoke_manual_rule.py RULE_ID --context-file context.json
    python invoke_manual_rule.py RULE_ID --issue PROJ-123
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


def invoke_manual_rule(
    client=None,
    rule_id: str | None = None,
    issue_key: str | None = None,
    context: dict[str, Any] | None = None,
    properties: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Invoke a manual automation rule.

    Args:
        client: AutomationClient instance (optional, created if not provided)
        rule_id: Rule ID (not UUID)
        issue_key: Issue key to run rule on
        context: Full context object (alternative to issue_key)
        properties: Optional input properties for the rule
        dry_run: If True, preview without invoking

    Returns:
        Invocation result

    Raises:
        ValueError: If neither issue_key nor context provided
    """
    if client is None:
        client = get_automation_client()

    if not rule_id:
        raise ValueError("rule_id is required")

    # Build context from issue_key if not provided
    if context is None:
        if issue_key:
            context = {"issue": {"key": issue_key}}
        else:
            raise ValueError("Either issue_key or context must be provided")

    if dry_run:
        return {
            "dry_run": True,
            "would_invoke": True,
            "rule_id": rule_id,
            "context": context,
            "properties": properties,
        }

    # Invoke the rule
    return client.invoke_manual_rule(
        rule_id=rule_id, context=context, properties=properties
    )


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Invoke a manual automation rule",
        epilog="""
Examples:
    # Invoke rule on an issue
    python invoke_manual_rule.py 12345 --issue PROJ-123

    # With custom properties
    python invoke_manual_rule.py 12345 --issue PROJ-123 \\
      --property '{"priority": "High", "assignee": "john@example.com"}'

    # Preview without invoking
    python invoke_manual_rule.py 12345 --issue PROJ-123 --dry-run

    # From JSON context file
    python invoke_manual_rule.py 12345 --context-file context.json

    # Output as JSON
    python invoke_manual_rule.py 12345 --issue PROJ-123 --output json

    # Use specific profile
    python invoke_manual_rule.py 12345 --issue PROJ-123
        """,
    )

    parser.add_argument("rule_id", help="Rule ID")
    parser.add_argument(
        "--issue", "-i", dest="issue_key", help="Issue key to run rule on"
    )
    parser.add_argument("--context-file", "-f", help="JSON file with context object")
    parser.add_argument(
        "--property", "-p", dest="properties_json", help="Properties as JSON string"
    )
    parser.add_argument(
        "--dry-run", "-d", action="store_true", help="Preview without invoking"
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    # Must have either issue key or context file
    if not args.issue_key and not args.context_file:
        parser.error("Either --issue or --context-file must be provided")

    try:
        # Load context from file if provided
        context = None
        if args.context_file:
            with open(args.context_file) as f:
                context = json.load(f)

        # Parse properties JSON
        properties = None
        if args.properties_json:
            properties = json.loads(args.properties_json)

        result = invoke_manual_rule(
            rule_id=args.rule_id,
            issue_key=args.issue_key,
            context=context,
            properties=properties,
            dry_run=args.dry_run,
        )

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            if args.dry_run:
                print("\n[DRY RUN] Would invoke rule:")
                print(f"  Rule ID: {result.get('rule_id')}")
                print(f"  Context: {json.dumps(result.get('context'), indent=4)}")
                if result.get("properties"):
                    print(
                        f"  Properties: {json.dumps(result.get('properties'), indent=4)}"
                    )
            else:
                print("\nRule Invocation")
                print("=" * 40)
                print(f"Status: {result.get('status', 'completed')}")
                if result.get("message"):
                    print(f"Message: {result.get('message')}")
                print("\nSuccess: Manual rule has been invoked.")

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
