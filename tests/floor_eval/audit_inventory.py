#!/usr/bin/env python3
"""Check inventory coverage and citations against explicit local plugin checkouts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def audit(
    inventory: dict, roots: dict[str, Path], jira_snapshot: Path | None = None
) -> dict:
    """Report path/line/snapshot integrity, without asserting factual truth."""
    facts = inventory.get("facts", [])
    errors = []
    expected = list(range(1, 154))
    if inventory.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if sorted(f.get("inventory_item", 0) for f in facts) != expected:
        errors.append("inventory must cover items 1 through 153 exactly once")
    if sorted(f.get("id", "") for f in facts) != [f"G{n:03}" for n in expected]:
        errors.append("IDs must be unique G001 through G153")
    citations = []
    for fact in facts:
        for citation in fact.get("citations", []):
            row = {
                "id": fact["id"],
                "repo": citation["repo"],
                "file": citation["file"],
                "lines": citation["lines"],
                "recorded_audit_status": citation.get("audit_status"),
            }
            repo_root = roots[citation["repo"]].resolve()
            if (
                jira_snapshot is not None
                and citation.get("audit_status") == "uncommitted_main_snapshot"
            ):
                repo_root = jira_snapshot.resolve()
            path = (repo_root / citation["file"]).resolve()
            if not path.is_relative_to(repo_root):
                row["status"] = "outside_repo"
            elif not path.is_file():
                row["status"] = "missing_file"
            else:
                raw = path.read_bytes()
                lines = raw.decode("utf-8").splitlines()
                spans = citation["lines"]
                in_range = bool(spans) and all(
                    len(span) == 2
                    and all(type(value) is int for value in span)
                    and 1 <= span[0] <= span[1] <= len(lines)
                    for span in spans
                )
                row["status"] = "resolves" if in_range else "out_of_range"
                row["line_count"] = len(lines)
                row["source_unchanged"] = hashlib.sha256(
                    raw
                ).hexdigest() == citation.get("source_sha256")
                excerpt = "\n".join(
                    "\n".join(lines[start - 1 : end])
                    for start, end in citation.get("excerpt_lines", [])
                )
                row["excerpt_matches"] = excerpt == citation.get("excerpt", "")
            citations.append(row)
    counts = {
        name: sum(c["status"] == name for c in citations)
        for name in ("resolves", "missing_file", "out_of_range", "outside_repo")
    }
    changed = sum(c.get("source_unchanged") is False for c in citations)
    excerpt_mismatches = sum(c.get("excerpt_matches") is False for c in citations)
    return {
        "facts": len(facts),
        "unique_ids": len({f.get("id") for f in facts}),
        "citations": len(citations),
        "counts": counts,
        "changed_source_citations": changed,
        "excerpt_mismatches": excerpt_mismatches,
        "structural_errors": errors,
        "review_fact_ids": [
            f["id"] for f in facts if f.get("citation_review_required")
        ],
        "ok": not errors
        and not changed
        and not excerpt_mismatches
        and all(c["status"] == "resolves" for c in citations),
        "details": citations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory", type=Path, default=Path(__file__).with_name("inventory.json")
    )
    parser.add_argument("--jira-root", type=Path, required=True)
    parser.add_argument("--confluence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="optional JSON audit report")
    parser.add_argument(
        "--jira-snapshot",
        type=Path,
        help="explicit read-only snapshot root for uncommitted-main citations",
    )
    args = parser.parse_args()
    try:
        result = audit(
            json.loads(args.inventory.read_text(encoding="utf-8")),
            {"jira": args.jira_root, "confluence": args.confluence_root},
            args.jira_snapshot,
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"inventory-audit: {error}\n")
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"facts={result['facts']} unique_ids={result['unique_ids']} "
        f"citations={result['citations']} "
        + " ".join(f"{key}={value}" for key, value in result["counts"].items())
        + f" changed_sources={result['changed_source_citations']} "
        f"excerpt_mismatches={result['excerpt_mismatches']} "
        f"structural_errors={len(result['structural_errors'])}"
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
