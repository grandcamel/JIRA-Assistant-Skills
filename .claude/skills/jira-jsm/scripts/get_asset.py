#!/usr/bin/env python3
"""
Get asset/CMDB object details by ID.

Retrieves full asset details including all attributes.
Requires JSM Premium license or Assets license.

Usage:
    get_asset.py --id 10001
    get_asset.py --id 10001 --output json
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


def get_asset(asset_id: int):
    """
    Get asset details by ID.

    Args:
        asset_id: Asset object ID

    Returns:
        Asset object with all attributes
    """
    with get_jira_client() as client:
        # Check license first
        if not client.has_assets_license():
            print("ERROR: Assets/Insight not available. Requires JSM Premium license.", file=sys.stderr)
            sys.exit(1)

        return client.get_asset(asset_id)


def format_text(asset: dict) -> str:
    """Format asset as human-readable text."""
    output = [f"Asset: {asset.get('objectKey', 'N/A')} ({asset.get('label', 'N/A')})\n"]

    if 'objectType' in asset:
        output.append(f"Object Type: {asset['objectType'].get('name', 'N/A')}")

    if 'attributes' in asset:
        output.append("\nAttributes:")
        for attr in asset['attributes']:
            attr_name = attr.get('objectTypeAttribute', {}).get('name', 'Unknown')
            values = attr.get('objectAttributeValues', [])
            if values:
                attr_value = values[0].get('value', 'N/A')
                output.append(f"  {attr_name}: {attr_value}")

    if '_links' in asset and 'self' in asset['_links']:
        output.append(f"\nURL: {asset['_links']['self']}")

    return "\n".join(output)


def format_json(asset: dict) -> str:
    """Format asset as JSON."""
    return json.dumps(asset, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Get asset/CMDB object details",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--id', type=int, required=True,
                       help='Asset object ID')
    parser.add_argument('--output', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        asset = get_asset(args.id)

        if args.output == 'json':
            print(format_json(asset))
        else:
            print(format_text(asset))

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error getting asset: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
