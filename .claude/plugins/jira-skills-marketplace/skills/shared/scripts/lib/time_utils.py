"""
Time parsing and formatting utilities for JIRA time tracking.

Provides functions to parse JIRA time format strings (e.g., '2h', '1d 4h 30m')
and convert between seconds and human-readable formats.
"""

import re
from datetime import datetime, timedelta
from typing import Optional

# JIRA default time units (configurable in JIRA, these are common defaults)
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
HOURS_PER_DAY = 8  # JIRA default: 8 hours per day
DAYS_PER_WEEK = 5  # JIRA default: 5 days per week

# Derived values
SECONDS_PER_DAY = HOURS_PER_DAY * SECONDS_PER_HOUR
SECONDS_PER_WEEK = DAYS_PER_WEEK * SECONDS_PER_DAY


def parse_time_string(time_str: str) -> int:
    """
    Parse JIRA time format to seconds.

    Args:
        time_str: Time string like '2h', '1d 4h 30m', '3w 2d'

    Returns:
        Time in seconds

    Raises:
        ValueError: If time format is invalid

    Examples:
        >>> parse_time_string('2h')
        7200
        >>> parse_time_string('1d 4h')
        43200
        >>> parse_time_string('30m')
        1800
        >>> parse_time_string('1w')
        144000
    """
    if not time_str or not time_str.strip():
        raise ValueError("Time string cannot be empty")

    patterns = {
        'w': SECONDS_PER_WEEK,
        'd': SECONDS_PER_DAY,
        'h': SECONDS_PER_HOUR,
        'm': SECONDS_PER_MINUTE
    }

    total_seconds = 0
    time_str_lower = time_str.lower().strip()

    for match in re.finditer(r'(\d+(?:\.\d+)?)\s*([wdhm])', time_str_lower):
        value_str, unit = match.groups()
        value = float(value_str)
        if unit in patterns:
            total_seconds += int(value * patterns[unit])

    if total_seconds == 0:
        raise ValueError(f"Invalid time format: '{time_str}'. "
                        f"Use format like '2h', '1d 4h', '30m'")

    return total_seconds


def format_seconds(seconds: int, compact: bool = False) -> str:
    """
    Format seconds to human-readable JIRA time format.

    Args:
        seconds: Time in seconds
        compact: If True, use minimal spacing

    Returns:
        Human-readable string like '1d 4h 30m'

    Examples:
        >>> format_seconds(7200)
        '2h'
        >>> format_seconds(43200)
        '1d 4h'
        >>> format_seconds(0)
        '0m'
    """
    if seconds == 0:
        return '0m'

    if seconds < 0:
        return '-' + format_seconds(abs(seconds), compact)

    parts = []
    remaining = seconds

    weeks = remaining // SECONDS_PER_WEEK
    remaining %= SECONDS_PER_WEEK

    days = remaining // SECONDS_PER_DAY
    remaining %= SECONDS_PER_DAY

    hours = remaining // SECONDS_PER_HOUR
    remaining %= SECONDS_PER_HOUR

    minutes = remaining // SECONDS_PER_MINUTE

    if weeks:
        parts.append(f'{weeks}w')
    if days:
        parts.append(f'{days}d')
    if hours:
        parts.append(f'{hours}h')
    if minutes:
        parts.append(f'{minutes}m')

    separator = '' if compact else ' '
    return separator.join(parts) if parts else '0m'


def format_seconds_long(seconds: int) -> str:
    """
    Format seconds to verbose human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Verbose string like '1 day 4 hours 30 minutes'

    Examples:
        >>> format_seconds_long(7200)
        '2 hours'
        >>> format_seconds_long(43200)
        '1 day 4 hours'
    """
    if seconds == 0:
        return '0 minutes'

    if seconds < 0:
        return '-' + format_seconds_long(abs(seconds))

    parts = []
    remaining = seconds

    weeks = remaining // SECONDS_PER_WEEK
    remaining %= SECONDS_PER_WEEK

    days = remaining // SECONDS_PER_DAY
    remaining %= SECONDS_PER_DAY

    hours = remaining // SECONDS_PER_HOUR
    remaining %= SECONDS_PER_HOUR

    minutes = remaining // SECONDS_PER_MINUTE

    if weeks:
        parts.append(f'{weeks} {"week" if weeks == 1 else "weeks"}')
    if days:
        parts.append(f'{days} {"day" if days == 1 else "days"}')
    if hours:
        parts.append(f'{hours} {"hour" if hours == 1 else "hours"}')
    if minutes:
        parts.append(f'{minutes} {"minute" if minutes == 1 else "minutes"}')

    return ' '.join(parts) if parts else '0 minutes'


def parse_relative_date(date_str: str, base_date: Optional[datetime] = None) -> datetime:
    """
    Parse relative or absolute date strings.

    Args:
        date_str: Date string like 'yesterday', 'last-week', '2025-01-15',
                 '2025-01-15 09:00', or ISO format
        base_date: Base date for relative calculations (default: now)

    Returns:
        datetime object

    Raises:
        ValueError: If date format is unrecognized

    Examples:
        >>> parse_relative_date('yesterday')  # doctest: +SKIP
        datetime.datetime(2025, 1, 14, 0, 0)
        >>> parse_relative_date('2025-01-15')
        datetime.datetime(2025, 1, 15, 0, 0)
    """
    if base_date is None:
        base_date = datetime.now()

    today = base_date.replace(hour=0, minute=0, second=0, microsecond=0)

    relative_dates = {
        'today': today,
        'yesterday': today - timedelta(days=1),
        'tomorrow': today + timedelta(days=1),
        'last-week': today - timedelta(weeks=1),
        'this-week': today - timedelta(days=today.weekday()),
        'last-month': (today.replace(day=1) - timedelta(days=1)).replace(day=1),
        'this-month': today.replace(day=1),
    }

    date_str_lower = date_str.lower().strip()

    if date_str_lower in relative_dates:
        return relative_dates[date_str_lower]

    # Try various date formats
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y',
        '%m/%d/%Y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unrecognized date format: '{date_str}'. "
                    f"Use 'yesterday', '2025-01-15', or ISO format.")


def format_datetime_for_jira(dt: datetime) -> str:
    """
    Format datetime to JIRA API format.

    Args:
        dt: datetime object

    Returns:
        ISO format string like '2025-01-15T09:00:00.000+0000'

    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2025, 1, 15, 9, 0, 0)
        >>> format_datetime_for_jira(dt)
        '2025-01-15T09:00:00.000+0000'
    """
    # JIRA expects milliseconds and timezone
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000+0000')
    else:
        return dt.strftime('%Y-%m-%dT%H:%M:%S.000%z')


def validate_time_format(time_str: str) -> bool:
    """
    Validate that a string is a valid JIRA time format.

    Args:
        time_str: Time string to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_time_format('2h')
        True
        >>> validate_time_format('invalid')
        False
        >>> validate_time_format('')
        False
    """
    try:
        parse_time_string(time_str)
        return True
    except ValueError:
        return False


def calculate_progress(time_spent_seconds: int, original_estimate_seconds: int) -> float:
    """
    Calculate progress percentage.

    Args:
        time_spent_seconds: Time spent in seconds
        original_estimate_seconds: Original estimate in seconds

    Returns:
        Progress as percentage (0-100+)

    Examples:
        >>> calculate_progress(3600, 7200)
        50.0
        >>> calculate_progress(0, 7200)
        0.0
        >>> calculate_progress(7200, 0)
        0.0
    """
    if original_estimate_seconds <= 0:
        return 0.0
    return (time_spent_seconds / original_estimate_seconds) * 100


def format_progress_bar(progress: float, width: int = 20) -> str:
    """
    Create a visual progress bar.

    Args:
        progress: Progress percentage (0-100)
        width: Width of the bar in characters

    Returns:
        Progress bar string like '████████░░░░░░░░░░░░'

    Examples:
        >>> format_progress_bar(50, 10)
        '█████░░░░░'
        >>> format_progress_bar(0, 10)
        '░░░░░░░░░░'
    """
    filled = int(min(progress, 100) / 100 * width)
    empty = width - filled
    return '█' * filled + '░' * empty


def parse_date_to_iso(date_str: str, base_date: Optional[datetime] = None) -> str:
    """
    Parse various date formats to ISO 8601 format for JIRA API.

    Combines parsing of relative dates, simple dates, and full ISO dates
    into a single function that returns a consistent ISO format.

    Args:
        date_str: Date string in various formats:
                  - Relative: 'today', 'yesterday', 'last-week', 'this-month'
                  - Simple: 'YYYY-MM-DD' (e.g., '2025-01-20')
                  - Full ISO: '2025-01-20T00:00:00.000Z'
        base_date: Base date for relative calculations (default: now)

    Returns:
        ISO 8601 date string like '2025-01-20T00:00:00.000Z'

    Raises:
        ValueError: If date format is unrecognized

    Examples:
        >>> parse_date_to_iso('2025-01-20')
        '2025-01-20T00:00:00.000Z'
        >>> parse_date_to_iso('2025-01-20T10:30:00.000Z')
        '2025-01-20T10:30:00.000Z'
        >>> parse_date_to_iso('today')  # doctest: +SKIP
        '2025-01-15T00:00:00.000Z'
    """
    if not date_str or not date_str.strip():
        raise ValueError("Date string cannot be empty")

    date_str = date_str.strip()

    # Already in full ISO format with 'T'
    if 'T' in date_str:
        # Normalize timezone format
        if date_str.endswith('Z'):
            return date_str
        if '+' in date_str or date_str[-6:].startswith('-'):
            # Has timezone, convert to Z format
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            except ValueError:
                pass
        return date_str

    # Try simple date format YYYY-MM-DD first
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%Y-%m-%dT00:00:00.000Z')
    except ValueError:
        pass

    # Try relative date parsing
    try:
        dt = parse_relative_date(date_str, base_date)
        return dt.strftime('%Y-%m-%dT00:00:00.000Z')
    except ValueError:
        pass

    raise ValueError(
        f"Invalid date format: '{date_str}'. "
        f"Use YYYY-MM-DD, ISO format, or relative dates like 'today', 'yesterday'."
    )


def convert_to_jira_datetime_string(date_str: str, base_date: Optional[datetime] = None) -> str:
    """
    Convert a date string to JIRA datetime format with timezone offset.

    Similar to parse_date_to_iso but returns format with +0000 timezone
    offset instead of 'Z', which is preferred for some JIRA APIs.

    Args:
        date_str: Date string in various formats:
                  - Relative: 'today', 'yesterday', 'last-week'
                  - Simple: 'YYYY-MM-DD'
                  - Full ISO: '2025-01-20T00:00:00.000Z'
        base_date: Base date for relative calculations (default: now)

    Returns:
        JIRA datetime string like '2025-01-20T00:00:00.000+0000'

    Raises:
        ValueError: If date format is unrecognized

    Examples:
        >>> convert_to_jira_datetime_string('2025-01-20')
        '2025-01-20T00:00:00.000+0000'
        >>> convert_to_jira_datetime_string('yesterday')  # doctest: +SKIP
        '2025-01-14T00:00:00.000+0000'
    """
    if not date_str or not date_str.strip():
        raise ValueError("Date string cannot be empty")

    date_str = date_str.strip()

    # Try to parse using parse_date_to_iso first
    iso_date = parse_date_to_iso(date_str, base_date)

    # Convert 'Z' suffix to '+0000'
    if iso_date.endswith('Z'):
        return iso_date[:-1] + '+0000'

    # Already has timezone offset
    return iso_date
