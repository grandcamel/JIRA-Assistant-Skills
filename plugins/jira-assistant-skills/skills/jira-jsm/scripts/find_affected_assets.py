#!/usr/bin/env python3
"""
Find assets affected by an incident or change.

Searches for assets based on criteria like location, type, or IQL query.
Useful for impact analysis.
Requires JSM Premium license or Assets license.

Usage:
    find_affected_assets.py --iql 'Location="DC-1"'
    find_affected_assets.py --iql 'objectType="Server" AND Status="Active"'
    find_affected_assets.py --type Server --iql 'Location="DC-1"'
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


def find_affected_assets(iql: str, object_type: str | None = None):
    """
    Find assets matching criteria.

    Args:
        iql: IQL query string
        object_type: Optional object type filter

    Returns:
        List of matching assets
    """
    with get_jira_client() as client:
        # Check license first
        if not client.has_assets_license():
            print(
                "ERROR: Assets/Insight not available. Requires JSM Premium license.",
                file=sys.stderr,
            )
            sys.exit(1)

        return client.find_assets_by_criteria(iql)


def format_text(assets: list, criteria: str) -> str:
    """Format affected assets as human-readable text."""
    if not assets:
        return f"No assets found matching criteria: {criteria}"

    output = [f"Affected Assets ({len(assets)} found):\n"]
    output.append(f"Search Criteria: {criteria}\n")

    for asset in assets:
        output.append(f"Key: {asset.get('objectKey', 'N/A')}")
        output.append(f"Label: {asset.get('label', 'N/A')}")

        if "objectType" in asset:
            output.append(f"Type: {asset['objectType'].get('name', 'N/A')}")

        if "attributes" in asset:
            for attr in asset["attributes"][:2]:  # Show first 2 attributes
                attr_name = attr.get("objectTypeAttribute", {}).get("name", "Unknown")
                values = attr.get("objectAttributeValues", [])
                if values:
                    attr_value = values[0].get("value", "N/A")
                    output.append(f"  {attr_name}: {attr_value}")

        output.append("")

    return "\n".join(output)


def format_json(assets: list) -> str:
    """Format affected assets as JSON."""
    return json.dumps(assets, indent=2)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Find assets affected by incident or change",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--iql", required=True, help="IQL query string for asset criteria"
    )
    parser.add_argument("--type", help="Optional object type filter")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        assets = find_affected_assets(args.iql, args.type)

        if args.output == "json":
            print(format_json(assets))
        else:
            print(format_text(assets, args.iql))

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error finding affected assets: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
