"""
CLI commands for issue relationships: links, dependencies, cloning.

This module contains all logic for jira-relationships operations.
All implementation functions are inlined for direct CLI usage.
"""

import json
from collections import defaultdict
from typing import Any

import click

from jira_assistant_skills_lib import (
    JiraError,
    ValidationError,
    get_jira_client,
    text_to_adf,
    validate_issue_key,
    validate_jql,
)

from jira_assistant_skills.cli.cli_utils import handle_jira_errors, format_json


# =============================================================================
# Constants
# =============================================================================

# Mapping of semantic flags to JIRA link type names
LINK_TYPE_MAPPING = {
    "blocks": "Blocks",
    "is_blocked_by": "Blocks",
    "duplicates": "Duplicate",
    "is_duplicated_by": "Duplicate",
    "relates_to": "Relates",
    "clones": "Cloners",
    "is_cloned_by": "Cloners",
}

# Fields that can be cloned to new issue
CLONEABLE_FIELDS = [
    "summary",
    "description",
    "priority",
    "labels",
    "components",
    "assignee",
    "reporter",
    "environment",
    "fixVersions",
    "versions",
]


# =============================================================================
# Helper Functions
# =============================================================================


def _find_link_type(link_types: list, name: str) -> dict:
    """
    Find a link type by name (case-insensitive).

    Args:
        link_types: List of available link types
        name: Link type name to find

    Returns:
        Link type object

    Raises:
        ValidationError: If link type not found
    """
    name_lower = name.lower()

    for lt in link_types:
        if lt["name"].lower() == name_lower:
            return lt

    available = ", ".join(lt["name"] for lt in link_types)
    raise ValidationError(f"Link type '{name}' not found. Available: {available}")


def _find_link_to_issue(links: list, target_key: str) -> dict | None:
    """Find a link to/from a specific issue."""
    target_upper = target_key.upper()
    for link in links:
        if "outwardIssue" in link:
            if link["outwardIssue"]["key"].upper() == target_upper:
                return link
        if "inwardIssue" in link:
            if link["inwardIssue"]["key"].upper() == target_upper:
                return link
    return None


def _sanitize_key(key: str) -> str:
    """Sanitize issue key for diagram node ID."""
    return key.replace("-", "_")


def _extract_blockers(links: list, direction: str = "inward") -> list:
    """Extract blocker issues from links."""
    blockers = []
    for link in links:
        if link["type"]["name"] != "Blocks":
            continue

        if direction == "inward" and "outwardIssue" in link:
            issue = link["outwardIssue"]
            blockers.append({
                "key": issue["key"],
                "summary": issue.get("fields", {}).get("summary", ""),
                "status": issue.get("fields", {}).get("status", {}).get("name", "Unknown"),
                "link_id": link["id"],
            })
        elif direction == "outward" and "inwardIssue" in link:
            issue = link["inwardIssue"]
            blockers.append({
                "key": issue["key"],
                "summary": issue.get("fields", {}).get("summary", ""),
                "status": issue.get("fields", {}).get("status", {}).get("name", "Unknown"),
                "link_id": link["id"],
            })

    return blockers


def _get_blockers_recursive(
    client,
    issue_key: str,
    direction: str,
    visited: set[str],
    max_depth: int,
    current_depth: int,
) -> dict[str, Any]:
    """Recursively get blockers."""
    if issue_key in visited:
        return {"key": issue_key, "circular": True, "blockers": []}

    if max_depth > 0 and current_depth >= max_depth:
        return {"key": issue_key, "depth_limited": True, "blockers": []}

    visited.add(issue_key)

    links = client.get_issue_links(issue_key)
    direct_blockers = _extract_blockers(links, direction)

    result = {"key": issue_key, "blockers": []}

    for blocker in direct_blockers:
        blocker_info = _get_blockers_recursive(
            client, blocker["key"], direction, visited, max_depth, current_depth + 1
        )
        blocker_info["summary"] = blocker["summary"]
        blocker_info["status"] = blocker["status"]
        result["blockers"].append(blocker_info)

    return result


def _flatten_blockers(tree: dict[str, Any], all_blockers: list[dict], seen: set[str]):
    """Flatten blocker tree into list."""
    for blocker in tree.get("blockers", []):
        if blocker["key"] not in seen:
            seen.add(blocker["key"])
            all_blockers.append({
                "key": blocker["key"],
                "summary": blocker.get("summary", ""),
                "status": blocker.get("status", "Unknown"),
                "circular": blocker.get("circular", False),
            })
            _flatten_blockers(blocker, all_blockers, seen)


def _extract_cloneable_fields(
    issue: dict[str, Any], to_project: str | None = None
) -> dict[str, Any]:
    """Extract fields from an issue that can be cloned."""
    original_fields = issue.get("fields", {})
    new_fields = {}

    # Project - either original or target
    if to_project:
        new_fields["project"] = {"key": to_project}
    else:
        project = original_fields.get("project", {})
        new_fields["project"] = {"key": project.get("key")}

    # Issue type
    issuetype = original_fields.get("issuetype", {})
    new_fields["issuetype"] = {"name": issuetype.get("name", "Task")}

    # Summary - prefix with clone indicator
    original_summary = original_fields.get("summary", "Untitled")
    new_fields["summary"] = f"[Clone of {issue['key']}] {original_summary}"

    # Clone other fields if they exist and have values
    for field_name in CLONEABLE_FIELDS:
        if field_name == "summary":
            continue  # Already handled

        value = original_fields.get(field_name)
        if value is not None:
            if field_name in ["priority"]:
                if isinstance(value, dict) and "name" in value:
                    new_fields[field_name] = {"name": value["name"]}
            elif field_name in ["labels"]:
                new_fields[field_name] = value if isinstance(value, list) else []
            elif field_name in ["components", "fixVersions", "versions"]:
                if not to_project:
                    new_fields[field_name] = value
            elif field_name in ["assignee", "reporter"]:
                if isinstance(value, dict) and "accountId" in value:
                    new_fields[field_name] = {"accountId": value["accountId"]}
            else:
                new_fields[field_name] = value

    return new_fields


# =============================================================================
# Diagram Format Functions
# =============================================================================


def _format_mermaid(issue_key: str, dependencies: list) -> str:
    """Format as Mermaid flowchart."""
    lines = []
    lines.append("flowchart TD")
    lines.append(f"    {_sanitize_key(issue_key)}[{issue_key}]")

    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep["key"]
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            summary = dep["summary"][:30].replace('"', "'") if dep["summary"] else dep_key
            lines.append(f'    {_sanitize_key(dep_key)}["{dep_key}: {summary}"]')

        label = dep["direction_label"]
        if dep["direction"] == "outward":
            lines.append(f"    {_sanitize_key(issue_key)} -->|{label}| {_sanitize_key(dep_key)}")
        else:
            lines.append(f"    {_sanitize_key(dep_key)} -->|{label}| {_sanitize_key(issue_key)}")

    return "\n".join(lines)


def _format_dot(issue_key: str, dependencies: list) -> str:
    """Format as DOT/Graphviz."""
    lines = []
    lines.append("digraph Dependencies {")
    lines.append("    rankdir=LR;")
    lines.append("    node [shape=box];")
    lines.append("")
    lines.append(f'    "{issue_key}" [style=filled, fillcolor=lightblue];')

    for dep in dependencies:
        dep_key = dep["key"]
        status = dep["status"]
        color = (
            "lightgreen" if status == "Done"
            else "lightyellow" if status == "In Progress"
            else "white"
        )
        lines.append(f'    "{dep_key}" [style=filled, fillcolor={color}];')

        label = dep["direction_label"]
        if dep["direction"] == "outward":
            lines.append(f'    "{issue_key}" -> "{dep_key}" [label="{label}"];')
        else:
            lines.append(f'    "{dep_key}" -> "{issue_key}" [label="{label}"];')

    lines.append("}")
    return "\n".join(lines)


def _format_plantuml(issue_key: str, dependencies: list) -> str:
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
    lines.append(f'rectangle "{issue_key}" as {_sanitize_key(issue_key)} <<main>>')
    lines.append("")

    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep["key"]
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            status = dep["status"].lower().replace(" ", "")
            summary = dep["summary"][:40].replace('"', "'") if dep["summary"] else dep_key

            if "done" in status or "closed" in status or "resolved" in status:
                stereotype = "<<done>>"
            elif "progress" in status:
                stereotype = "<<inprogress>>"
            else:
                stereotype = "<<open>>"

            lines.append(f'rectangle "{dep_key}\\n{summary}" as {_sanitize_key(dep_key)} {stereotype}')

    lines.append("")

    for dep in dependencies:
        dep_key = dep["key"]
        label = dep["direction_label"]

        if dep["direction"] == "outward":
            lines.append(f"{_sanitize_key(issue_key)} --> {_sanitize_key(dep_key)} : {label}")
        else:
            lines.append(f"{_sanitize_key(dep_key)} --> {_sanitize_key(issue_key)} : {label}")

    lines.append("")
    lines.append("@enduml")

    return "\n".join(lines)


def _format_d2(issue_key: str, dependencies: list) -> str:
    """Format as d2 diagram (Terrastruct)."""
    lines = []
    lines.append("# Dependency diagram for " + issue_key)
    lines.append("direction: right")
    lines.append("")

    safe_main = issue_key.replace("-", "_")
    lines.append(f'{safe_main}: "{issue_key}" {{')
    lines.append('  style.fill: "#87CEEB"')
    lines.append('  style.stroke: "#4169E1"')
    lines.append("}")
    lines.append("")

    seen_nodes = {issue_key}
    for dep in dependencies:
        dep_key = dep["key"]
        if dep_key not in seen_nodes:
            seen_nodes.add(dep_key)
            safe_key = dep_key.replace("-", "_")
            status = dep["status"]
            summary = dep["summary"][:35].replace('"', "'") if dep["summary"] else ""

            status_lower = status.lower()
            if "done" in status_lower or "closed" in status_lower or "resolved" in status_lower:
                fill_color = "#90EE90"
            elif "progress" in status_lower:
                fill_color = "#FFFACD"
            else:
                fill_color = "#FFFFFF"

            label = f"{dep_key}"
            if summary:
                label += f"\\n{summary}"
            label += f"\\n[{status}]"

            lines.append(f'{safe_key}: "{label}" {{')
            lines.append(f'  style.fill: "{fill_color}"')
            lines.append("}")

    lines.append("")

    for dep in dependencies:
        dep_key = dep["key"]
        safe_dep = dep_key.replace("-", "_")
        label = dep["direction_label"]

        if dep["direction"] == "outward":
            lines.append(f'{safe_main} -> {safe_dep}: "{label}"')
        else:
            lines.append(f'{safe_dep} -> {safe_main}: "{label}"')

    return "\n".join(lines)


# =============================================================================
# Implementation Functions
# =============================================================================


def _link_issue_impl(
    issue_key: str,
    blocks: str | None = None,
    duplicates: str | None = None,
    relates_to: str | None = None,
    clones: str | None = None,
    is_blocked_by: str | None = None,
    is_duplicated_by: str | None = None,
    is_cloned_by: str | None = None,
    link_type: str | None = None,
    target_issue: str | None = None,
    comment: str | None = None,
    dry_run: bool = False,
) -> dict | None:
    """Create a link between two issues."""
    issue_key = validate_issue_key(issue_key)

    # Determine link type and target from semantic flags or explicit type
    resolved_type = None
    resolved_target = None
    is_inward = False

    semantic_args = {
        "blocks": blocks,
        "duplicates": duplicates,
        "relates_to": relates_to,
        "clones": clones,
        "is_blocked_by": is_blocked_by,
        "is_duplicated_by": is_duplicated_by,
        "is_cloned_by": is_cloned_by,
    }

    for flag_name, flag_value in semantic_args.items():
        if flag_value:
            resolved_type = LINK_TYPE_MAPPING[flag_name]
            resolved_target = flag_value
            is_inward = flag_name.startswith("is_")
            break

    if link_type and target_issue:
        resolved_type = link_type
        resolved_target = target_issue

    if not resolved_type or not resolved_target:
        raise ValidationError(
            "Must specify a link type (--blocks, --duplicates, etc.) or --type with --to"
        )

    resolved_target = validate_issue_key(resolved_target)

    if issue_key.upper() == resolved_target.upper():
        raise ValidationError("Cannot link an issue to itself")

    client = get_jira_client()

    try:
        link_types = client.get_link_types()
        link_type_obj = _find_link_type(link_types, resolved_type)

        if is_inward:
            inward_key = issue_key
            outward_key = resolved_target
        else:
            inward_key = resolved_target
            outward_key = issue_key

        adf_comment = None
        if comment:
            adf_comment = text_to_adf(comment)

        if dry_run:
            direction = (
                link_type_obj.get("outward", resolved_type)
                if not is_inward
                else link_type_obj.get("inward", resolved_type)
            )
            return {
                "source": issue_key,
                "target": resolved_target,
                "link_type": link_type_obj["name"],
                "direction": direction,
                "preview": f"{issue_key} {direction} {resolved_target}",
            }

        client.create_link(link_type_obj["name"], inward_key, outward_key, adf_comment)

    finally:
        client.close()

    return None


def _unlink_issue_impl(
    issue_key: str,
    from_issue: str | None = None,
    link_type: str | None = None,
    remove_all: bool = False,
    dry_run: bool = False,
) -> dict:
    """Remove links from an issue."""
    issue_key = validate_issue_key(issue_key)

    if not from_issue and not (link_type and remove_all):
        raise ValidationError("Must specify --from ISSUE or --type TYPE with --all")

    if from_issue:
        from_issue = validate_issue_key(from_issue)

    client = get_jira_client()

    try:
        links = client.get_issue_links(issue_key)
        links_to_delete = []

        if from_issue:
            link = _find_link_to_issue(links, from_issue)
            if not link:
                raise ValidationError(f"{issue_key} is not linked to {from_issue}")
            links_to_delete.append(link)

        elif link_type and remove_all:
            type_lower = link_type.lower()
            links_to_delete = [
                l for l in links if l["type"]["name"].lower() == type_lower
            ]
            if not links_to_delete:
                raise ValidationError(f"No '{link_type}' links found for {issue_key}")

        if dry_run:
            result = {"issue_key": issue_key, "links_to_delete": []}
            for link in links_to_delete:
                if "outwardIssue" in link:
                    target = link["outwardIssue"]["key"]
                    direction = link["type"]["outward"]
                else:
                    target = link["inwardIssue"]["key"]
                    direction = link["type"]["inward"]
                result["links_to_delete"].append({
                    "id": link["id"],
                    "target": target,
                    "type": link["type"]["name"],
                    "direction": direction,
                })
            return result

        for link in links_to_delete:
            client.delete_link(link["id"])

    finally:
        client.close()

    return {"deleted_count": len(links_to_delete)}


def _get_links_impl(
    issue_key: str,
    direction: str | None = None,
    link_type: str | None = None,
) -> list:
    """Get links for an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()
    try:
        links = client.get_issue_links(issue_key)
    finally:
        client.close()

    if direction == "outward":
        links = [l for l in links if "inwardIssue" in l]
    elif direction == "inward":
        links = [l for l in links if "outwardIssue" in l]

    if link_type:
        type_lower = link_type.lower()
        links = [l for l in links if l["type"]["name"].lower() == type_lower]

    return links


def _get_blockers_impl(
    issue_key: str,
    direction: str = "inward",
    recursive: bool = False,
    max_depth: int = 0,
) -> dict[str, Any]:
    """Get blockers for an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()

    try:
        if recursive:
            visited: set[str] = set()
            tree = _get_blockers_recursive(
                client, issue_key, direction, visited, max_depth, 0
            )

            all_blockers: list[dict] = []
            seen: set[str] = set()
            _flatten_blockers(tree, all_blockers, seen)

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
            blockers = _extract_blockers(links, direction)

            return {
                "issue_key": issue_key,
                "direction": direction,
                "recursive": False,
                "blockers": blockers,
                "total": len(blockers),
            }
    finally:
        client.close()


def _get_dependencies_impl(
    issue_key: str,
    link_types: list[str] | None = None,
) -> dict[str, Any]:
    """Get all dependencies for an issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()

    try:
        links = client.get_issue_links(issue_key)
    finally:
        client.close()

    dependencies = []
    status_counts = defaultdict(int)

    for link in links:
        lt = link["type"]["name"]

        if link_types and lt.lower() not in [t.lower() for t in link_types]:
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

        dependencies.append({
            "key": issue["key"],
            "summary": issue.get("fields", {}).get("summary", ""),
            "status": status,
            "link_type": lt,
            "direction": direction,
            "direction_label": direction_label,
            "link_id": link["id"],
        })

    return {
        "issue_key": issue_key,
        "dependencies": dependencies,
        "total": len(dependencies),
        "status_summary": dict(status_counts),
    }


def _get_link_types_impl(filter_pattern: str | None = None) -> list:
    """Get all available issue link types."""
    client = get_jira_client()
    try:
        link_types = client.get_link_types()
    finally:
        client.close()

    if filter_pattern:
        pattern_lower = filter_pattern.lower()
        link_types = [
            lt for lt in link_types
            if pattern_lower in lt["name"].lower()
            or pattern_lower in lt.get("inward", "").lower()
            or pattern_lower in lt.get("outward", "").lower()
        ]

    return link_types


def _clone_issue_impl(
    issue_key: str,
    to_project: str | None = None,
    summary: str | None = None,
    include_subtasks: bool = False,
    include_links: bool = False,
    create_clone_link: bool = True,
) -> dict[str, Any]:
    """Clone a JIRA issue."""
    issue_key = validate_issue_key(issue_key)

    client = get_jira_client()

    try:
        original = client.get_issue(issue_key)
        new_fields = _extract_cloneable_fields(original, to_project)

        if summary:
            new_fields["summary"] = summary

        created = client.create_issue(new_fields)
        clone_key = created["key"]

        result = {
            "original_key": issue_key,
            "clone_key": clone_key,
            "project": new_fields["project"]["key"],
            "links_copied": 0,
            "subtasks_cloned": 0,
        }

        if create_clone_link:
            try:
                client.create_link("Cloners", clone_key, issue_key)
                result["clone_link_created"] = True
            except JiraError:
                result["clone_link_created"] = False

        if include_links:
            original_links = original.get("fields", {}).get("issuelinks", [])
            links_copied = 0

            for link in original_links:
                lt = link["type"]["name"]
                try:
                    if "outwardIssue" in link:
                        target_key = link["outwardIssue"]["key"]
                        client.create_link(lt, clone_key, target_key)
                        links_copied += 1
                    elif "inwardIssue" in link:
                        source_key = link["inwardIssue"]["key"]
                        client.create_link(lt, source_key, clone_key)
                        links_copied += 1
                except JiraError:
                    pass

            result["links_copied"] = links_copied

        if include_subtasks:
            subtasks = original.get("fields", {}).get("subtasks", [])
            subtasks_cloned = 0

            for subtask in subtasks:
                try:
                    subtask_full = client.get_issue(subtask["key"])
                    subtask_fields = _extract_cloneable_fields(subtask_full, to_project)
                    subtask_fields["parent"] = {"key": clone_key}
                    original_summary = subtask_full.get("fields", {}).get("summary", "")
                    subtask_fields["summary"] = f"[Clone] {original_summary}"
                    client.create_issue(subtask_fields)
                    subtasks_cloned += 1
                except JiraError:
                    pass

            result["subtasks_cloned"] = subtasks_cloned

        return result

    finally:
        client.close()


def _bulk_link_impl(
    issues: list[str] | None = None,
    jql: str | None = None,
    target: str | None = None,
    link_type: str | None = None,
    dry_run: bool = False,
    skip_existing: bool = False,
) -> dict[str, Any]:
    """Bulk link multiple issues to a target."""
    target = validate_issue_key(target)

    client = get_jira_client()

    try:
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

        issues = [validate_issue_key(key) for key in issues]

        if dry_run:
            return {
                "target": target,
                "link_type": link_type,
                "issues": issues,
                "dry_run": True,
                "would_create": len(issues),
            }

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

        created = 0
        failed = 0
        skipped = 0
        errors = []

        for issue_key in issues:
            if issue_key in existing_targets:
                skipped += 1
                continue

            try:
                client.create_link(link_type, issue_key, target)
                created += 1
            except JiraError as e:
                failed += 1
                errors.append(f"{issue_key}: {e!s}")

        return {
            "target": target,
            "link_type": link_type,
            "created": created,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "dry_run": False,
        }

    finally:
        client.close()


def _get_link_stats_impl(
    issue_key: str | None = None,
    jql: str | None = None,
    project: str | None = None,
    max_results: int = 500,
) -> dict[str, Any]:
    """Get link statistics for issues."""
    if issue_key:
        issue_key = validate_issue_key(issue_key)
        return _get_single_issue_stats(issue_key)
    else:
        if project:
            jql = f"project = {project}"
        else:
            jql = validate_jql(jql)
        return _get_project_stats(jql, max_results)


def _get_single_issue_stats(issue_key: str) -> dict[str, Any]:
    """Get link statistics for a single issue."""
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
        stats["linked_issues"].append({
            "key": issue["key"],
            "status": status,
            "link_type": link_type,
        })

    stats["by_type"] = dict(stats["by_type"])
    stats["by_status"] = dict(stats["by_status"])

    return stats


def _get_project_stats(jql: str, max_results: int = 500) -> dict[str, Any]:
    """Get link statistics for issues matching a JQL query."""
    client = get_jira_client()

    try:
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
                stats["orphaned_issues"].append({
                    "key": issue_key,
                    "summary": issue.get("fields", {}).get("summary", "")[:50],
                })
            else:
                issue_link_counts.append({
                    "key": issue_key,
                    "summary": issue.get("fields", {}).get("summary", "")[:50],
                    "link_count": link_count,
                })

            for link in links:
                link_type = link["type"]["name"]
                stats["by_type"][link_type] += 1

                if "outwardIssue" in link:
                    stats["by_direction"]["inward"] += 1
                    linked_issue = link["outwardIssue"]
                else:
                    stats["by_direction"]["outward"] += 1
                    linked_issue = link["inwardIssue"]

                status = linked_issue.get("fields", {}).get("status", {}).get("name", "Unknown")
                stats["by_status"][status] += 1

        issue_link_counts.sort(key=lambda x: x["link_count"], reverse=True)
        stats["most_connected"] = issue_link_counts[:20]

        stats["by_type"] = dict(stats["by_type"])
        stats["by_status"] = dict(stats["by_status"])

        return stats

    finally:
        client.close()


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_links(links: list, issue_key: str) -> str:
    """Format links for text output."""
    if not links:
        return f"No links found for {issue_key}"

    lines = []
    lines.append(f"Links for {issue_key}:")
    lines.append("")

    outward_links = [l for l in links if "inwardIssue" in l]
    inward_links = [l for l in links if "outwardIssue" in l]

    if outward_links:
        lines.append("Outward (this issue...):")
        for link in outward_links:
            link_type = link["type"]
            target = link["inwardIssue"]
            status = target.get("fields", {}).get("status", {}).get("name", "Unknown")
            summary = target.get("fields", {}).get("summary", "")
            if len(summary) > 50:
                summary = summary[:47] + "..."
            lines.append(f"  {link_type['outward']} -> {target['key']} [{status}] {summary}")
        lines.append("")

    if inward_links:
        lines.append("Inward (...this issue):")
        for link in inward_links:
            link_type = link["type"]
            source = link["outwardIssue"]
            status = source.get("fields", {}).get("status", {}).get("name", "Unknown")
            summary = source.get("fields", {}).get("summary", "")
            if len(summary) > 50:
                summary = summary[:47] + "..."
            lines.append(f"  {link_type['inward']} <- {source['key']} [{status}] {summary}")
        lines.append("")

    lines.append(f"Total: {len(links)} link(s)")

    return "\n".join(lines)


def _format_blockers(result: dict[str, Any]) -> str:
    """Format blockers for text output."""
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

    for blocker in blockers:
        status = blocker.get("status", "Unknown")
        summary = blocker.get("summary", "")[:50]
        status_mark = " ✓" if status == "Done" else ""
        lines.append(f"  {blocker['key']} [{status}] {summary}{status_mark}")

    lines.append("")

    total = result.get("total", len(blockers))
    if result.get("recursive"):
        all_blockers = result.get("all_blockers", [])
        done_count = sum(1 for b in all_blockers if b.get("status") == "Done")
        lines.append(f"Total: {total} blocker(s) ({done_count} resolved, {total - done_count} unresolved)")

        if result.get("circular"):
            lines.append("Warning: Circular dependency detected!")
    else:
        lines.append(f"Total: {total} direct blocker(s)")

    return "\n".join(lines)


def _format_dependencies(result: dict[str, Any], output_format: str = "text") -> str:
    """Format dependencies for output."""
    if output_format == "json":
        return json.dumps(result, indent=2)

    issue_key = result["issue_key"]
    dependencies = result.get("dependencies", [])

    if output_format == "mermaid":
        return _format_mermaid(issue_key, dependencies)
    elif output_format == "dot":
        return _format_dot(issue_key, dependencies)
    elif output_format == "plantuml":
        return _format_plantuml(issue_key, dependencies)
    elif output_format == "d2":
        return _format_d2(issue_key, dependencies)

    if not dependencies:
        return f"No dependencies found for {issue_key}"

    lines = []
    lines.append(f"Dependencies for {issue_key}:")
    lines.append("")

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

    status_summary = result.get("status_summary", {})
    if status_summary:
        lines.append("Status Summary:")
        for status, count in sorted(status_summary.items()):
            lines.append(f"  {status}: {count}")
        lines.append("")

    lines.append(f"Total: {result['total']} dependency(ies)")

    return "\n".join(lines)


def _format_link_types(link_types: list) -> str:
    """Format link types for text output."""
    if not link_types:
        return "No link types found."

    name_width = max(len(lt["name"]) for lt in link_types)
    outward_width = max(len(lt.get("outward", "")) for lt in link_types)
    inward_width = max(len(lt.get("inward", "")) for lt in link_types)

    name_width = max(name_width, 4)
    outward_width = max(outward_width, 7)
    inward_width = max(inward_width, 6)

    lines = []
    lines.append("Available Link Types:")
    lines.append("")
    header = f"{'Name':<{name_width}}  {'Outward':<{outward_width}}  {'Inward':<{inward_width}}"
    lines.append(header)
    lines.append("─" * name_width + "  " + "─" * outward_width + "  " + "─" * inward_width)

    for lt in link_types:
        row = f"{lt['name']:<{name_width}}  {lt.get('outward', ''):<{outward_width}}  {lt.get('inward', ''):<{inward_width}}"
        lines.append(row)

    lines.append("")
    lines.append(f"Total: {len(link_types)} link type(s)")

    return "\n".join(lines)


def _format_clone_result(result: dict[str, Any]) -> str:
    """Format clone result for text output."""
    lines = []
    lines.append(f"Cloned {result['original_key']} -> {result['clone_key']}")
    lines.append(f"  Project: {result.get('project', 'N/A')}")

    if result.get("clone_link_created"):
        lines.append("  Clone link: Created")

    if result.get("links_copied", 0) > 0:
        lines.append(f"  Links copied: {result['links_copied']}")

    if result.get("subtasks_cloned", 0) > 0:
        lines.append(f"  Subtasks cloned: {result['subtasks_cloned']}")

    return "\n".join(lines)


def _format_bulk_result(result: dict[str, Any]) -> str:
    """Format bulk link result for text output."""
    lines = []

    target = result.get("target", "Unknown")
    link_type = result.get("link_type", "Unknown")

    if result.get("dry_run"):
        lines.append(f"[DRY RUN] Would create {result.get('would_create', 0)} links:")
        lines.append(f"  Target: {target}")
        lines.append(f"  Link type: {link_type}")
        issues = result.get("issues", [])
        for issue in issues[:10]:
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


def _format_single_issue_stats(stats: dict[str, Any]) -> str:
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
            lines.append(f"  {linked['key']} [{linked['status']}] ({linked['link_type']})")

    return "\n".join(lines)


def _format_project_stats(stats: dict[str, Any], top: int = 10) -> str:
    """Format stats for multiple issues."""
    lines = []
    lines.append("Link Statistics Report")
    lines.append("=" * 50)
    lines.append("")

    lines.append(f"Query: {stats['jql']}")
    lines.append(f"Issues Analyzed: {stats['issues_analyzed']} of {stats['total_matching']}")
    lines.append(f"Total Links: {stats['total_links']}")
    lines.append("")

    lines.append("Link Direction:")
    lines.append(f"  Outward: {stats['by_direction']['outward']}")
    lines.append(f"  Inward: {stats['by_direction']['inward']}")
    lines.append("")

    if stats["by_type"]:
        lines.append("Links by Type:")
        for link_type, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
            lines.append(f"  {link_type}: {count}")
        lines.append("")

    lines.append(f"Orphaned Issues (no links): {stats['orphaned_count']}")
    if stats["orphaned_issues"][:5]:
        for orphan in stats["orphaned_issues"][:5]:
            lines.append(f"  {orphan['key']}: {orphan['summary']}")
        if stats["orphaned_count"] > 5:
            lines.append(f"  ... and {stats['orphaned_count'] - 5} more")
    lines.append("")

    if stats["most_connected"]:
        lines.append(f"Most Connected Issues (top {min(top, len(stats['most_connected']))}):")
        for issue in stats["most_connected"][:top]:
            lines.append(f"  {issue['key']} ({issue['link_count']} links): {issue['summary']}")
        lines.append("")

    if stats["by_status"]:
        lines.append("Linked Issues by Status:")
        for status, count in sorted(stats["by_status"].items(), key=lambda x: -x[1]):
            lines.append(f"  {status}: {count}")

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def relationships():
    """Commands for managing issue links and dependencies."""
    pass


@relationships.command(name="link")
@click.argument("source_issue")
@click.option("--blocks", help="Issue that this issue blocks")
@click.option("--is-blocked-by", help="Issue that blocks this issue")
@click.option("--relates-to", help="Issue that this issue relates to")
@click.option("--duplicates", help="Issue that this issue duplicates")
@click.option("--clones", help="Issue that this issue clones")
@click.option("--type", "-t", "link_type", help="Explicit link type name")
@click.option("--to", "target", help="Target issue (use with --type)")
@click.option("--comment", "-c", help="Add comment with the link")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.pass_context
@handle_jira_errors
def relationships_link(
    ctx,
    source_issue: str,
    blocks: str,
    is_blocked_by: str,
    relates_to: str,
    duplicates: str,
    clones: str,
    link_type: str,
    target: str,
    comment: str,
    dry_run: bool,
):
    """Create a link between two issues."""
    link_opts = [blocks, is_blocked_by, relates_to, duplicates, clones]
    explicit_opts = link_type and target
    if sum(1 for opt in link_opts if opt) + (1 if explicit_opts else 0) != 1:
        raise click.UsageError(
            "Specify exactly one link type: --blocks, --relates-to, --duplicates, --clones, --is-blocked-by, or --type with --to"
        )

    result = _link_issue_impl(
        issue_key=source_issue,
        blocks=blocks,
        duplicates=duplicates,
        relates_to=relates_to,
        clones=clones,
        is_blocked_by=is_blocked_by,
        link_type=link_type,
        target_issue=target,
        comment=comment,
        dry_run=dry_run,
    )

    if dry_run and result:
        click.echo(f"[DRY RUN] Would create link: {result['preview']}")
    else:
        actual_target = blocks or is_blocked_by or relates_to or duplicates or clones or target
        click.echo(f"Linked {source_issue} to {actual_target}")


@relationships.command(name="unlink")
@click.argument("source_issue")
@click.argument("target_issue", required=False)
@click.option("--type", "-t", "link_type", help="Link type to remove (use with --all)")
@click.option("--all", "-a", "remove_all", is_flag=True, help="Remove all links of specified type")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without deleting")
@click.pass_context
@handle_jira_errors
def relationships_unlink(
    ctx,
    source_issue: str,
    target_issue: str,
    link_type: str,
    remove_all: bool,
    dry_run: bool,
):
    """Remove a link between two issues."""
    if not target_issue and not (link_type and remove_all):
        raise click.UsageError(
            "Specify TARGET_ISSUE or use --type TYPE with --all to remove all links of a type"
        )

    result = _unlink_issue_impl(
        issue_key=source_issue,
        from_issue=target_issue,
        link_type=link_type,
        remove_all=remove_all,
        dry_run=dry_run,
    )

    if dry_run:
        click.echo(f"[DRY RUN] Would remove {len(result['links_to_delete'])} link(s):")
        for link in result["links_to_delete"]:
            click.echo(f"  - {link['direction']} {link['target']} ({link['type']})")
    else:
        count = result.get("deleted_count", 0)
        if target_issue:
            click.echo(f"Removed link between {source_issue} and {target_issue}")
        else:
            click.echo(f"Removed {count} '{link_type}' link(s) from {source_issue}")


@relationships.command(name="get-links")
@click.argument("issue_key")
@click.option("--type", "-t", "link_type", help="Filter by link type")
@click.option(
    "--direction", "-d",
    type=click.Choice(["inward", "outward", "both"]),
    default="both",
    help="Link direction",
)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def relationships_get_links(ctx, issue_key: str, link_type: str, direction: str, output: str):
    """Get all links for an issue."""
    dir_filter = None if direction == "both" else direction
    links = _get_links_impl(issue_key, direction=dir_filter, link_type=link_type)

    if output == "json":
        click.echo(format_json(links))
    else:
        click.echo(_format_links(links, issue_key))


@relationships.command(name="get-blockers")
@click.argument("issue_key")
@click.option("--recursive", "-r", is_flag=True, help="Show full blocker chain")
@click.option("--include-done", is_flag=True, help="Include completed blockers")
@click.option("--depth", type=int, default=0, help="Max recursion depth (0=unlimited)")
@click.option("--direction", "-d", type=click.Choice(["inward", "outward"]), default="inward")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def relationships_get_blockers(
    ctx, issue_key: str, recursive: bool, include_done: bool, depth: int, direction: str, output: str
):
    """Get issues blocking this issue."""
    result = _get_blockers_impl(
        issue_key=issue_key,
        direction=direction,
        recursive=recursive,
        max_depth=depth,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_blockers(result))


@relationships.command(name="get-dependencies")
@click.argument("issue_key")
@click.option("--type", "-t", "link_types", help="Comma-separated link types to include")
@click.option(
    "--output", "-o",
    type=click.Choice(["text", "json", "mermaid", "dot", "plantuml", "d2"]),
    default="text",
    help="Output format",
)
@click.pass_context
@handle_jira_errors
def relationships_get_dependencies(ctx, issue_key: str, link_types: str, output: str):
    """Get dependency tree for an issue."""
    types_list = link_types.split(",") if link_types else None
    result = _get_dependencies_impl(issue_key=issue_key, link_types=types_list)

    click.echo(_format_dependencies(result, output_format=output))


@relationships.command(name="link-types")
@click.option("--filter", "-f", "filter_pattern", help="Filter link types by name pattern")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def relationships_link_types(ctx, filter_pattern: str, output: str):
    """List available link types."""
    link_types = _get_link_types_impl(filter_pattern=filter_pattern)

    if output == "json":
        click.echo(format_json(link_types))
    else:
        click.echo(_format_link_types(link_types))


@relationships.command(name="clone")
@click.argument("issue_key")
@click.option("--to-project", "-p", help="Target project key")
@click.option("--summary", "-s", help="Custom summary for cloned issue")
@click.option("--clone-links", "-l", is_flag=True, help="Clone issue links")
@click.option("--clone-subtasks", is_flag=True, help="Clone subtasks")
@click.option("--no-link", is_flag=True, help="Do not create 'clones' link to original")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def relationships_clone(
    ctx,
    issue_key: str,
    to_project: str,
    summary: str,
    clone_links: bool,
    clone_subtasks: bool,
    no_link: bool,
    output: str,
):
    """Clone an issue with optional links and subtasks."""
    result = _clone_issue_impl(
        issue_key=issue_key,
        to_project=to_project,
        summary=summary,
        include_subtasks=clone_subtasks,
        include_links=clone_links,
        create_clone_link=not no_link,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_clone_result(result))


@relationships.command(name="bulk-link")
@click.option("--jql", "-j", help="JQL query to find issues")
@click.option("--issues", "-i", help="Comma-separated issue keys")
@click.option("--blocks", help="Issue that source issues block")
@click.option("--is-blocked-by", help="Issue that blocks source issues")
@click.option("--relates-to", help="Issue that source issues relate to")
@click.option("--duplicates", help="Issue that source issues duplicate")
@click.option("--clones", help="Issue that source issues clone")
@click.option("--type", "-t", "link_type", help="Explicit link type name")
@click.option("--to", "target", help="Target issue (use with --type)")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without making changes")
@click.option("--skip-existing", is_flag=True, help="Skip already linked issues")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def relationships_bulk_link(
    ctx,
    jql: str,
    issues: str,
    blocks: str,
    is_blocked_by: str,
    relates_to: str,
    duplicates: str,
    clones: str,
    link_type: str,
    target: str,
    dry_run: bool,
    skip_existing: bool,
    output: str,
):
    """Link multiple issues to a target issue."""
    if not jql and not issues:
        raise click.UsageError("Either --jql or --issues is required")
    if jql and issues:
        raise click.UsageError("--jql and --issues are mutually exclusive")

    link_opts = [blocks, is_blocked_by, relates_to, duplicates, clones]
    explicit_opts = link_type and target
    if sum(1 for opt in link_opts if opt) + (1 if explicit_opts else 0) != 1:
        raise click.UsageError(
            "Specify exactly one link type: --blocks, --relates-to, etc., or --type with --to"
        )

    # Determine target and link type
    resolved_target = None
    resolved_link_type = None

    if blocks:
        resolved_target = blocks
        resolved_link_type = "Blocks"
    elif is_blocked_by:
        resolved_target = is_blocked_by
        resolved_link_type = "Blocks"
    elif relates_to:
        resolved_target = relates_to
        resolved_link_type = "Relates"
    elif duplicates:
        resolved_target = duplicates
        resolved_link_type = "Duplicate"
    elif clones:
        resolved_target = clones
        resolved_link_type = "Cloners"
    elif link_type and target:
        resolved_link_type = link_type
        resolved_target = target

    issues_list = [k.strip() for k in issues.split(",")] if issues else None

    result = _bulk_link_impl(
        issues=issues_list,
        jql=jql,
        target=resolved_target,
        link_type=resolved_link_type,
        dry_run=dry_run,
        skip_existing=skip_existing,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_bulk_result(result))


@relationships.command(name="stats")
@click.argument("key_or_project", required=False)
@click.option("--project", "-p", help="Project key to analyze all issues")
@click.option("--jql", "-j", help="JQL query to find issues to analyze")
@click.option("--top", "-t", type=int, default=10, help="Number of most-connected issues to show")
@click.option("--max-results", "-m", type=int, default=500, help="Maximum issues to analyze")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
@handle_jira_errors
def relationships_stats(
    ctx,
    key_or_project: str,
    project: str,
    jql: str,
    top: int,
    max_results: int,
    output: str,
):
    """Get link statistics for an issue or project."""
    options_set = sum(1 for opt in [key_or_project, project, jql] if opt)
    if options_set == 0:
        raise click.UsageError("Specify ISSUE_KEY, --project, or --jql")
    if options_set > 1:
        raise click.UsageError("Specify only one of: ISSUE_KEY, --project, or --jql")

    if key_or_project:
        # Determine if it's an issue key or project key
        if "-" in key_or_project:
            stats = _get_link_stats_impl(issue_key=key_or_project)
            if output == "json":
                click.echo(format_json(stats))
            else:
                click.echo(_format_single_issue_stats(stats))
        else:
            stats = _get_link_stats_impl(project=key_or_project, max_results=max_results)
            if output == "json":
                click.echo(format_json(stats))
            else:
                click.echo(_format_project_stats(stats, top=top))
    elif project:
        stats = _get_link_stats_impl(project=project, max_results=max_results)
        if output == "json":
            click.echo(format_json(stats))
        else:
            click.echo(_format_project_stats(stats, top=top))
    elif jql:
        stats = _get_link_stats_impl(jql=jql, max_results=max_results)
        if output == "json":
            click.echo(format_json(stats))
        else:
            click.echo(_format_project_stats(stats, top=top))
