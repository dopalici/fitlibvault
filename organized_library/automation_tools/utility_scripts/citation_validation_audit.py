#!/usr/bin/env python3
"""
Audit citation validations and DOI/PMID links across rewritten notes.

Outputs:
- JSON summary report
- CSV row-level link checks
"""

import argparse
import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


DOI_LINK_RE = re.compile(r"https?://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
PMID_LINK_RE = re.compile(r"https?://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", re.IGNORECASE)
VALIDATION_WARNING_RE = re.compile(r"<!--\s*VALIDATION WARNING:\s*(.*?)\s*-->", re.IGNORECASE | re.DOTALL)


@dataclass
class LinkCheck:
    note: str
    link_type: str
    identifier: str
    url: str
    status_code: Optional[int]
    result: str
    error: str


def classify_status(status_code: Optional[int], error: str) -> str:
    if error:
        return "error"
    if status_code is None:
        return "error"
    if 200 <= status_code < 400:
        return "ok"
    if status_code in (401, 403):
        return "blocked"
    return "invalid"


def check_url(url: str, timeout: int) -> Tuple[Optional[int], str]:
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        status = response.status_code
        if status == 405:
            response = requests.get(url, allow_redirects=True, timeout=timeout)
            status = response.status_code
        return status, ""
    except Exception as exc:  # pylint: disable=broad-except
        return None, str(exc)


def parse_note(file_path: Path) -> Dict:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    doi_ids = sorted(set(DOI_LINK_RE.findall(content)))
    pmid_ids = sorted(set(PMID_LINK_RE.findall(content)))

    warning_match = VALIDATION_WARNING_RE.search(content)
    warnings: List[str] = []
    if warning_match:
        warning_text = warning_match.group(1)
        warnings = [w.strip() for w in warning_text.split(";") if w.strip()]

    return {
        "note": file_path.name,
        "path": str(file_path),
        "dois": doi_ids,
        "pmids": pmid_ids,
        "warnings": warnings,
    }


def build_checks(parsed_note: Dict) -> List[LinkCheck]:
    checks: List[LinkCheck] = []
    note_name = parsed_note["note"]

    for doi in parsed_note["dois"]:
        checks.append(
            LinkCheck(
                note=note_name,
                link_type="doi",
                identifier=doi,
                url=f"https://doi.org/{doi}",
                status_code=None,
                result="pending",
                error="",
            )
        )

    for pmid in parsed_note["pmids"]:
        checks.append(
            LinkCheck(
                note=note_name,
                link_type="pmid",
                identifier=pmid,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                status_code=None,
                result="pending",
                error="",
            )
        )

    return checks


def run_audit(input_dir: Path, timeout: int, workers: int, file_glob: str) -> Dict:
    files = sorted(input_dir.glob(file_glob))
    parsed_notes = [parse_note(path) for path in files]

    checks: List[LinkCheck] = []
    for note in parsed_notes:
        checks.extend(build_checks(note))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(check_url, check.url, timeout): check for check in checks}
        for future in as_completed(futures):
            check = futures[future]
            status_code, error = future.result()
            check.status_code = status_code
            check.error = error
            check.result = classify_status(status_code, error)

    per_note_summary: Dict[str, Dict] = {}
    for note in parsed_notes:
        note_name = note["note"]
        note_checks = [c for c in checks if c.note == note_name]
        per_note_summary[note_name] = {
            "doi_count": len(note["dois"]),
            "pmid_count": len(note["pmids"]),
            "warning_count": len(note["warnings"]),
            "warnings": note["warnings"],
            "ok_links": sum(1 for c in note_checks if c.result == "ok"),
            "blocked_links": sum(1 for c in note_checks if c.result == "blocked"),
            "invalid_links": sum(1 for c in note_checks if c.result == "invalid"),
            "error_links": sum(1 for c in note_checks if c.result == "error"),
        }

    return {
        "input_dir": str(input_dir),
        "note_count": len(parsed_notes),
        "total_links": len(checks),
        "ok_links": sum(1 for c in checks if c.result == "ok"),
        "blocked_links": sum(1 for c in checks if c.result == "blocked"),
        "invalid_links": sum(1 for c in checks if c.result == "invalid"),
        "error_links": sum(1 for c in checks if c.result == "error"),
        "notes_with_warnings": sum(1 for n in parsed_notes if n["warnings"]),
        "per_note_summary": per_note_summary,
        "checks": [
            {
                "note": c.note,
                "type": c.link_type,
                "identifier": c.identifier,
                "url": c.url,
                "status_code": c.status_code,
                "result": c.result,
                "error": c.error,
            }
            for c in checks
        ],
    }


def write_outputs(report: Dict, output_dir: Path) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "citation_audit_report.json"
    csv_path = output_dir / "citation_audit_links.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["note", "type", "identifier", "url", "status_code", "result", "error"],
        )
        writer.writeheader()
        for row in report["checks"]:
            writer.writerow(row)

    return json_path, csv_path


def main():
    default_notes_dir = (
        Path(__file__).resolve().parents[2] / "processed_archive" / "processed_notes"
    )
    parser = argparse.ArgumentParser(description="Audit DOI/PMID validation across rewritten notes.")
    parser.add_argument(
        "--input-dir",
        default=str(default_notes_dir),
        help="Directory containing rewritten notes",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_notes_dir),
        help="Directory to write report files",
    )
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds")
    parser.add_argument("--workers", type=int, default=12, help="Concurrent HTTP workers")
    parser.add_argument(
        "--file-glob",
        default="rewritten_*.md",
        help="Glob used to select rewritten markdown files (default: rewritten_*.md)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    workers = max(args.workers, 1)
    report = run_audit(input_dir, args.timeout, workers, args.file_glob)
    json_path, csv_path = write_outputs(report, Path(args.output_dir))

    print(f"Notes scanned: {report['note_count']}")
    print(f"Total links checked: {report['total_links']}")
    print(
        f"ok={report['ok_links']} blocked={report['blocked_links']} "
        f"invalid={report['invalid_links']} error={report['error_links']}"
    )
    print(f"Notes with validation warnings: {report['notes_with_warnings']}")
    print(f"JSON report: {json_path}")
    print(f"CSV report:  {csv_path}")


if __name__ == "__main__":
    main()
