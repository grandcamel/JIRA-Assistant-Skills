#!/usr/bin/env python3
"""
List and search assets/CMDB objects with IQL filtering.

Lists assets from Insight/Assets with optional IQL query filtering.
Requires JSM Premium license or Assets license.

Usage:
    list_assets.py
    list_assets.py --type Server
    list_assets.py --iql 'Status="Active"'
    list_assets.py --type Server --iql 'Status="Active"'
    list_assets.py --output json
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


def list_assets(
    object_type: str | None = None, iql: str | None = None, max_results: int = 100
):
    """
    List assets with optional filtering.

    Args:
        object_type: Optional object type name
        iql: Optional IQL query string
        max_results: Maximum results to return

    Returns:
        List of asset objects
    """
    with get_jira_client() as client:
        # Check license first
        if not client.has_assets_license():
            print(
                "ERROR: Assets/Insight not available. Requires JSM Premium license.",
                file=sys.stderr,
            )
            sys.exit(1)

        return client.list_assets(object_type, iql, max_results)


def format_text(assets: list) -> str:
    """Format assets as human-readable text."""
    if not assets:
        return "No assets found matching criteria."

    output = [f"Assets ({len(assets)} total):\n"]

    for asset in assets:
        output.append(f"Key: {asset.get('objectKey', 'N/A')}")
        output.append(f"Label: {asset.get('label', 'N/A')}")

        if "objectType" in asset:
            output.append(f"Type: {asset['objectType'].get('name', 'N/A')}")

        if "attributes" in asset:
            for attr in asset["attributes"][:3]:  # Show first 3 attributes
                attr_name = attr.get("objectTypeAttribute", {}).get("name", "Unknown")
                values = attr.get("objectAttributeValues", [])
                if values:
                    attr_value = values[0].get("value", "N/A")
                    output.append(f"  {attr_name}: {attr_value}")

        output.append("")

    return "\n".join(output)


def format_json(assets: list) -> str:
    """Format assets as JSON."""
    return json.dumps(assets, indent=2)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(
        description="List assets/CMDB objects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--type", help="Object type name filter")
    parser.add_argument("--iql", help="IQL query string for filtering")
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum results to return (default: 100)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        assets = list_assets(args.type, args.iql, args.max_results)

        if args.output == "json":
            print(format_json(assets))
        else:
            print(format_text(assets))

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error listing assets: {e!s}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
