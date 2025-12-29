#!/usr/bin/env python3
"""
Suggest relevant KB articles for a service request.

Analyzes request summary/description and suggests relevant KB articles.
Useful for automated deflection and self-service suggestions.

Usage:
    suggest_kb.py --request REQ-123
    suggest_kb.py --request REQ-123 --max-suggestions 3
    suggest_kb.py --request REQ-123 --output json
"""

import argparse
import sys
import json
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from config_manager import get_jira_client


def suggest_kb(issue_key: str, max_suggestions: int = 5):
    """
    Suggest KB articles for a request.

    Args:
        issue_key: Request issue key
        max_suggestions: Maximum suggestions to return

    Returns:
        List of suggested KB articles
    """
    with get_jira_client() as client:
        return client.suggest_kb_for_request(issue_key, max_suggestions)


def format_text(suggestions: list, issue_key: str) -> str:
    """Format KB suggestions as human-readable text."""
    if not suggestions:
        return f"No KB article suggestions found for {issue_key}."

    output = [f"KB Article Suggestions for {issue_key} ({len(suggestions)} suggestions):\n"]

    for i, article in enumerate(suggestions, 1):
        output.append(f"{i}. {article['title']}")
        if 'excerpt' in article:
            excerpt = article['excerpt'].replace('<em>', '').replace('</em>', '')
            output.append(f"   Excerpt: {excerpt}")
        if '_links' in article and 'self' in article['_links']:
            output.append(f"   URL: {article['_links']['self']}")
        output.append("")

    return "\n".join(output)


def format_json(suggestions: list) -> str:
    """Format KB suggestions as JSON."""
    return json.dumps(suggestions, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Suggest KB articles for a request",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--request', required=True,
                       help='Request issue key (e.g., REQ-123)')
    parser.add_argument('--max-suggestions', type=int, default=5,
                       help='Maximum suggestions to return (default: 5)')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        suggestions = suggest_kb(args.request, args.max_suggestions)

        if args.output == 'json':
            print(format_json(suggestions))
        else:
            print(format_text(suggestions, args.request))

    except Exception as e:
        print(f"Error suggesting KB articles: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
