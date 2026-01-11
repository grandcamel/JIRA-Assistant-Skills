#!/usr/bin/env python3
"""
Get detailed workflow information.

Retrieves workflow details including statuses, transitions, rules, and scheme usage.
Requires 'Administer Jira' global permission.
"""

import argparse
import json
import sys
from typing import Any

# Add shared lib to path
from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    ValidationError,
    get_jira_client,
    print_error,
)


def get_workflow(
    client,
    name: str | None = None,
    entity_id: str | None = None,
    show_statuses: bool = False,
    show_transitions: bool = False,
    show_rules: bool = False,
    show_schemes: bool = False,
) -> dict[str, Any]:
    """
    Get detailed workflow information.

    Args:
        client: JiraClient instance
        name: Workflow name to look up
        entity_id: Workflow entity ID (alternative to name)
        show_statuses: Include status details
        show_transitions: Include transition details
        show_rules: Include transition rules (conditions, validators, post-functions)
        show_schemes: Include workflow schemes using this workflow

    Returns:
        Dict with workflow details

    Raises:
        ValidationError: If neither name nor entity_id provided
        NotFoundError: If workflow not found
    """
    if not name and not entity_id:
        raise ValidationError("Either workflow name or entity_id must be provided")

    workflow_data = None

    if entity_id:
        # Get workflow by entity ID using bulk endpoint
        response = client.get_workflow_bulk(
            workflow_ids=[entity_id],
            expand="transitions,transitions.rules,statuses"
            if (show_statuses or show_transitions or show_rules)
            else None,
        )
        workflows = response.get("workflows", [])
        if not workflows:
            raise NotFoundError(f"Workflow with entity ID '{entity_id}' not found")
        workflow_data = workflows[0]
    else:
        # Search for workflow by name
        expand = "transitions,statuses"
        if show_rules:
            expand = "transitions,transitions.rules,statuses"

        response = client.search_workflows(
            workflow_name=name, expand=expand, max_results=100
        )

        workflows = response.get("values", [])
        # Find exact match
        for wf in workflows:
            wf_name = wf.get("id", {}).get("name", wf.get("name", ""))
            if wf_name.lower() == name.lower():
                workflow_data = wf
                break

        if not workflow_data:
            raise NotFoundError(f"Workflow '{name}' not found")

    # Parse workflow data
    result = _parse_workflow_details(workflow_data)

    # Add statuses if requested
    if show_statuses or show_transitions or show_rules:
        statuses = workflow_data.get("statuses", [])
        result["statuses"] = _parse_statuses(statuses)

    # Add transitions if requested
    if show_transitions or show_rules:
        transitions = workflow_data.get("transitions", [])
        result["transitions"] = _parse_transitions(transitions, show_rules)

    # Add schemes if requested
    if show_schemes:
        try:
            schemes_response = client.get_workflow_schemes_for_workflow(
                result["entity_id"], max_results=100
            )
            result["schemes"] = [
                {
                    "id": s.get("id"),
                    "name": s.get("name", "Unknown"),
                    "description": s.get("description", ""),
                }
                for s in schemes_response.get("values", [])
            ]
        except JiraError:
            result["schemes"] = []

    return result


def _parse_workflow_details(workflow_data: dict[str, Any]) -> dict[str, Any]:
    """Parse basic workflow details from API response."""
    # Handle different response formats
    if "id" in workflow_data and isinstance(workflow_data["id"], dict):
        name = workflow_data["id"].get("name", "Unknown")
        entity_id = workflow_data["id"].get("entityId", "")
    else:
        name = workflow_data.get("name", "Unknown")
        entity_id = workflow_data.get(
            "entityId", workflow_data.get("id", {}).get("entityId", "")
        )

    result = {
        "name": name,
        "entity_id": entity_id,
        "description": workflow_data.get("description", ""),
        "is_default": workflow_data.get("isDefault", False),
    }

    # Handle scope
    scope = workflow_data.get("scope", {})
    result["scope_type"] = scope.get("type", "GLOBAL")
    if scope.get("project"):
        result["scope_project"] = scope["project"].get("key", "")

    # Handle version
    version = workflow_data.get("version", {})
    result["version"] = version.get("versionNumber", 1) if version else 1

    # Handle dates
    result["created"] = workflow_data.get("created", "")
    result["updated"] = workflow_data.get("updated", "")

    return result


def _parse_statuses(statuses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse status list from workflow data."""
    result = []
    for status in statuses:
        result.append(
            {
                "id": status.get("id", ""),
                "name": status.get("name", "Unknown"),
                "statusCategory": status.get("statusCategory", "UNKNOWN"),
                "statusReference": status.get("statusReference", ""),
            }
        )

    # Sort by category: TODO, IN_PROGRESS, DONE
    category_order = {"TODO": 0, "IN_PROGRESS": 1, "DONE": 2}
    result.sort(key=lambda s: category_order.get(s["statusCategory"], 99))

    return result


def _parse_transitions(
    transitions: list[dict[str, Any]], include_rules: bool = False
) -> list[dict[str, Any]]:
    """Parse transition list from workflow data."""
    result = []
    for transition in transitions:
        t = {
            "id": transition.get("id", ""),
            "name": transition.get("name", "Unknown"),
            "description": transition.get("description", ""),
            "from": transition.get("from", []),
            "to": transition.get("to", ""),
            "type": transition.get("type", "DIRECTED"),
        }

        if include_rules:
            rules = transition.get("rules", {})
            t["rules"] = {
                "conditions": rules.get("conditions", []),
                "validators": rules.get("validators", []),
                "postFunctions": rules.get("postFunctions", []),
            }

        result.append(t)

    return result


def format_workflow_details(workflow: dict[str, Any]) -> str:
    """Format workflow details as human-readable text."""
    lines = []

    # Header
    lines.append(f"Workflow: {workflow['name']}")
    lines.append("=" * (len(workflow["name"]) + 10))

    # Basic info
    lines.append(f"Entity ID:   {workflow.get('entity_id', 'N/A')}")
    lines.append(f"Description: {workflow.get('description', 'No description')}")
    lines.append(f"Scope:       {workflow.get('scope_type', 'GLOBAL')}")
    lines.append(f"Default:     {'Yes' if workflow.get('is_default') else 'No'}")
    lines.append(f"Version:     {workflow.get('version', 1)}")

    if workflow.get("created"):
        lines.append(f"Created:     {workflow['created']}")
    if workflow.get("updated"):
        lines.append(f"Updated:     {workflow['updated']}")

    # Statuses
    if "statuses" in workflow:
        lines.append("")
        lines.append(f"Statuses ({len(workflow['statuses'])})")
        lines.append("-" * 20)

        for status in workflow["statuses"]:
            category = status.get("statusCategory", "UNKNOWN")
            lines.append(f"  - {status['name']} [{category}]")

    # Transitions
    if "transitions" in workflow:
        lines.append("")
        lines.append(f"Transitions ({len(workflow['transitions'])})")
        lines.append("-" * 20)

        for t in workflow["transitions"]:
            from_states = ", ".join(t.get("from", [])) or "Any"
            to_state = t.get("to", "Unknown")
            lines.append(f"  - {t['name']}: {from_states} -> {to_state}")

            if t.get("description"):
                lines.append(f"    {t['description']}")

            # Show rules if present
            if "rules" in t:
                rules = t["rules"]
                if rules.get("conditions"):
                    lines.append(f"    Conditions: {len(rules['conditions'])}")
                if rules.get("validators"):
                    lines.append(f"    Validators: {len(rules['validators'])}")
                if rules.get("postFunctions"):
                    lines.append(f"    Post-functions: {len(rules['postFunctions'])}")

    # Schemes
    if "schemes" in workflow:
        lines.append("")
        lines.append(
            f"Workflow Schemes Using This Workflow ({len(workflow['schemes'])})"
        )
        lines.append("-" * 40)

        if workflow["schemes"]:
            for scheme in workflow["schemes"]:
                lines.append(f"  - {scheme['name']}")
        else:
            lines.append("  (Not used by any workflow schemes)")

    return "\n".join(lines)


def format_workflow_json(workflow: dict[str, Any]) -> str:
    """Format workflow as JSON."""
    return json.dumps(workflow, indent=2, default=str)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Get detailed workflow information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get workflow by name
  python get_workflow.py "Software Development Workflow"

  # Get by entity ID
  python get_workflow.py --entity-id "c6c7e6b0-19c4-4516-9a47-93f76124d4d4"

  # Show all statuses
  python get_workflow.py "Software Development Workflow" --show-statuses

  # Show all transitions
  python get_workflow.py "Software Development Workflow" --show-transitions

  # Show transition rules (conditions, validators, post-functions)
  python get_workflow.py "Software Development Workflow" --show-rules

  # Show which schemes use this workflow
  python get_workflow.py "Software Development Workflow" --show-schemes

  # All details
  python get_workflow.py "Software Development Workflow" --show-statuses --show-transitions --show-schemes

  # JSON output
  python get_workflow.py "Software Development Workflow" --output json

Note: Requires 'Administer Jira' global permission.
        """,
    )

    parser.add_argument("name", nargs="?", help="Workflow name to look up")
    parser.add_argument(
        "--entity-id",
        "-e",
        dest="entity_id",
        help="Workflow entity ID (alternative to name)",
    )
    parser.add_argument(
        "--show-statuses",
        "-s",
        action="store_true",
        help="Show all statuses in the workflow",
    )
    parser.add_argument(
        "--show-transitions",
        "-t",
        action="store_true",
        help="Show all transitions in the workflow",
    )
    parser.add_argument(
        "--show-rules",
        "-r",
        action="store_true",
        help="Show transition rules (conditions, validators, post-functions)",
    )
    parser.add_argument(
        "--show-schemes",
        action="store_true",
        help="Show which workflow schemes use this workflow",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    if not args.name and not args.entity_id:
        parser.error("Either workflow name or --entity-id must be provided")

    try:
        client = get_jira_client()

        result = get_workflow(
            client=client,
            name=args.name,
            entity_id=args.entity_id,
            show_statuses=args.show_statuses,
            show_transitions=args.show_transitions,
            show_rules=args.show_rules,
            show_schemes=args.show_schemes,
        )

        if args.output == "json":
            print(format_workflow_json(result))
        else:
            print(format_workflow_details(result))

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    finally:
        if "client" in locals():
            client.close()


if __name__ == "__main__":
    main()
