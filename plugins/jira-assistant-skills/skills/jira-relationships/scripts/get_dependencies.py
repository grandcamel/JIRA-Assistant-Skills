#!/usr/bin/env python3
"""
Find all dependencies for a JIRA issue and export as diagrams.

WHEN TO USE THIS SCRIPT:
- Stakeholder communication: Generate visual dependency diagrams
- Release planning: Create dependency graphs for release scope
- Technical documentation: Export diagrams for wiki/confluence
- Architecture review: Visualize component relationships
- Sprint review: Generate dependency visuals for presentations
- Vs. get_blockers.py: Use this for visualization; use blockers for chain analysis
- Vs. link_stats.py: Use this for diagrams; use stats for metrics/patterns

OUTPUT FORMATS:
- mermaid: GitHub/GitLab markdown (renders in-browser)
- dot: Graphviz (use: dot -Tpng deps.dot -o deps.png)
- plantuml: PlantUML server or CLI
- d2: D2/Terrastruct (use: d2 deps.d2 deps.svg)
- text: Terminal tree view
- json: Programmatic processing

Usage:
    python get_dependencies.py PROJ-123
    python get_dependencies.py PROJ-123 --type blocks,relates
    python get_dependencies.py PROJ-123 --output mermaid
    python get_dependencies.py PROJ-123 --output dot > deps.dot
    python get_dependencies.py PROJ-123 --output plantuml > deps.puml
    python get_dependencies.py PROJ-123 --output d2 > deps.d2
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
)


def get_dependencies(
    issue_key: str,
    link_types: list[str] | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """
    Get all dependencies for an issue.

    Args:
        issue_key: Issue key
        link_types: Optional list of link type names to filter
        profile: JIRA profile

    Returns:
        Dict with dependencies info
    """
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client(profile)

    try:
        links = client.get_issue_links(issue_key)
    finally:
        client.close()

    dependencies = []
    status_counts = defaultdict(int)

    for link in links:
        link_type = link["type"]["name"]

        # Filter by link type if specified
        if link_types and link_type.lower() not in [t.lower() for t in link_types]:
            continue

        if "outwardIssue" in link:
            issue = link["outwardIssue"]
            direction = "outward"
            direction_label = link["type"]["outward"]
        else:
            issue = link["inwardIssue"]
            direction = "inward"
            direction_label = link["type"]["inward"]

        status = issue.get("fields", {}).get("status", {}).get("name", "Unknown")
        status_counts[status] += 1

        dependencies.append(
            {
                "key": issue["key"],
                "summary": issue.get("fields", {}).get("summary", ""),
                "status": status,
                "link_type": link_type,
                "direction": direction,
                "direction_label": direction_label,
                "link_id": link["id"],
            }
        )

    return {
        "issue_key": issue_key,
        "dependencies": dependencies,
        "total": len(dependencies),
        "status_summary": dict(status_counts),
    }


def format_dependencies(result: dict[str, Any], output_format: str = "text") -> str:
    """
    Format dependencies for output.

    Args:
        result: Dependencies result dict
        output_format: 'text', 'json', 'mermaid', 'dot', 'plantuml', or 'd2'

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(result, indent=2)

    issue_key = result["issue_key"]
    dependencies = result.get("dependencies", [])

    if output_format == "mermaid":
        return format_mermaid(issue_key, dependencies)
    elif output_format == "dot":
        return format_dot(issue_key, dependencies)
    elif output_format == "plantuml":
        return format_plantuml(issue_key, dependencies)
    elif output_format == "d2":
        return format_d2(issue_key, dependencies)

    # Text format
    if not dependencies:
        return f"No dependencies found for {issue_key}"

    lines = []
    lines.append(f"Dependencies for {issue_key}:")
    lines.append("")

    # Group by link type
    by_type = defaultdict(list)
    for dep in dependencies:
        by_type[dep["link_type"]].append(dep)

    for link_type, deps in by_type.items():
        lines.append(f"{link_type}:")
        for dep in deps:
            status = dep["status"]
            summary = dep["summary"][:45] if dep["summary"] else ""
            arrow = "->" if dep["direction"] == "outward" else "<-"
            lines.append(f"  {arrow} {dep['key']} [{status}] {summary}")
        lines.append("")

    # Status summary
    status_summary = result.get("status_summary", {})
    if status_summary:
        lines.append("Status Summary:")
        for status, count in sorted(status_summary.items()):
            lines.append(f"  {status}: {count}")
        lines.append("")

    lines.append(f"Total: {result['total']} dependency(ies)")

    return "\n".join(lines)


def format_mermaid(issue_key: str, dependencies: list) -> str:
    """Format as Mermaid flowchart."""
    lines = []
    lines.append("flowchart TD")

    # Define the main issue
    lines.append(f"    {sanitize_key(issue_key)}[{issue_key}]")

    # Add nodes and edges
    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep["key"]
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            # Node with summary
            summary = (
                dep["summary"][:30].replace('"', "'") if dep["summary"] else dep_key
            )
            lines.append(f'    {sanitize_key(dep_key)}["{dep_key}: {summary}"]')

        # Edge
        label = dep["direction_label"]
        if dep["direction"] == "outward":
            lines.append(
                f"    {sanitize_key(issue_key)} -->|{label}| {sanitize_key(dep_key)}"
            )
        else:
            lines.append(
                f"    {sanitize_key(dep_key)} -->|{label}| {sanitize_key(issue_key)}"
            )

    return "\n".join(lines)


def format_dot(issue_key: str, dependencies: list) -> str:
    """Format as DOT/Graphviz."""
    lines = []
    lines.append("digraph Dependencies {")
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=box];")
    lines.append("")

    # Main issue
    lines.append(f'    "{issue_key}" [style=filled, fillcolor=lightblue];')

    # Dependencies
    for dep in dependencies:
        dep_key = dep["key"]
        status = dep["status"]

        # Color by status
        color = (
            "lightgreen"
            if status == "Done"
            else "lightyellow"
            if status == "In Progress"
            else "white"
        )
        lines.append(f'    "{dep_key}" [style=filled, fillcolor={color}];')

        # Edge
        label = dep["direction_label"]
        if dep["direction"] == "outward":
            lines.append(f'    "{issue_key}" -> "{dep_key}" [label="{label}"];')
        else:
            lines.append(f'    "{dep_key}" -> "{issue_key}" [label="{label}"];')

    lines.append("}")
    return "\n".join(lines)


def sanitize_key(key: str) -> str:
    """Sanitize issue key for Mermaid node ID."""
    return key.replace("-", "_")


def format_plantuml(issue_key: str, dependencies: list) -> str:
    """Format as PlantUML diagram."""
    lines = []
    lines.append("@startuml")
    lines.append("")
    lines.append("' Dependency diagram for " + issue_key)
    lines.append("skinparam rectangle {")
    lines.append("    BackgroundColor<<done>> LightGreen")
    lines.append("    BackgroundColor<<inprogress>> LightYellow")
    lines.append("    BackgroundColor<<open>> White")
    lines.append("    BackgroundColor<<main>> LightBlue")
    lines.append("}")
    lines.append("")

    # Main issue
    lines.append(f'rectangle "{issue_key}" as {sanitize_key(issue_key)} <<main>>')
    lines.append("")

    # Dependency nodes
    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep["key"]
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            status = dep["status"].lower().replace(" ", "")
            summary = (
                dep["summary"][:40].replace('"', "'") if dep["summary"] else dep_key
            )

            # Determine stereotype based on status
            if "done" in status or "closed" in status or "resolved" in status:
                stereotype = "<<done>>"
            elif "progress" in status:
                stereotype = "<<inprogress>>"
            else:
                stereotype = "<<open>>"

            lines.append(
                f'rectangle "{dep_key}\\n{summary}" as {sanitize_key(dep_key)} {stereotype}'
            )

    lines.append("")

    # Edges
    for dep in dependencies:
        dep_key = dep["key"]
        label = dep["direction_label"]

        if dep["direction"] == "outward":
            lines.append(
                f"{sanitize_key(issue_key)} --> {sanitize_key(dep_key)} : {label}"
            )
        else:
            lines.append(
                f"{sanitize_key(dep_key)} --> {sanitize_key(issue_key)} : {label}"
            )

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


def format_d2(issue_key: str, dependencies: list) -> str:
    """Format as d2 diagram (Terrastruct)."""
    lines = []
    lines.append("# Dependency diagram for " + issue_key)
    lines.append("direction: right")
    lines.append("")

    # Define main issue
    safe_main = issue_key.replace("-", "_")
    lines.append(f'{safe_main}: "{issue_key}" {{')
    lines.append('  style.fill: "#87CEEB"')  # Light blue
    lines.append('  style.stroke: "#4169E1"')
    lines.append("}")
    lines.append("")

    # Define dependency nodes
    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep["key"]
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            safe_key = dep_key.replace("-", "_")
            status = dep["status"]
            summary = dep["summary"][:35].replace('"', "'") if dep["summary"] else ""

            # Color based on status
            status_lower = status.lower()
            if (
                "done" in status_lower
                or "closed" in status_lower
                or "resolved" in status_lower
            ):
                fill_color = "#90EE90"  # Light green
            elif "progress" in status_lower:
                fill_color = "#FFFACD"  # Light yellow
            else:
                fill_color = "#FFFFFF"  # White

            label = f"{dep_key}"
            if summary:
                label += f"\\n{summary}"
            label += f"\\n[{status}]"

            lines.append(f'{safe_key}: "{label}" {{')
            lines.append(f'  style.fill: "{fill_color}"')
            lines.append("}")

    lines.append("")

    # Define edges
    for dep in dependencies:
        dep_key = dep["key"]
        safe_dep = dep_key.replace("-", "_")
        label = dep["direction_label"]

        if dep["direction"] == "outward":
            lines.append(f'{safe_main} -> {safe_dep}: "{label}"')
        else:
            lines.append(f'{safe_dep} -> {safe_main}: "{label}"')

    return "\n".join(lines)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Find all dependencies for a JIRA issue",
        epilog="""
Examples:
  %(prog)s PROJ-123
  %(prog)s PROJ-123 --output mermaid
  %(prog)s PROJ-123 --output dot > deps.dot
  %(prog)s PROJ-123 --output plantuml > deps.puml
  %(prog)s PROJ-123 --output d2 > deps.d2

Export formats:
  mermaid   - Mermaid.js flowchart format
  dot       - Graphviz DOT format
  plantuml  - PlantUML diagram format
  d2        - D2 diagram format (Terrastruct)
        """,
    )

    parser.add_argument("issue_key", help="Issue key (e.g., PROJ-123)")

    parser.add_argument(
        "--type",
        "-t",
        dest="link_types",
        help="Comma-separated link types to include (e.g., blocks,relates)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["text", "json", "mermaid", "dot", "plantuml", "d2"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use (default: from config)")

    args = parser.parse_args(argv)

    try:
        link_types = args.link_types.split(",") if args.link_types else None

        result = get_dependencies(
            issue_key=args.issue_key, link_types=link_types, profile=args.profile
        )
        output = format_dependencies(result, output_format=args.output)
        print(output)

    except JiraError as e:
        print_error(e)
        sys.exit(1)
    except Exception as e:
        print_error(e, debug=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
