#!/usr/bin/env python3
"""
Get Knowledge Base article details by ID.

Retrieves full KB article content including title, body, and metadata.
Useful for viewing documentation details.

Usage:
    get_kb_article.py --article-id 131073
    get_kb_article.py --article-id 131073 --output json
"""

import argparse
import sys
import json
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(Path(__file__).parent.parent.parent.parent / 'shared' / 'scripts' / 'lib')
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import get_jira_client


def get_kb_article(article_id: str):
    """
    Get KB article details by ID.

    Args:
        article_id: KB article ID

    Returns:
        KB article details
    """
    with get_jira_client() as client:
        return client.get_kb_article(article_id)


def format_text(article: dict) -> str:
    """Format KB article as human-readable text."""
    output = [f"Knowledge Base Article: {article['title']}\n"]

    if 'excerpt' in article:
        excerpt = article['excerpt'].replace('<em>', '').replace('</em>', '')
        output.append(f"Excerpt:\n{excerpt}\n")

    if '_links' in article and 'self' in article['_links']:
        output.append(f"URL: {article['_links']['self']}")

    if 'source' in article:
        output.append(f"Source: {article['source'].get('type', 'unknown')}")

    return "\n".join(output)


def format_json(article: dict) -> str:
    """Format KB article as JSON."""
    return json.dumps(article, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Get Knowledge Base article details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--article-id', required=True,
                       help='KB article ID')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        article = get_kb_article(args.article_id)

        if args.output == 'json':
            print(format_json(article))
        else:
            print(format_text(article))

    except Exception as e:
        print(f"Error getting KB article: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
