#!/usr/bin/env python3
"""
Strip trailing `.md` suffixes from Obsidian wikilink targets.

Examples:
- [[VIII-2. Commercial Gym Equipment.md]] -> [[VIII-2. Commercial Gym Equipment]]
- [[Note.md#Heading|Alias]] -> [[Note#Heading|Alias]]

Default mode is dry-run. Use --apply to write changes.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from interlink_validator import iter_markdown_files


WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")


@dataclass
class LinkRewrite:
    source_file: str
    line_number: int
    original: str
    rewritten: str


def split_target(link_body: str) -> Tuple[str, str, str]:
    alias = ""
    before_alias = link_body
    if "|" in link_body:
        before_alias, alias = link_body.split("|", 1)

    anchor = ""
    target = before_alias
    if "#" in before_alias:
        target, anchor = before_alias.split("#", 1)

    return target.strip(), anchor, alias


def rewrite_link_body(link_body: str) -> Tuple[str, bool]:
    target, anchor, alias = split_target(link_body)
    canonical_target = re.sub(r"\.md$", "", target, flags=re.IGNORECASE)
    changed = canonical_target != target
    if not changed:
        return link_body, False

    rebuilt = canonical_target
    if anchor:
        rebuilt += f"#{anchor}"
    if alias:
        rebuilt += f"|{alias}"
    return rebuilt, True


def rewrite_line(line: str) -> Tuple[str, List[Tuple[str, str]]]:
    replacements: List[Tuple[str, str]] = []

    def _replace(match: re.Match[str]) -> str:
        body = match.group(1)
        rewritten, changed = rewrite_link_body(body)
        if not changed:
            return match.group(0)
        original_token = f"[[{body}]]"
        rewritten_token = f"[[{rewritten}]]"
        replacements.append((original_token, rewritten_token))
        return rewritten_token

    new_line = WIKILINK_RE.sub(_replace, line)
    return new_line, replacements


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


def collect_targets(vault_root: Path, include_organized: bool, extra_exclude: Set[str]) -> Iterable[Path]:
    return iter_markdown_files(vault_root, extra_exclude=extra_exclude, include_organized=include_organized)


def process_file(vault_root: Path, path: Path) -> Tuple[Optional[str], List[LinkRewrite]]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None, []

    new_lines: List[str] = []
    rewrites: List[LinkRewrite] = []
    changed = False

    for idx, line in enumerate(text.splitlines(keepends=True), start=1):
        new_line, replacements = rewrite_line(line)
        if replacements:
            changed = True
            rel_path = str(path.relative_to(vault_root)) if vault_root in path.parents else str(path)
            for original, rewritten in replacements:
                rewrites.append(
                    LinkRewrite(
                        source_file=rel_path,
                        line_number=idx,
                        original=original,
                        rewritten=rewritten,
                    )
                )
        new_lines.append(new_line)

    if not changed:
        return None, []
    return "".join(new_lines), rewrites


def write_csv(output_csv: Path, rows: List[LinkRewrite]) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source_file", "line_number", "original", "rewritten"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "source_file": row.source_file,
                    "line_number": row.line_number,
                    "original": row.original,
                    "rewritten": row.rewritten,
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Strip .md suffixes from wikilink targets.")
    parser.add_argument(
        "--vault-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Vault root directory to scan",
    )
    parser.add_argument(
        "--output-csv",
        default=str(
            Path(__file__).resolve().parents[1]
            / "processed_archive"
            / "processed_notes"
            / "wikilink_md_strip_changes.csv"
        ),
        help="CSV file to write suggested or applied rewrites",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Extra directory name to exclude (repeatable)",
    )
    parser.add_argument(
        "--include-organized",
        action="store_true",
        help="Also scan organized_library topic mirrors",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply rewrites to files (default is dry-run)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vault_root = Path(args.vault_root).resolve()
    output_csv = Path(args.output_csv).resolve()

    if not vault_root.exists():
        print(f"Vault root not found: {vault_root}")
        return 2

    extra_exclude = set(args.exclude_dir)
    files = list(collect_targets(vault_root, args.include_organized, extra_exclude))
    total_rows: List[LinkRewrite] = []
    touched_files = 0

    for path in files:
        rewritten_text, rewrites = process_file(vault_root, path)
        if not rewrites:
            continue
        total_rows.extend(rewrites)
        touched_files += 1
        if args.apply and rewritten_text is not None:
            atomic_write(path, rewritten_text)

    write_csv(output_csv, total_rows)
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"Scanned files: {len(files)}")
    print(f"Touched files: {touched_files}")
    print(f"Rewritten wikilinks: {len(total_rows)}")
    print(f"CSV report: {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
