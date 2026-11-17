#!/usr/bin/env python3
"""Migrate note metadata from bold-inline form to YAML frontmatter."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set

from note_metadata import parse_frontmatter, read_metadata, replace_or_insert_frontmatter
from interlink_validator import iter_markdown_files


ID_LINE_RE = re.compile(r"^\s*\*\*ID:\*\*.*\n?", flags=re.MULTILINE)
CREATED_LINE_RE = re.compile(r"^\s*\*\*Created:\*\*.*\n?", flags=re.MULTILINE)
UPDATED_LINE_RE = re.compile(r"^\s*\*\*Updated:\*\*.*\n?", flags=re.MULTILINE)


@dataclass
class MigrationRow:
    file_path: str
    status: str
    detail: str = ""


def derive_section_from_name(file_name: str) -> str:
    stem = Path(file_name).stem
    if stem.startswith("IX"):
        return "IX"
    if stem.startswith("VIII"):
        return "VIII"
    if stem.startswith("VII"):
        return "VII"
    if stem.startswith("VI"):
        return "VI"
    if stem.startswith("IV"):
        return "IV"
    if stem.startswith("V"):
        return "V"
    if stem.startswith("III"):
        return "III"
    if stem.startswith("II"):
        return "II"
    if stem.startswith("I"):
        return "I"
    if stem.startswith("X"):
        return "X"
    if stem.startswith("EXL"):
        return "EXL"
    if stem.startswith("Z"):
        return "Z"
    if stem and stem[0].isalpha():
        return stem[0].upper()
    return "Unknown"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(path.parent), delete=False
    ) as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def clean_inline_metadata(content: str) -> str:
    cleaned = ID_LINE_RE.sub("", content)
    cleaned = CREATED_LINE_RE.sub("", cleaned)
    cleaned = UPDATED_LINE_RE.sub("", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.lstrip("\n")


def migrate_file(path: Path, vault_root: Path) -> MigrationRow:
    try:
        original = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return MigrationRow(str(path.relative_to(vault_root)), "failed", f"read-error: {exc}")

    frontmatter, _ = parse_frontmatter(original)
    rel = str(path.relative_to(vault_root))
    if frontmatter:
        return MigrationRow(rel, "skipped", "already-has-frontmatter")

    metadata = read_metadata(original)
    if not metadata.note_id and not metadata.created and not metadata.updated:
        return MigrationRow(rel, "skipped", "no-inline-metadata")

    payload = {
        "id": metadata.note_id,
        "created": metadata.created,
        "updated": metadata.updated,
        "section": metadata.section or derive_section_from_name(path.name),
    }
    cleaned = clean_inline_metadata(original)
    rewritten = replace_or_insert_frontmatter(cleaned, payload)

    if rewritten == original:
        return MigrationRow(rel, "skipped", "no-change")

    return MigrationRow(rel, "ready", rewritten)


def collect_files(vault_root: Path, include_organized: bool, extra_exclude: Set[str]) -> Iterable[Path]:
    for path in iter_markdown_files(
        vault_root,
        extra_exclude=extra_exclude,
        include_organized=include_organized,
    ):
        rel = path.relative_to(vault_root)
        if rel.parts[:2] == ("organized_library", "automation_tools"):
            continue
        if "processed_archive" in rel.parts:
            continue
        if "original_backup" in rel.parts:
            continue
        yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate bold metadata to YAML frontmatter.")
    parser.add_argument(
        "--vault-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Vault root directory",
    )
    parser.add_argument(
        "--include-organized",
        action="store_true",
        help="Include organized_library topic mirrors",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Extra directory names to exclude",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write migrated files (default dry-run)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vault_root = Path(args.vault_root).resolve()
    if not vault_root.exists():
        print(f"Vault root not found: {vault_root}")
        return 2

    rows: List[MigrationRow] = []
    apply_count = 0
    ready_count = 0

    for path in collect_files(vault_root, args.include_organized, set(args.exclude_dir)):
        row = migrate_file(path, vault_root)
        if row.status == "ready":
            ready_count += 1
            new_text = row.detail
            row.detail = "converted-inline-metadata"
            if args.apply:
                atomic_write(path, new_text)
                apply_count += 1
                row.status = "applied"
        rows.append(row)

    print(f"Scanned files: {len(rows)}")
    print(f"Ready conversions: {ready_count}")
    print(f"Applied conversions: {apply_count}")
    print(f"Skipped: {sum(1 for row in rows if row.status == 'skipped')}")
    print(f"Failed: {sum(1 for row in rows if row.status == 'failed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
