#!/usr/bin/env python3
"""
Promote rewritten notes to canonical OG notes without renaming files.

Workflow:
1) Read rewritten files from organized_library/processed_archive/processed_notes
2) Validate required structure + ID consistency
3) Replace root OG file contents in place (same filename), preserving wikilink targets
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


AUTOMATION_ROOT = Path(__file__).resolve().parents[2]
if str(AUTOMATION_ROOT) not in sys.path:
    sys.path.append(str(AUTOMATION_ROOT))

from utility_scripts.note_metadata import read_metadata


REQUIRED_SECTIONS = [
    "## Quick Takeaway",
    "## Key Points",
    "## Deep Dive",
    "## Research Evidence",
    "## Practical Applications",
    "## Common Mistakes",
    "## Related Concepts",
    "## Update Log",
]


@dataclass
class PromotionResult:
    file_name: str
    status: str
    reason: str = ""


def extract_id(markdown: str) -> str:
    return read_metadata(markdown).note_id


def validate_structure(markdown: str) -> List[str]:
    issues: List[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in markdown:
            issues.append(f"Missing section: {section}")
    if "[[" not in markdown:
        issues.append("No wikilinks found; expected Obsidian cross-links")
    return issues


def promote_notes(vault_root: Path, rewritten_dir: Path, apply_changes: bool) -> List[PromotionResult]:
    rewritten_files = sorted(rewritten_dir.glob("rewritten_*.md"))
    results: List[PromotionResult] = []

    for rewritten_path in rewritten_files:
        canonical_name = rewritten_path.name.replace("rewritten_", "", 1)
        canonical_path = vault_root / canonical_name

        if not canonical_path.exists():
            results.append(
                PromotionResult(canonical_name, "skipped", "Canonical OG file not found at vault root")
            )
            continue

        rewritten_content = rewritten_path.read_text(encoding="utf-8")
        canonical_content = canonical_path.read_text(encoding="utf-8")

        issues = validate_structure(rewritten_content)
        rewritten_id = extract_id(rewritten_content)
        canonical_id = extract_id(canonical_content)
        if rewritten_id and canonical_id and rewritten_id != canonical_id:
            issues.append(f"ID mismatch (rewritten={rewritten_id}, canonical={canonical_id})")

        if issues:
            results.append(PromotionResult(canonical_name, "failed", "; ".join(issues)))
            continue

        if apply_changes:
            # Same target filename; only content changes. Link targets remain stable.
            shutil.copy2(rewritten_path, canonical_path)

        mode = "promoted" if apply_changes else "ready"
        results.append(PromotionResult(canonical_name, mode))

    return results


def print_summary(results: List[PromotionResult], apply_changes: bool) -> int:
    promoted = sum(1 for r in results if r.status in {"promoted", "ready"})
    failed = sum(1 for r in results if r.status == "failed")
    skipped = sum(1 for r in results if r.status == "skipped")

    print(f"\nProcessed rewritten notes: {len(results)}")
    print(f"{'Promoted' if apply_changes else 'Ready to promote'}: {promoted}")
    print(f"Failed validation: {failed}")
    print(f"Skipped: {skipped}")

    for row in results:
        if row.status in {"failed", "skipped"}:
            print(f"- {row.file_name}: {row.status} ({row.reason})")

    return 1 if failed > 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote rewritten notes to OG vault files without renaming."
    )
    parser.add_argument(
        "--vault-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Path to vault root containing canonical OG markdown files",
    )
    parser.add_argument(
        "--rewritten-dir",
        default=str(
            Path(__file__).resolve().parents[2] / "processed_archive" / "processed_notes"
        ),
        help="Path containing rewritten_*.md files",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply replacements. Without this flag, runs dry-run validation only.",
    )
    args = parser.parse_args()

    vault_root = Path(args.vault_root)
    rewritten_dir = Path(args.rewritten_dir)

    if not vault_root.exists():
        print(f"Vault root not found: {vault_root}")
        return 2
    if not rewritten_dir.exists():
        print(f"Rewritten directory not found: {rewritten_dir}")
        return 2

    results = promote_notes(vault_root=vault_root, rewritten_dir=rewritten_dir, apply_changes=args.apply)
    return print_summary(results, apply_changes=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
