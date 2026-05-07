#!/usr/bin/env python3
"""
Suggest DOI fixes for rewritten notes without modifying files.

Workflow:
1) Read citation_audit_report.json
2) Focus on invalid/error DOI entries
3) Retry DOI resolution with GET + URL normalization
4) Emit per-file suggestions:
   - keep (if retry works)
   - normalize (candidate DOI string)
   - remove_or_replace (still failing)
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import requests


def normalize_doi(doi: str) -> str:
    """Apply light normalization to likely malformed DOI strings."""
    value = doi.strip()
    value = value.replace(" ", "")
    value = value.rstrip(".,;:")
    return value


def resolve_doi(doi: str, timeout: int) -> Tuple[bool, int, str]:
    """Try to resolve DOI URL and return (ok, status_code, final_url)."""
    url = f"https://doi.org/{doi}"
    try:
        resp = requests.get(url, allow_redirects=True, timeout=timeout)
        status = resp.status_code
        ok = 200 <= status < 400
        return ok, status, resp.url
    except Exception:  # pylint: disable=broad-except
        return False, 0, ""


def load_invalid_dois(report_path: Path) -> Dict[str, List[str]]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    invalid = defaultdict(list)
    for row in report.get("checks", []):
        if row.get("type") != "doi":
            continue
        if row.get("result") not in ("invalid", "error"):
            continue
        invalid[row["note"]].append(row["identifier"])
    return invalid


def suggest_fix(doi: str, timeout: int) -> Dict[str, str]:
    original = doi
    normalized = normalize_doi(original)

    ok_original, status_original, final_original = resolve_doi(original, timeout)
    if ok_original:
        return {
            "action": "keep",
            "original": original,
            "candidate": original,
            "status": str(status_original),
            "final_url": final_original,
        }

    if normalized != original:
        ok_norm, status_norm, final_norm = resolve_doi(normalized, timeout)
        if ok_norm:
            return {
                "action": "normalize",
                "original": original,
                "candidate": normalized,
                "status": str(status_norm),
                "final_url": final_norm,
            }

    return {
        "action": "remove_or_replace",
        "original": original,
        "candidate": normalized,
        "status": str(status_original),
        "final_url": "",
    }


def main():
    default_notes_dir = (
        Path(__file__).resolve().parents[2] / "processed_archive" / "processed_notes"
    )
    parser = argparse.ArgumentParser(description="Suggest DOI fixes from citation audit report.")
    parser.add_argument(
        "--report",
        default=str(default_notes_dir / "citation_audit_report.json"),
        help="Path to citation_audit_report.json",
    )
    parser.add_argument(
        "--output",
        default=str(default_notes_dir / "citation_doi_fix_suggestions.json"),
        help="Path for suggested-fixes JSON output",
    )
    parser.add_argument("--timeout", type=int, default=12, help="HTTP timeout in seconds")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        raise SystemExit(
            f"Audit report not found: {report_path}. Run citation_validation_audit.py first."
        )

    invalid_by_note = load_invalid_dois(report_path)

    suggestions = {}
    for note in sorted(invalid_by_note):
        note_suggestions = []
        for doi in sorted(set(invalid_by_note[note])):
            note_suggestions.append(suggest_fix(doi, args.timeout))
        suggestions[note] = note_suggestions

    output_path = Path(args.output)
    output_path.write_text(json.dumps(suggestions, indent=2), encoding="utf-8")

    total = sum(len(v) for v in suggestions.values())
    needs_replace = sum(
        1 for rows in suggestions.values() for row in rows if row.get("action") == "remove_or_replace"
    )
    normalized = sum(1 for rows in suggestions.values() for row in rows if row.get("action") == "normalize")
    kept = sum(1 for rows in suggestions.values() for row in rows if row.get("action") == "keep")

    print(f"Notes with DOI issues: {len(suggestions)}")
    print(f"Problematic DOI entries: {total}")
    print(f"keep={kept} normalize={normalized} remove_or_replace={needs_replace}")
    print(f"Suggestions file: {output_path}")

    for note, rows in suggestions.items():
        print(f"\n{note}")
        for row in rows:
            print(
                f"  - {row['action']}: {row['original']}"
                + (f" -> {row['candidate']}" if row['candidate'] != row['original'] else "")
            )


if __name__ == "__main__":
    main()
