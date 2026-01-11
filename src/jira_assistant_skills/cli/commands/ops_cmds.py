"""
CLI commands for cache management and operational utilities.

This module contains all logic for jira-ops operations.
All implementation functions are inlined for direct CLI usage.
"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click

from jira_assistant_skills_lib import (
    JiraCache,
    JiraError,
    get_jira_client,
)

from jira_assistant_skills.cli.cli_utils import format_json, handle_jira_errors


# =============================================================================
# Helper Functions
# =============================================================================


def _format_bytes(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _is_critical_error(e: Exception) -> bool:
    """Check if an exception is a critical error that should stop execution."""
    try:
        from jira_assistant_skills_lib import (
            AuthenticationError,
            RateLimitError,
            ServerError,
        )
        if isinstance(e, (AuthenticationError, RateLimitError, ServerError)):
            return True
    except ImportError:
        pass

    try:
        import requests
        if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True
    except ImportError:
        pass

    return False


# =============================================================================
# Implementation Functions - Cache Status
# =============================================================================


def _cache_status_impl(
    verbose: bool = False,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """
    Get cache statistics.

    Args:
        verbose: Include detailed information
        cache_dir: Optional custom cache directory

    Returns:
        Dict with cache statistics
    """
    cache = JiraCache(cache_dir=cache_dir)
    stats = cache.get_stats()

    return {
        "total_size_bytes": stats.total_size_bytes,
        "max_size_bytes": cache.max_size,
        "entry_count": stats.entry_count,
        "hits": stats.hits,
        "misses": stats.misses,
        "hit_rate": stats.hit_rate,
        "by_category": stats.by_category,
    }


# =============================================================================
# Implementation Functions - Cache Clear
# =============================================================================


def _cache_clear_impl(
    category: str | None = None,
    pattern: str | None = None,
    key: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """
    Clear cache entries.

    Args:
        category: Category to clear (issue, project, user, field, search, default)
        pattern: Pattern to match keys (glob style)
        key: Specific key to clear (requires category)
        dry_run: If True, don't actually clear
        force: Skip confirmation prompt
        cache_dir: Optional custom cache directory

    Returns:
        Dict with clear results
    """
    cache = JiraCache(cache_dir=cache_dir)
    stats_before = cache.get_stats()

    # Build description
    if key:
        if not category:
            raise ValueError("--key requires --category")
        description = f"key '{key}' in category '{category}'"
    elif pattern:
        if category:
            description = f"keys matching '{pattern}' in category '{category}'"
        else:
            description = f"keys matching '{pattern}' in all categories"
    elif category:
        description = f"all entries in category '{category}'"
    else:
        description = "all cache entries"

    result = {
        "description": description,
        "entries_before": stats_before.entry_count,
        "size_before_bytes": stats_before.total_size_bytes,
        "dry_run": dry_run,
        "cleared_count": 0,
        "freed_bytes": 0,
    }

    if dry_run:
        return result

    # Perform clear
    if key:
        count = cache.invalidate(key=key, category=category)
    elif pattern:
        count = cache.invalidate(pattern=pattern, category=category)
    elif category:
        count = cache.invalidate(category=category)
    else:
        count = cache.clear()

    stats_after = cache.get_stats()
    freed = stats_before.total_size_bytes - stats_after.total_size_bytes

    result["cleared_count"] = count
    result["freed_bytes"] = freed
    result["entries_after"] = stats_after.entry_count
    result["size_after_bytes"] = stats_after.total_size_bytes

    return result


# =============================================================================
# Implementation Functions - Cache Warm
# =============================================================================


def _warm_projects(client, cache, verbose: bool = False) -> tuple[int, Exception | None]:
    """Fetch and cache project list."""
    if verbose:
        click.echo("Fetching projects...")

    try:
        response = client.get("/rest/api/3/project", operation="fetch projects")

        for project in response:
            key = cache.generate_key("project", project["key"])
            cache.set(key, project, category="project")

        count = len(response) if isinstance(response, list) else 1
        if verbose:
            click.echo(f"  Cached {count} projects")
        return count, None
    except Exception as e:
        if verbose:
            click.echo(f"  Error fetching projects: {e}", err=True)
        if _is_critical_error(e):
            return 0, e
        return 0, None


def _warm_fields(client, cache, verbose: bool = False) -> tuple[int, Exception | None]:
    """Fetch and cache field definitions."""
    if verbose:
        click.echo("Fetching fields...")

    try:
        response = client.get("/rest/api/3/field", operation="fetch fields")

        for field in response:
            key = cache.generate_key("field", field["id"])
            cache.set(key, field, category="field")

        # Cache full list
        all_fields_key = cache.generate_key("field", "all")
        cache.set(all_fields_key, response, category="field")

        count = len(response) if isinstance(response, list) else 1
        if verbose:
            click.echo(f"  Cached {count} fields")
        return count, None
    except Exception as e:
        if verbose:
            click.echo(f"  Error fetching fields: {e}", err=True)
        if _is_critical_error(e):
            return 0, e
        return 0, None


def _warm_issue_types(client, cache, verbose: bool = False) -> tuple[int, Exception | None]:
    """Fetch and cache issue type definitions."""
    if verbose:
        click.echo("Fetching issue types...")

    try:
        response = client.get("/rest/api/3/issuetype", operation="fetch issue types")

        for issue_type in response:
            key = cache.generate_key("field", "issuetype", issue_type["id"])
            cache.set(key, issue_type, category="field")

        # Cache full list
        all_types_key = cache.generate_key("field", "issuetypes", "all")
        cache.set(all_types_key, response, category="field")

        count = len(response) if isinstance(response, list) else 1
        if verbose:
            click.echo(f"  Cached {count} issue types")
        return count, None
    except Exception as e:
        if verbose:
            click.echo(f"  Error fetching issue types: {e}", err=True)
        if _is_critical_error(e):
            return 0, e
        return 0, None


def _warm_priorities(client, cache, verbose: bool = False) -> tuple[int, Exception | None]:
    """Fetch and cache priority definitions."""
    if verbose:
        click.echo("Fetching priorities...")

    try:
        response = client.get("/rest/api/3/priority", operation="fetch priorities")

        for priority in response:
            key = cache.generate_key("field", "priority", priority["id"])
            cache.set(key, priority, category="field")

        # Cache full list
        all_key = cache.generate_key("field", "priorities", "all")
        cache.set(all_key, response, category="field")

        count = len(response) if isinstance(response, list) else 1
        if verbose:
            click.echo(f"  Cached {count} priorities")
        return count, None
    except Exception as e:
        if verbose:
            click.echo(f"  Error fetching priorities: {e}", err=True)
        if _is_critical_error(e):
            return 0, e
        return 0, None


def _warm_statuses(client, cache, verbose: bool = False) -> tuple[int, Exception | None]:
    """Fetch and cache status definitions."""
    if verbose:
        click.echo("Fetching statuses...")

    try:
        response = client.get("/rest/api/3/status", operation="fetch statuses")

        for status in response:
            key = cache.generate_key("field", "status", status["id"])
            cache.set(key, status, category="field")

        # Cache full list
        all_key = cache.generate_key("field", "statuses", "all")
        cache.set(all_key, response, category="field")

        count = len(response) if isinstance(response, list) else 1
        if verbose:
            click.echo(f"  Cached {count} statuses")
        return count, None
    except Exception as e:
        if verbose:
            click.echo(f"  Error fetching statuses: {e}", err=True)
        if _is_critical_error(e):
            return 0, e
        return 0, None


def _cache_warm_impl(
    projects: bool = False,
    fields: bool = False,
    users: bool = False,
    warm_all: bool = False,
    verbose: bool = False,
    cache_dir: str | None = None,
) -> dict[str, Any]:
    """
    Pre-warm cache with commonly accessed data.

    Args:
        projects: Cache project list
        fields: Cache field definitions
        users: Cache assignable users
        warm_all: Cache all available metadata
        verbose: Verbose output
        cache_dir: Optional custom cache directory

    Returns:
        Dict with warming results
    """
    if not any([projects, fields, users, warm_all]):
        raise ValueError("At least one warming option is required")

    client = get_jira_client()
    cache = JiraCache(cache_dir=cache_dir)

    try:
        total_cached = 0
        critical_errors = []
        warmed = []

        if warm_all or projects:
            count, error = _warm_projects(client, cache, verbose)
            total_cached += count
            if count > 0:
                warmed.append("projects")
            if error:
                critical_errors.append(str(error))

        if warm_all or fields:
            count, error = _warm_fields(client, cache, verbose)
            total_cached += count
            if count > 0:
                warmed.append("fields")
            if error:
                critical_errors.append(str(error))

            count, error = _warm_issue_types(client, cache, verbose)
            total_cached += count
            if count > 0:
                warmed.append("issue_types")
            if error:
                critical_errors.append(str(error))

            count, error = _warm_priorities(client, cache, verbose)
            total_cached += count
            if count > 0:
                warmed.append("priorities")
            if error:
                critical_errors.append(str(error))

            count, error = _warm_statuses(client, cache, verbose)
            total_cached += count
            if count > 0:
                warmed.append("statuses")
            if error:
                critical_errors.append(str(error))

        stats = cache.get_stats()

        result = {
            "total_cached": total_cached,
            "warmed": warmed,
            "cache_size_bytes": stats.total_size_bytes,
            "entry_count": stats.entry_count,
        }

        if critical_errors:
            result["errors"] = critical_errors

        return result
    finally:
        client.close()


# =============================================================================
# Implementation Functions - Discover Project
# =============================================================================


def _discover_metadata(client, project_key: str, verbose: bool = False) -> dict[str, Any]:
    """Fetch project metadata from JIRA."""
    if verbose:
        click.echo(f"Discovering metadata for {project_key}...")

    metadata = {
        "project_key": project_key,
        "discovered_at": datetime.utcnow().isoformat() + "Z",
    }

    # Get project info
    project = client.get_project(project_key, expand=["lead", "description"])
    metadata["project_name"] = project.get("name", project_key)
    metadata["project_type"] = project.get("projectTypeKey", "software")
    metadata["is_team_managed"] = project.get("simplified", False)

    if project.get("lead"):
        metadata["project_lead"] = {
            "account_id": project["lead"].get("accountId"),
            "display_name": project["lead"].get("displayName"),
        }

    # Get issue types with statuses
    if verbose:
        click.echo("  Fetching issue types and statuses...")
    statuses_by_type = client.get_project_statuses(project_key)

    issue_types = []
    for item in statuses_by_type:
        issue_type = {
            "id": item.get("id"),
            "name": item.get("name"),
            "subtask": item.get("subtask", False),
            "statuses": [s.get("name") for s in item.get("statuses", [])],
        }
        issue_types.append(issue_type)

    metadata["issue_types"] = issue_types
    if verbose:
        click.echo(f"    Found {len(issue_types)} issue types")

    # Get components
    if verbose:
        click.echo("  Fetching components...")
    components = client.get_project_components(project_key)
    metadata["components"] = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "description": c.get("description"),
            "lead": c.get("lead", {}).get("displayName") if c.get("lead") else None,
        }
        for c in components
    ]
    if verbose:
        click.echo(f"    Found {len(metadata['components'])} components")

    # Get versions
    if verbose:
        click.echo("  Fetching versions...")
    versions = client.get_project_versions(project_key)
    metadata["versions"] = [
        {
            "id": v.get("id"),
            "name": v.get("name"),
            "description": v.get("description"),
            "released": v.get("released", False),
            "archived": v.get("archived", False),
            "release_date": v.get("releaseDate"),
        }
        for v in versions
    ]
    if verbose:
        click.echo(f"    Found {len(metadata['versions'])} versions")

    # Get priorities
    if verbose:
        click.echo("  Fetching priorities...")
    try:
        priorities = client.get("/rest/api/3/priority")
        metadata["priorities"] = [
            {"id": p.get("id"), "name": p.get("name")} for p in priorities
        ]
        if verbose:
            click.echo(f"    Found {len(metadata['priorities'])} priorities")
    except Exception:
        metadata["priorities"] = []

    # Get assignable users
    if verbose:
        click.echo("  Fetching assignable users...")
    try:
        users = client.find_assignable_users("", project_key, max_results=100)
        metadata["assignable_users"] = [
            {
                "account_id": u.get("accountId"),
                "display_name": u.get("displayName"),
                "email": u.get("emailAddress"),
            }
            for u in users
        ]
        if verbose:
            click.echo(f"    Found {len(metadata['assignable_users'])} assignable users")
    except Exception:
        metadata["assignable_users"] = []

    return metadata


def _discover_patterns(
    client,
    project_key: str,
    sample_size: int = 100,
    sample_period_days: int = 30,
    verbose: bool = False,
) -> dict[str, Any]:
    """Analyze recent issues to discover usage patterns."""
    if verbose:
        click.echo(f"Discovering patterns (last {sample_period_days} days, up to {sample_size} issues)...")

    patterns = {
        "project_key": project_key,
        "sample_size": 0,
        "sample_period_days": sample_period_days,
        "discovered_at": datetime.utcnow().isoformat() + "Z",
        "by_issue_type": {},
        "common_labels": [],
        "top_assignees": [],
    }

    # Build JQL for recent issues
    since_date = (datetime.utcnow() - timedelta(days=sample_period_days)).strftime("%Y-%m-%d")
    jql = f'project = "{project_key}" AND created >= "{since_date}" ORDER BY created DESC'

    fields = [
        "issuetype", "assignee", "reporter", "priority",
        "labels", "components", "status", "customfield_10016",
    ]

    try:
        results = client.search_issues(jql, fields=fields, max_results=sample_size)
        issues = results.get("issues", [])
        patterns["sample_size"] = len(issues)
        if verbose:
            click.echo(f"  Sampled {len(issues)} issues")
    except Exception as e:
        if verbose:
            click.echo(f"  Could not sample issues: {e}", err=True)
        return patterns

    if not issues:
        return patterns

    # Aggregate by issue type
    by_type: dict[str, dict] = defaultdict(lambda: {
        "issue_count": 0,
        "assignees": defaultdict(lambda: {"count": 0, "display_name": ""}),
        "labels": defaultdict(int),
        "components": defaultdict(int),
        "priorities": defaultdict(int),
        "story_points": [],
    })

    all_labels: dict[str, int] = defaultdict(int)
    all_assignees: dict[str, dict] = defaultdict(lambda: {"count": 0, "display_name": ""})

    for issue in issues:
        fields_data = issue.get("fields", {})
        issue_type = fields_data.get("issuetype", {}).get("name", "Unknown")

        type_data = by_type[issue_type]
        type_data["issue_count"] += 1

        # Assignee
        assignee = fields_data.get("assignee")
        if assignee:
            account_id = assignee.get("accountId", "unknown")
            display_name = assignee.get("displayName", "Unknown")
            type_data["assignees"][account_id]["count"] += 1
            type_data["assignees"][account_id]["display_name"] = display_name
            all_assignees[account_id]["count"] += 1
            all_assignees[account_id]["display_name"] = display_name

        # Labels
        labels = fields_data.get("labels", [])
        for label in labels:
            type_data["labels"][label] += 1
            all_labels[label] += 1

        # Components
        components = fields_data.get("components", [])
        for comp in components:
            comp_name = comp.get("name", "Unknown")
            type_data["components"][comp_name] += 1

        # Priority
        priority = fields_data.get("priority")
        if priority:
            priority_name = priority.get("name", "Unknown")
            type_data["priorities"][priority_name] += 1

        # Story points
        story_points = fields_data.get("customfield_10016")
        if story_points is not None:
            type_data["story_points"].append(story_points)

    # Convert to final format
    for type_name, type_data in by_type.items():
        issue_count = type_data["issue_count"]

        assignees = {}
        for account_id, data in type_data["assignees"].items():
            assignees[account_id] = {
                "display_name": data["display_name"],
                "count": data["count"],
                "percentage": round(data["count"] / issue_count * 100, 1),
            }

        priorities = {}
        for priority_name, count in type_data["priorities"].items():
            priorities[priority_name] = {
                "count": count,
                "percentage": round(count / issue_count * 100, 1),
            }

        story_points_list = type_data["story_points"]
        story_points_info = {}
        if story_points_list:
            story_points_info = {
                "avg": round(sum(story_points_list) / len(story_points_list), 1),
            }

        patterns["by_issue_type"][type_name] = {
            "issue_count": issue_count,
            "assignees": assignees,
            "labels": dict(type_data["labels"]),
            "components": dict(type_data["components"]),
            "priorities": priorities,
            "story_points": story_points_info,
        }

    # Common labels
    sorted_labels = sorted(all_labels.items(), key=lambda x: x[1], reverse=True)
    patterns["common_labels"] = [label for label, _ in sorted_labels[:20]]

    # Top assignees
    sorted_assignees = sorted(all_assignees.items(), key=lambda x: x[1]["count"], reverse=True)
    patterns["top_assignees"] = [
        {
            "account_id": account_id,
            "display_name": data["display_name"],
            "total_assignments": data["count"],
        }
        for account_id, data in sorted_assignees[:20]
    ]

    if verbose:
        click.echo(f"  Found {len(patterns['by_issue_type'])} issue types with patterns")

    return patterns


def _discover_project_impl(
    project_key: str,
    sample_size: int = 100,
    sample_period_days: int = 30,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Discover project context.

    Args:
        project_key: JIRA project key
        sample_size: Number of issues to sample
        sample_period_days: How many days back to sample
        verbose: Verbose output

    Returns:
        Dict with discovered context
    """
    project_key = project_key.upper()

    client = get_jira_client()
    try:
        metadata = _discover_metadata(client, project_key, verbose)
        patterns = _discover_patterns(client, project_key, sample_size, sample_period_days, verbose)

        return {
            "metadata": metadata,
            "patterns": patterns,
        }
    finally:
        client.close()


# =============================================================================
# Formatting Functions
# =============================================================================


def _format_cache_status(stats: dict, verbose: bool = False) -> str:
    """Format cache status for text output."""
    lines = ["\nCache Statistics:"]
    lines.append(f"  Total Size: {_format_bytes(stats['total_size_bytes'])} / {_format_bytes(stats['max_size_bytes'])}")
    lines.append(f"  Entries: {stats['entry_count']:,}")

    if stats['hits'] + stats['misses'] > 0:
        lines.append(f"  Hit Rate: {stats['hit_rate'] * 100:.1f}% ({stats['hits']:,} hits, {stats['misses']:,} misses)")
    else:
        lines.append("  Hit Rate: N/A (no requests)")

    if stats.get('by_category'):
        lines.append("\nBy Category:")
        for category, cat_stats in sorted(stats['by_category'].items()):
            lines.append(f"  {category}: {cat_stats['count']:,} entries, {_format_bytes(cat_stats['size_bytes'])}")
    else:
        lines.append("\nNo cached entries.")

    lines.append("")
    return "\n".join(lines)


def _format_cache_clear(result: dict) -> str:
    """Format cache clear result for text output."""
    if result["dry_run"]:
        lines = [
            f"DRY RUN: Would clear {result['description']}",
            f"  Current entries: {result['entries_before']:,}",
            f"  Current size: {result['size_before_bytes'] / (1024 * 1024):.1f} MB",
        ]
    else:
        lines = [
            f"Cleared {result['cleared_count']:,} cache entries.",
            f"Freed {result['freed_bytes'] / (1024 * 1024):.1f} MB",
        ]
    return "\n".join(lines)


def _format_cache_warm(result: dict) -> str:
    """Format cache warm result for text output."""
    lines = [
        f"\nCache warming complete. Cached {result['total_cached']} items.",
        f"Total cache size: {result['cache_size_bytes'] / (1024 * 1024):.1f} MB",
    ]

    if result.get('errors'):
        lines.append(f"\nWarnings:")
        for err in result['errors']:
            lines.append(f"  - {err}")

    return "\n".join(lines)


def _format_discover_project(context: dict) -> str:
    """Format discover project result for text output."""
    metadata = context.get("metadata", {})
    patterns = context.get("patterns", {})

    lines = [
        f"\nProject: {metadata.get('project_key')}",
        f"  Name: {metadata.get('project_name')}",
        f"  Type: {metadata.get('project_type')}",
        f"  Team-managed: {metadata.get('is_team_managed', False)}",
        "",
        f"Issue Types: {len(metadata.get('issue_types', []))}",
        f"Components: {len(metadata.get('components', []))}",
        f"Versions: {len(metadata.get('versions', []))}",
        f"Assignable Users: {len(metadata.get('assignable_users', []))}",
        "",
        f"Pattern Analysis:",
        f"  Sampled Issues: {patterns.get('sample_size', 0)}",
        f"  Sample Period: {patterns.get('sample_period_days', 30)} days",
    ]

    if patterns.get('top_assignees'):
        top_names = [a['display_name'] for a in patterns['top_assignees'][:3]]
        lines.append(f"  Top Assignees: {', '.join(top_names)}")

    if patterns.get('common_labels'):
        lines.append(f"  Common Labels: {', '.join(patterns['common_labels'][:5])}")

    return "\n".join(lines)


# =============================================================================
# CLI Commands
# =============================================================================


@click.group()
def ops():
    """Commands for cache management and operational utilities."""
    pass


@ops.command(name="cache-status")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
@handle_jira_errors
def ops_cache_status(ctx, output_json: bool, verbose: bool):
    """Show cache status and statistics."""
    result = _cache_status_impl(verbose=verbose)

    if output_json:
        click.echo(format_json(result))
    else:
        click.echo(_format_cache_status(result, verbose))


@ops.command(name="cache-clear")
@click.option(
    "--category", "-c",
    type=click.Choice(["issue", "project", "user", "field", "search", "default"]),
    help="Clear only entries in this category",
)
@click.option("--pattern", help="Clear keys matching glob pattern (e.g., 'PROJ-*')")
@click.option("--key", help="Clear specific cache key (requires --category)")
@click.option("--dry-run", is_flag=True, help="Show what would be cleared without clearing")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation prompt")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
@handle_jira_errors
def ops_cache_clear(
    ctx,
    category: str,
    pattern: str,
    key: str,
    dry_run: bool,
    force: bool,
    output_json: bool,
):
    """Clear cache entries."""
    if key and not category:
        click.echo("Error: --key requires --category", err=True)
        ctx.exit(1)

    # Confirm unless force or dry-run
    if not force and not dry_run:
        # Build description for prompt
        if key:
            description = f"key '{key}' in category '{category}'"
        elif pattern:
            description = f"keys matching '{pattern}'" + (f" in category '{category}'" if category else "")
        elif category:
            description = f"all entries in category '{category}'"
        else:
            description = "all cache entries"

        if not click.confirm(f"Clear {description}?"):
            click.echo("Cancelled.")
            return

    result = _cache_clear_impl(
        category=category,
        pattern=pattern,
        key=key,
        dry_run=dry_run,
        force=force,
    )

    if output_json:
        click.echo(format_json(result))
    else:
        click.echo(_format_cache_clear(result))


@ops.command(name="cache-warm")
@click.option("--projects", is_flag=True, help="Cache project list")
@click.option("--fields", is_flag=True, help="Cache field definitions")
@click.option("--users", is_flag=True, help="Cache assignable users (requires project context)")
@click.option("--all", "warm_all", is_flag=True, help="Cache all available metadata")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
@handle_jira_errors
def ops_cache_warm(
    ctx,
    projects: bool,
    fields: bool,
    users: bool,
    warm_all: bool,
    verbose: bool,
    output_json: bool,
):
    """Pre-warm cache with commonly accessed data."""
    if not any([projects, fields, users, warm_all]):
        click.echo("Error: At least one warming option is required", err=True)
        ctx.exit(1)

    if users:
        click.echo("User caching requires a project context. Use search scripts instead.", err=True)
        return

    result = _cache_warm_impl(
        projects=projects,
        fields=fields,
        users=users,
        warm_all=warm_all,
        verbose=verbose,
    )

    if result.get("errors"):
        click.echo(f"\nCache warming completed with {len(result['errors'])} error(s).", err=True)
        for err in result['errors']:
            click.echo(f"  - {err}", err=True)
        ctx.exit(1)

    if output_json:
        click.echo(format_json(result))
    else:
        click.echo(_format_cache_warm(result))


@ops.command(name="discover-project")
@click.argument("project_key")
@click.option("--sample-size", "-s", type=int, default=100, help="Number of issues to sample for patterns")
@click.option("--days", "-d", type=int, default=30, help="Sample period in days")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
@handle_jira_errors
def ops_discover_project(
    ctx,
    project_key: str,
    sample_size: int,
    days: int,
    output: str,
    verbose: bool,
):
    """Discover project configuration and capabilities."""
    result = _discover_project_impl(
        project_key=project_key,
        sample_size=sample_size,
        sample_period_days=days,
        verbose=verbose,
    )

    if output == "json":
        click.echo(format_json(result))
    else:
        click.echo(_format_discover_project(result))
        click.echo("\nUse --output json to get the full discovery data.")
