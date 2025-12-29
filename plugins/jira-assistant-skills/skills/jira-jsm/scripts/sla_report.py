#!/usr/bin/env python3
"""
Generate JSM SLA compliance report.

Usage:
    python sla_report.py --project SD
    python sla_report.py --service-desk 1
    python sla_report.py --jql "project = SD AND created >= -7d"
    python sla_report.py --project SD --output csv > sla_report.csv
"""

import sys
import os
import argparse
import json
import csv
from io import StringIO
from pathlib import Path
from typing import Optional, Dict, Any, List


from jira_assistant_skills_lib import get_jira_client
from jira_assistant_skills_lib import print_error, JiraError, NotFoundError


def generate_sla_report(project: Optional[str] = None,
                        service_desk_id: Optional[int] = None,
                        jql: Optional[str] = None,
                        sla_name: Optional[str] = None,
                        breached_only: bool = False,
                        profile: Optional[str] = None) -> Dict[str, Any]:
    """Generate SLA compliance report."""
    with get_jira_client(profile) as client:
        # Build JQL query
        if jql:
            query = jql
        elif project:
            query = f"project = {project}"
        elif service_desk_id:
            # Get service desk to find project key
            sd = client.get_service_desk(str(service_desk_id))
            project_key = sd.get('projectKey')
            query = f"project = {project_key}"
        else:
            raise ValueError("Must specify --project, --service-desk, or --jql")

        # Search for issues
        results = client.search_issues(query, max_results=1000)
        issues = results.get('issues', [])

        # Collect SLA data for each issue
        report_data = []
        for issue in issues:
            issue_key = issue.get('key')
            try:
                sla_data = client.get_request_slas(issue_key)
                slas = sla_data.get('values', [])

                # Filter by SLA name if specified
                if sla_name:
                    slas = [s for s in slas if s.get('name') == sla_name]

                # Filter breached only if specified
                if breached_only:
                    slas = [s for s in slas if _is_breached(s)]

                if slas:
                    for sla in slas:
                        report_data.append({
                            'issue_key': issue_key,
                            'summary': issue.get('fields', {}).get('summary'),
                            'sla': sla
                        })
            except Exception:
                # Skip issues without SLA data
                pass

    return {
        'total_issues': len(issues),
        'total_slas': len(report_data),
        'report_data': report_data
    }


def _is_breached(sla: Dict[str, Any]) -> bool:
    """Check if SLA is breached."""
    ongoing = sla.get('ongoingCycle')
    if ongoing and ongoing.get('breached'):
        return True
    completed = sla.get('completedCycles', [])
    if completed and completed[-1].get('breached'):
        return True
    return False


def format_report_text(report: Dict[str, Any]) -> str:
    """Format report as text."""
    lines = []
    lines.append("\nSLA Compliance Report")
    lines.append("=" * 80)
    lines.append(f"Total Issues: {report['total_issues']}")
    lines.append(f"Total SLA Metrics: {report['total_slas']}")
    lines.append("")

    for entry in report['report_data'][:10]:  # Show top 10
        issue_key = entry['issue_key']
        summary = entry['summary']
        sla = entry['sla']
        sla_name = sla.get('name')
        is_breached = _is_breached(sla)

        lines.append(f"{issue_key}: {summary[:60]}")
        lines.append(f"  SLA: {sla_name} - {'BREACHED' if is_breached else 'OK'}")

    return '\n'.join(lines)


def format_report_csv(report: Dict[str, Any]) -> str:
    """Format report as CSV."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Request Key', 'Summary', 'SLA Name', 'Breached'])

    for entry in report['report_data']:
        writer.writerow([
            entry['issue_key'],
            entry['summary'],
            entry['sla'].get('name'),
            'Yes' if _is_breached(entry['sla']) else 'No'
        ])

    return output.getvalue()


def format_report_json(report: Dict[str, Any]) -> str:
    """Format report as JSON."""
    return json.dumps(report, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate JSM SLA compliance report')
    parser.add_argument('--project', help='Project key')
    parser.add_argument('--service-desk', type=int, help='Service desk ID')
    parser.add_argument('--jql', help='Custom JQL query')
    parser.add_argument('--sla-name', help='Filter to specific SLA')
    parser.add_argument('--breached-only', action='store_true', help='Only breached SLAs')
    parser.add_argument('--output', choices=['text', 'csv', 'json'], default='text')
    parser.add_argument('--profile', help='JIRA profile to use')

    args = parser.parse_args()

    try:
        report = generate_sla_report(
            project=args.project,
            service_desk_id=args.service_desk,
            jql=args.jql,
            sla_name=args.sla_name,
            breached_only=args.breached_only,
            profile=args.profile
        )

        if args.output == 'json':
            print(format_report_json(report))
        elif args.output == 'csv':
            print(format_report_csv(report))
        else:
            print(format_report_text(report))

        return 0

    except Exception as e:
        print_error(f"Failed to generate report: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
