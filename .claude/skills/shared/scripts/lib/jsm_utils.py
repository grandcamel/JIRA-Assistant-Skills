"""
JSM utility functions for SLA formatting and processing.

Provides helper functions for:
- Time formatting (millis to human-readable)
- SLA status calculation
- Breach detection
- Status icons and text
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def format_sla_time(time_dict: Dict[str, Any]) -> str:
    """
    Format SLA time from API response.

    Args:
        time_dict: Time object with iso8601, jira, friendly, epochMillis

    Returns:
        Human-readable time string

    Examples:
        >>> format_sla_time({"friendly": "15/Jan/25 10:00 AM"})
        '15/Jan/25 10:00 AM'
    """
    if not time_dict:
        return "N/A"
    return time_dict.get('friendly', time_dict.get('iso8601', 'Unknown'))


def format_duration(duration_dict: Dict[str, Any]) -> str:
    """
    Format SLA duration from API response.

    Args:
        duration_dict: Duration with millis and friendly fields

    Returns:
        Human-readable duration string

    Examples:
        >>> format_duration({"friendly": "2h 30m"})
        '2h 30m'
    """
    if not duration_dict:
        return "N/A"
    return duration_dict.get('friendly', f"{duration_dict.get('millis', 0) // 1000}s")


def calculate_sla_percentage(elapsed_millis: int, goal_millis: int) -> float:
    """
    Calculate SLA completion percentage.

    Args:
        elapsed_millis: Elapsed time in milliseconds
        goal_millis: Goal duration in milliseconds

    Returns:
        Percentage (0-100+)

    Examples:
        >>> calculate_sla_percentage(7200000, 14400000)  # 2h of 4h
        50.0
    """
    if goal_millis == 0:
        return 0.0
    return (elapsed_millis / goal_millis) * 100


def is_sla_at_risk(remaining_millis: int, goal_millis: int,
                   threshold: float = 20.0) -> bool:
    """
    Check if SLA is at risk of breach.

    Args:
        remaining_millis: Remaining time in milliseconds
        goal_millis: Goal duration in milliseconds
        threshold: Warning threshold percentage (default 20%)

    Returns:
        True if remaining time is less than threshold% of goal

    Examples:
        >>> is_sla_at_risk(3600000, 14400000)  # 1h remaining of 4h goal
        True  # 25% remaining > 20% threshold = False
        >>> is_sla_at_risk(1800000, 14400000)  # 30m remaining of 4h goal
        True  # 12.5% remaining < 20% threshold = True
    """
    if goal_millis == 0:
        return False
    remaining_percentage = (remaining_millis / goal_millis) * 100
    return remaining_percentage < threshold


def get_sla_status_emoji(sla: Dict[str, Any]) -> str:
    """
    Get emoji for SLA status.

    Args:
        sla: SLA metric object

    Returns:
        Status emoji

    Examples:
        >>> get_sla_status_emoji({"ongoingCycle": {"breached": False}})
        '▶'
        >>> get_sla_status_emoji({"ongoingCycle": {"breached": True}})
        '✗'
    """
    ongoing = sla.get('ongoingCycle')
    completed = sla.get('completedCycles', [])

    if ongoing:
        if ongoing.get('breached'):
            return '✗'
        if ongoing.get('paused'):
            return '⏸'
        # Check if at risk
        remaining = ongoing.get('remainingTime', {}).get('millis', 0)
        goal = ongoing.get('goalDuration', {}).get('millis', 0)
        if is_sla_at_risk(remaining, goal):
            return '⚠'
        return '▶'  # Active

    if completed:
        last_cycle = completed[-1]
        if last_cycle.get('breached'):
            return '✗'
        return '✓'

    return '?'


def get_sla_status_text(sla: Dict[str, Any]) -> str:
    """
    Get human-readable SLA status.

    Args:
        sla: SLA metric object

    Returns:
        Status text
    """
    ongoing = sla.get('ongoingCycle')
    completed = sla.get('completedCycles', [])

    if ongoing:
        if ongoing.get('breached'):
            return 'BREACHED'
        if ongoing.get('paused'):
            return 'Paused'
        remaining = ongoing.get('remainingTime', {}).get('millis', 0)
        goal = ongoing.get('goalDuration', {}).get('millis', 0)
        if is_sla_at_risk(remaining, goal):
            return 'At Risk'
        return 'Active'

    if completed:
        last_cycle = completed[-1]
        if last_cycle.get('breached'):
            return 'Failed'
        return 'Met'

    return 'Unknown'
