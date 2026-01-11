#!/usr/bin/env python3
"""
Check JSM service request SLA breach status.

Usage:
    python check_sla_breach.py SD-123
    python check_sla_breach.py SD-123 --threshold 30
    python check_sla_breach.py SD-123 --sla-name "Time to First Response"
    python check_sla_breach.py SD-123 --output json
"""

import argparse
import json
import sys
from typing import Any

from jira_assistant_skills_lib import (
    JiraError,
    NotFoundError,
    format_duration,
    format_sla_time,
    get_jira_client,
    is_sla_at_risk,
    print_error,
)


def check_sla_breach(
    issue_key: str,
    threshold: float = 20.0,
    sla_name: str | None = None,
) -> dict[str, Any]:
    """
    Check SLA breach status for a service request.

    Args:
        issue_key: Request key (e.g., 'SD-123')
        threshold: At-risk threshold percentage (default 20%)
        sla_name: Filter to specific SLA name (optional)

    Returns:
        Dict with breach status, SLAs, and statistics

    Raises:
        NotFoundError: If request doesn't exist
    """
    with get_jira_client() as client:
        sla_data = client.get_request_slas(issue_key)

    slas = sla_data.get("values", [])

    # Filter by SLA name if specified
    if sla_name:
        slas = [sla for sla in slas if sla.get("name") == sla_name]

    # Analyze each SLA
    breached = []
    at_risk = []
    paused = []
    met = []

    for sla in slas:
        ongoing = sla.get("ongoingCycle")

        if ongoing:
            if ongoing.get("breached"):
                breached.append(sla)
            elif ongoing.get("paused"):
                paused.append(sla)
            else:
                remaining = ongoing.get("remainingTime", {}).get("millis", 0)
                goal = ongoing.get("goalDuration", {}).get("millis", 0)
                if is_sla_at_risk(remaining, goal, threshold):
                    at_risk.append(sla)
        else:
            # Check completed cycles
            completed = sla.get("completedCycles", [])
            if completed:
                last_cycle = completed[-1]
                if last_cycle.get("breached"):
                    breached.append(sla)
                else:
                    met.append(sla)

    return {
        "issue_key": issue_key,
        "total_slas": len(slas),
        "breached": breached,
        "at_risk": at_risk,
        "paused": paused,
        "met": met,
        "threshold": threshold,
        "has_breach": len(breached) > 0,
        "has_risk": len(at_risk) > 0,
    }


def format_breach_text(result: dict[str, Any]) -> str:
    """Format breach check result as text output."""
    lines = []

    lines.append(f"\nSLA Status for {result['issue_key']}:")
    lines.append("=" * 60)
    lines.append("")

    # Breached SLAs
    if result["breached"]:
        lines.append(
            f"✗ BREACHED ({len(result['breached'])} SLA{'s' if len(result['breached']) > 1 else ''}):"
        )
        for sla in result["breached"]:
            name = sla.get("name")
            ongoing = sla.get("ongoingCycle")
            if ongoing:
                elapsed = format_duration(ongoing.get("elapsedTime"))
                goal = format_duration(ongoing.get("goalDuration"))
                lines.append(f"  • {name}")
                lines.append(f"    Goal:    {goal}")
                lines.append(f"    Elapsed: {elapsed}")
            else:
                completed = sla.get("completedCycles", [])
                if completed:
                    last = completed[-1]
                    elapsed = format_duration(last.get("elapsedTime"))
                    goal = format_duration(last.get("goalDuration"))
                    lines.append(f"  • {name}")
                    lines.append(f"    Goal:    {goal}")
                    lines.append(f"    Actual:  {elapsed}")
        lines.append("")

    # At-risk SLAs
    if result["at_risk"]:
        lines.append(
            f"⚠ AT RISK ({len(result['at_risk'])} SLA{'s' if len(result['at_risk']) > 1 else ''}):"
        )
        for sla in result["at_risk"]:
            name = sla.get("name")
            ongoing = sla.get("ongoingCycle")
            elapsed = format_duration(ongoing.get("elapsedTime"))
            remaining = format_duration(ongoing.get("remainingTime"))
            breach_time = format_sla_time(ongoing.get("breachTime"))
            remaining_millis = ongoing.get("remainingTime", {}).get("millis", 0)
            goal_millis = ongoing.get("goalDuration", {}).get("millis", 0)
            percentage = (
                (remaining_millis / goal_millis * 100) if goal_millis > 0 else 0
            )

            lines.append(f"  • {name}")
            lines.append(f"    Elapsed:   {elapsed}")
            lines.append(f"    Remaining: {remaining} ({percentage:.1f}% of goal)")
            lines.append(f"    Breach at: {breach_time}")
            lines.append(
                f"    Warning:   Less than {result['threshold']}% time remaining"
            )
        lines.append("")

    # Paused SLAs
    if result["paused"]:
        lines.append(
            f"⏸ PAUSED ({len(result['paused'])} SLA{'s' if len(result['paused']) > 1 else ''}):"
        )
        for sla in result["paused"]:
            name = sla.get("name")
            lines.append(f"  • {name}")
        lines.append("")

    # Met SLAs
    if result["met"]:
        lines.append(
            f"✓ MET ({len(result['met'])} SLA{'s' if len(result['met']) > 1 else ''}):"
        )
        for sla in result["met"]:
            name = sla.get("name")
            completed = sla.get("completedCycles", [])
            if completed:
                last = completed[-1]
                elapsed = format_duration(last.get("elapsedTime"))
                lines.append(f"  • {name} (completed in {elapsed})")
        lines.append("")

    # Overall status
    if result["has_breach"]:
        lines.append("Overall Status: BREACHED")
        lines.append("Exit code: 1")
    elif result["has_risk"]:
        lines.append("Overall Status: AT RISK")
        lines.append("Exit code: 0 (use --fail-on-risk for non-zero exit)")
    else:
        lines.append("Overall Status: ALL CLEAR")
        lines.append("Exit code: 0")

    return "\n".join(lines)


def format_breach_json(result: dict[str, Any]) -> str:
    """Format breach check result as JSON output."""
    # Convert to JSON-serializable format
    output = {
        "issue_key": result["issue_key"],
        "total_slas": result["total_slas"],
        "threshold": result["threshold"],
        "has_breach": result["has_breach"],
        "has_risk": result["has_risk"],
        "breached_count": len(result["breached"]),
        "at_risk_count": len(result["at_risk"]),
        "paused_count": len(result["paused"]),
        "met_count": len(result["met"]),
        "breached": [
            {"name": s.get("name"), "id": s.get("id")} for s in result["breached"]
        ],
        "at_risk": [
            {"name": s.get("name"), "id": s.get("id")} for s in result["at_risk"]
        ],
        "paused": [
            {"name": s.get("name"), "id": s.get("id")} for s in result["paused"]
        ],
        "met": [{"name": s.get("name"), "id": s.get("id")} for s in result["met"]],
    }
    return json.dumps(output, indent=2)


def main(argv: list[str] | None = None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check JSM service request SLA breach status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Check SLA status:
    %(prog)s SD-123

  Custom at-risk threshold:
    %(prog)s SD-123 --threshold 30

  Check specific SLA:
    %(prog)s SD-123 --sla-name "Time to First Response"

  JSON output:
    %(prog)s SD-123 --output json
        """,
    )

    parser.add_argument("request_key", help="Request key (e.g., SD-123)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=20.0,
        help="At-risk threshold percentage (default: 20%%)",
    )
    parser.add_argument("--sla-name", help="Check specific SLA only")
    parser.add_argument(
        "--fail-on-risk",
        action="store_true",
        help="Exit with code 1 if any SLA is at risk",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        result = check_sla_breach(
            issue_key=args.request_key,
            threshold=args.threshold,
            sla_name=args.sla_name,
        )

        if args.output == "json":
            print(format_breach_json(result))
        else:
            print(format_breach_text(result))

        # Determine exit code
        if result["has_breach"]:
            return 1
        if args.fail_on_risk and result["has_risk"]:
            return 1

        return 0

    except NotFoundError as e:
        print_error(f"Request not found: {e}")
        return 1
    except JiraError as e:
        print_error(f"Failed to check SLA: {e}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
