#!/usr/bin/env python3
"""
Project context loader for JIRA Assistant Skills.

Provides lazy loading and caching of project-specific context including
metadata, workflows, patterns, and defaults. Context is loaded from:
1. Environment variables (highest priority)
2. settings.local.json (personal overrides)
3. Skill directories (.claude/skills/jira-project-PROJ/)
4. Hardcoded defaults (fallback)
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Module-level cache for session persistence
_context_cache: Dict[str, 'ProjectContext'] = {}


@dataclass
class ProjectContext:
    """Structured project context data."""
    project_key: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    workflows: Dict[str, Any] = field(default_factory=dict)
    patterns: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    source: str = 'none'  # 'skill', 'settings', 'merged', 'none'
    discovered_at: Optional[str] = None

    def has_context(self) -> bool:
        """Check if any context data is available."""
        return bool(self.metadata or self.workflows or self.patterns or self.defaults)

    def get_issue_types(self) -> List[Dict[str, Any]]:
        """Get available issue types."""
        return self.metadata.get('issue_types', [])

    def get_components(self) -> List[Dict[str, Any]]:
        """Get available components."""
        return self.metadata.get('components', [])

    def get_versions(self) -> List[Dict[str, Any]]:
        """Get available versions."""
        return self.metadata.get('versions', [])

    def get_priorities(self) -> List[Dict[str, Any]]:
        """Get available priorities."""
        return self.metadata.get('priorities', [])

    def get_assignable_users(self) -> List[Dict[str, Any]]:
        """Get assignable users."""
        return self.metadata.get('assignable_users', [])


def get_skills_root() -> Path:
    """Get the root path of the skills directory."""
    # This file is at .claude/skills/shared/scripts/lib/project_context.py
    return Path(__file__).parent.parent.parent.parent.parent


def get_project_skill_path(project_key: str) -> Path:
    """Get the path to a project-specific skill directory."""
    return get_skills_root() / 'skills' / f'jira-project-{project_key}'


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists."""
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def load_skill_context(project_key: str) -> Optional[Dict[str, Any]]:
    """
    Load context from a project skill directory.

    Looks for .claude/skills/jira-project-{PROJECT_KEY}/context/

    Returns:
        Dict with 'metadata', 'workflows', 'patterns', 'defaults' keys
        or None if skill directory doesn't exist
    """
    skill_path = get_project_skill_path(project_key)

    if not skill_path.exists():
        return None

    context = {}

    # Load context files
    context_dir = skill_path / 'context'
    if context_dir.exists():
        metadata = load_json_file(context_dir / 'metadata.json')
        if metadata:
            context['metadata'] = metadata

        workflows = load_json_file(context_dir / 'workflows.json')
        if workflows:
            context['workflows'] = workflows

        patterns = load_json_file(context_dir / 'patterns.json')
        if patterns:
            context['patterns'] = patterns

    # Load defaults from skill root
    defaults = load_json_file(skill_path / 'defaults.json')
    if defaults:
        context['defaults'] = defaults

    return context if context else None


def load_settings_context(project_key: str, profile: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load context overrides from settings.local.json.

    Looks for:
    {
      "jira": {
        "profiles": {
          "{profile}": {
            "projects": {
              "{PROJECT_KEY}": {
                "defaults": { ... },
                "metadata": { ... }  # optional overrides
              }
            }
          }
        }
      }
    }

    Returns:
        Dict with context overrides or None if not configured
    """
    # Find settings.local.json
    settings_path = get_skills_root().parent / 'settings.local.json'

    if not settings_path.exists():
        return None

    settings = load_json_file(settings_path)
    if not settings:
        return None

    # Get profile (default to 'production' or from environment)
    if profile is None:
        profile = os.environ.get('JIRA_PROFILE', 'production')

    # Navigate to project config
    jira_config = settings.get('jira', {})
    profiles = jira_config.get('profiles', {})
    profile_config = profiles.get(profile, {})
    projects = profile_config.get('projects', {})
    project_config = projects.get(project_key, {})

    if not project_config:
        return None

    return project_config


def merge_contexts(skill_ctx: Optional[Dict[str, Any]],
                   settings_ctx: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
    """
    Merge settings overrides on top of skill context.

    Returns:
        Tuple of (merged_context, source_string)
    """
    if not skill_ctx and not settings_ctx:
        return {}, 'none'

    if not skill_ctx:
        return settings_ctx, 'settings'

    if not settings_ctx:
        return skill_ctx, 'skill'

    # Deep merge settings on top of skill context
    merged = {}

    for key in ['metadata', 'workflows', 'patterns', 'defaults']:
        skill_data = skill_ctx.get(key, {})
        settings_data = settings_ctx.get(key, {})

        if skill_data and settings_data:
            # Deep merge dicts
            merged[key] = _deep_merge(skill_data, settings_data)
        elif settings_data:
            merged[key] = settings_data
        elif skill_data:
            merged[key] = skill_data

    return merged, 'merged'


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override dict into base dict."""
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def get_project_context(project_key: str,
                        profile: Optional[str] = None,
                        force_refresh: bool = False) -> ProjectContext:
    """
    Lazy-load project context with caching.

    Priority:
    1. Check memory cache (unless force_refresh)
    2. Load from skill directory
    3. Merge with settings.local.json overrides
    4. Cache in memory

    Args:
        project_key: JIRA project key (e.g., 'PROJ')
        profile: JIRA profile to use (default: from env or 'production')
        force_refresh: If True, bypass cache and reload

    Returns:
        ProjectContext with merged data from all sources
    """
    global _context_cache

    cache_key = f"{project_key}:{profile or 'default'}"

    # Check cache unless force refresh
    if not force_refresh and cache_key in _context_cache:
        return _context_cache[cache_key]

    # Load from sources
    skill_ctx = load_skill_context(project_key)
    settings_ctx = load_settings_context(project_key, profile)

    # Merge contexts
    merged, source = merge_contexts(skill_ctx, settings_ctx)

    # Get discovered_at timestamp
    discovered_at = None
    if merged.get('metadata', {}).get('discovered_at'):
        discovered_at = merged['metadata']['discovered_at']
    elif merged.get('patterns', {}).get('discovered_at'):
        discovered_at = merged['patterns']['discovered_at']

    # Create context object
    context = ProjectContext(
        project_key=project_key,
        metadata=merged.get('metadata', {}),
        workflows=merged.get('workflows', {}),
        patterns=merged.get('patterns', {}),
        defaults=merged.get('defaults', {}),
        source=source,
        discovered_at=discovered_at
    )

    # Cache and return
    _context_cache[cache_key] = context
    return context


def clear_context_cache(project_key: Optional[str] = None) -> None:
    """
    Clear the context cache.

    Args:
        project_key: If specified, only clear cache for this project.
                     If None, clear all cached contexts.
    """
    global _context_cache

    if project_key is None:
        _context_cache.clear()
    else:
        keys_to_remove = [k for k in _context_cache if k.startswith(f"{project_key}:")]
        for key in keys_to_remove:
            del _context_cache[key]


def get_defaults_for_issue_type(context: ProjectContext,
                                 issue_type: str) -> Dict[str, Any]:
    """
    Get creation defaults for a specific issue type.

    Merges global defaults with issue-type-specific defaults.

    Args:
        context: ProjectContext object
        issue_type: Issue type name (e.g., 'Bug', 'Story')

    Returns:
        Dict with default values: priority, assignee, labels, components, etc.
    """
    defaults = context.defaults

    # Start with global defaults
    result = dict(defaults.get('global', {}))

    # Merge issue-type-specific defaults
    by_type = defaults.get('by_issue_type', {})
    type_defaults = by_type.get(issue_type, {})

    for key, value in type_defaults.items():
        if key == 'labels' and key in result:
            # Merge label lists
            result[key] = list(set(result[key] + value))
        elif key == 'components' and key in result:
            # Merge component lists
            result[key] = list(set(result[key] + value))
        else:
            result[key] = value

    return result


def get_valid_transitions(context: ProjectContext,
                          issue_type: str,
                          current_status: str) -> List[Dict[str, Any]]:
    """
    Get valid transitions from current status for an issue type.

    Args:
        context: ProjectContext object
        issue_type: Issue type name
        current_status: Current status name

    Returns:
        List of transition dicts with 'id', 'name', 'to_status' keys
    """
    workflows = context.workflows

    by_type = workflows.get('by_issue_type', {})
    type_workflow = by_type.get(issue_type, {})
    transitions = type_workflow.get('transitions', {})

    return transitions.get(current_status, [])


def get_statuses_for_issue_type(context: ProjectContext,
                                 issue_type: str) -> List[Dict[str, Any]]:
    """
    Get all statuses for an issue type.

    Args:
        context: ProjectContext object
        issue_type: Issue type name

    Returns:
        List of status dicts with 'id', 'name', 'category' keys
    """
    workflows = context.workflows

    by_type = workflows.get('by_issue_type', {})
    type_workflow = by_type.get(issue_type, {})

    return type_workflow.get('statuses', [])


def suggest_assignee(context: ProjectContext,
                     issue_type: Optional[str] = None) -> Optional[str]:
    """
    Suggest the most common assignee based on patterns.

    Args:
        context: ProjectContext object
        issue_type: If specified, get top assignee for this type

    Returns:
        Account ID of suggested assignee, or None if no pattern data
    """
    patterns = context.patterns

    if issue_type:
        # Get top assignee for specific issue type
        by_type = patterns.get('by_issue_type', {})
        type_patterns = by_type.get(issue_type, {})
        assignees = type_patterns.get('assignees', {})

        if assignees:
            # Find assignee with highest count
            top = max(assignees.items(), key=lambda x: x[1].get('count', 0))
            return top[0]  # Return account ID

    # Fall back to overall top assignees
    top_assignees = patterns.get('top_assignees', [])
    if top_assignees:
        return top_assignees[0].get('account_id')

    return None


def get_common_labels(context: ProjectContext,
                      issue_type: Optional[str] = None,
                      limit: int = 10) -> List[str]:
    """
    Get the most commonly used labels.

    Args:
        context: ProjectContext object
        issue_type: If specified, get labels for this type
        limit: Maximum number of labels to return

    Returns:
        List of label strings, sorted by frequency
    """
    patterns = context.patterns

    if issue_type:
        by_type = patterns.get('by_issue_type', {})
        type_patterns = by_type.get(issue_type, {})
        labels = type_patterns.get('labels', {})
    else:
        # Get common labels from overall patterns
        labels = {}
        for type_patterns in patterns.get('by_issue_type', {}).values():
            for label, count in type_patterns.get('labels', {}).items():
                labels[label] = labels.get(label, 0) + count

    # Sort by count and return top N
    sorted_labels = sorted(labels.items(), key=lambda x: x[1], reverse=True)
    return [label for label, _ in sorted_labels[:limit]]


def validate_transition(context: ProjectContext,
                        issue_type: str,
                        from_status: str,
                        to_status: str) -> bool:
    """
    Check if a transition from one status to another is valid.

    Args:
        context: ProjectContext object
        issue_type: Issue type name
        from_status: Current status name
        to_status: Target status name

    Returns:
        True if transition is valid, False otherwise
    """
    valid_transitions = get_valid_transitions(context, issue_type, from_status)

    for transition in valid_transitions:
        if transition.get('to_status') == to_status:
            return True

    return False


def format_context_summary(context: ProjectContext) -> str:
    """
    Format a human-readable summary of the project context.

    Args:
        context: ProjectContext object

    Returns:
        Formatted string summary
    """
    lines = []
    lines.append(f"Project: {context.project_key}")
    lines.append(f"Source: {context.source}")

    if context.discovered_at:
        lines.append(f"Discovered: {context.discovered_at}")

    # Issue types
    issue_types = context.get_issue_types()
    if issue_types:
        type_names = [t.get('name', 'Unknown') for t in issue_types]
        lines.append(f"Issue Types: {', '.join(type_names)}")

    # Components
    components = context.get_components()
    if components:
        comp_names = [c.get('name', 'Unknown') for c in components]
        lines.append(f"Components: {', '.join(comp_names)}")

    # Versions
    versions = context.get_versions()
    if versions:
        version_names = [v.get('name', 'Unknown') for v in versions if not v.get('archived')]
        lines.append(f"Active Versions: {', '.join(version_names[:5])}")

    # Top assignees
    top_assignees = context.patterns.get('top_assignees', [])
    if top_assignees:
        names = [a.get('display_name', 'Unknown') for a in top_assignees[:5]]
        lines.append(f"Top Assignees: {', '.join(names)}")

    # Common labels
    common_labels = get_common_labels(context, limit=5)
    if common_labels:
        lines.append(f"Common Labels: {', '.join(common_labels)}")

    # Defaults summary
    if context.defaults:
        defaults_types = list(context.defaults.get('by_issue_type', {}).keys())
        if defaults_types:
            lines.append(f"Defaults configured for: {', '.join(defaults_types)}")

    return '\n'.join(lines)


# Convenience function for external access
def has_project_context(project_key: str, profile: Optional[str] = None) -> bool:
    """
    Check if project context exists without fully loading it.

    Args:
        project_key: JIRA project key
        profile: JIRA profile to check

    Returns:
        True if skill directory or settings config exists
    """
    # Check skill directory
    skill_path = get_project_skill_path(project_key)
    if skill_path.exists():
        return True

    # Check settings.local.json
    settings_ctx = load_settings_context(project_key, profile)
    return settings_ctx is not None
