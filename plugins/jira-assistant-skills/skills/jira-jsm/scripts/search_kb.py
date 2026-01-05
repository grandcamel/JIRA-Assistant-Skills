#!/usr/bin/env python3
"""
Search Knowledge Base articles for a service desk.

Searches KB articles using query terms and displays results with excerpts.
Useful for finding documentation and self-service solutions.

Usage:
    search_kb.py --service-desk 1 --query "password reset"
    search_kb.py --service-desk 1 --query "vpn" --max-results 10
    search_kb.py --service-desk 1 --query "login" --output json
"""

import argparse
import json
import sys
from pathlib import Path

# Add shared lib to path
shared_lib_path = str(
    Path(__file__).parent.parent.parent.parent / "shared" / "scripts" / "lib"
)
if shared_lib_path not in sys.path:
    sys.path.insert(0, shared_lib_path)

from jira_assistant_skills_lib import get_jira_client


def search_kb(service_desk_id: int, query: str, max_results: int = 50):
    """
    Search KB articles for a service desk.

    Args:
        service_desk_id: Service desk ID
        query: Search query string
        max_results: Maximum results to return

    Returns:
        List of matching KB articles
    """
    with get_jira_client() as client:
        return client.search_kb_articles(service_desk_id, query, max_results)


def format_text(articles: list) -> str:
    """Format KB search results as human-readable text."""
    if not articles:
        return "No KB articles found matching your query."

    output = [f"Knowledge Base Search Results ({len(articles)} articles):\n"]

    for article in articles:
        output.append(f"Title: {article['title']}")
        if "excerpt" in article:
            # Remove HTML tags from excerpt
            excerpt = article["excerpt"].replace("<em>", "").replace("</em>", "")
            output.append(f"Excerpt: {excerpt}")
        if "_links" in article and "self" in article["_links"]:
            output.append(f"URL: {article['_links']['self']}")
        output.append("")

    return "\n".join(output)


def format_json(articles: list) -> str:
    """Format KB search results as JSON."""
    return json.dumps(articles, indent=2)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Search Knowledge Base articles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--service-desk", type=int, required=True, help="Service desk ID"
    )
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum results to return (default: 50)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--profile", help="JIRA profile to use")

    args = parser.parse_args(argv)

    try:
        articles = search_kb(args.service_desk, args.query, args.max_results)

        if args.output == "json":
            print(format_json(articles))
        else:
            print(format_text(articles))

    except Exception as e:
        print(f"Error searching KB: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
