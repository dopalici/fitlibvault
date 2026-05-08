#!/usr/bin/env python3
"""
Validate every Obsidian-style [[wikilink]] in the vault.

For each wikilink we answer four questions:

1. Does the link target actually exist as a markdown file?
2. Is the target a stub (empty file or title-only / very low-content placeholder)?
3. Are there multiple files in the vault with the same basename, so Obsidian
   could resolve the link to the wrong one (shadowing)?
4. If the link is broken, what is the closest existing title we could suggest?

Outputs:

- JSON report:    interlink_audit_report.json
- Markdown report: interlink_audit.md
- Optional CSV:   interlink_audit_links.csv

By default the validator scans the entire vault root. Use ``--scope`` to
narrow it (for example to ``--scope rewritten`` to validate the staging
area before promotion).
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")


# Folders we never want to scan for wikilinks (build artefacts, caches, etc).
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".obsidian",
    ".cache",
    ".cursor",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "site-packages",
    "dist",
    "build",
    "web app fitlib",
    "automation_tools",
    "processed_archive",
    "original_backup",
}

# Subdirectories below ``organized_library`` are duplicate "sorted views" of
# vault-root files. They cause noisy false-positive shadow groups, so we
# exclude them by default. Pass ``--include-organized`` to opt in.
ORGANIZED_LIBRARY_TOPIC_DIRS = {
    "body_composition",
    "cardiovascular_training",
    "cross_training",
    "documentation",
    "elite_performance",
    "equipment_technology",
    "ethics",
    "exercise_library",
    "foundation",
    "frontend",
    "health_conditions",
    "hormones_fitness",
    "integrated_approaches",
    "key_overviews",
    "long_term_development",
    "nutrition_diet",
    "performance_factors",
    "recovery",
    "resistance_training",
    "special_populations",
    "sports_specific",
    "technology",
}

# Filename prefixes/suffixes that should never be treated as link targets.
NON_LINK_TARGET_PREFIXES = (
    "rewritten_",
    "._",
    "section_",  # intermediate per-section processing reports
)

NON_LINK_TARGET_SUFFIXES = (
    "_report.md",
    "_summary.md",
)


@dataclass
class TargetFile:
    path: Path
    size: int
    word_count: int
    is_stub: bool
    stub_reason: str = ""


@dataclass
class WikilinkOccurrence:
    source_file: str
    line_number: int
    raw: str
    target_basename: str
    target_anchor: str = ""
    status: str = "ok"  # ok | stub | shadowed | broken
    resolved_path: Optional[str] = None
    candidates: List[str] = field(default_factory=list)
    suggestion: Optional[str] = None
    detail: str = ""


def normalize_target(raw_link: str) -> Tuple[str, str]:
    """Split ``Note Name#Heading|alias`` into (basename, anchor)."""
    text = raw_link.split("|", 1)[0].strip()
    if "#" in text:
        base, _, anchor = text.partition("#")
        return base.strip(), anchor.strip()
    return text, ""


def is_excluded_dir(rel_dir: Path, extra_exclude: Set[str]) -> bool:
    parts = set(rel_dir.parts)
    if parts & DEFAULT_EXCLUDE_DIRS:
        return True
    if parts & extra_exclude:
        return True
    return False


def iter_markdown_files(
    root: Path,
    extra_exclude: Optional[Set[str]] = None,
    include_organized: bool = False,
) -> Iterable[Path]:
    extra_exclude = extra_exclude or set()
    for path in root.rglob("*.md"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if is_excluded_dir(rel.parent, extra_exclude):
            continue
        if (
            not include_organized
            and len(rel.parts) >= 2
            and rel.parts[0] == "organized_library"
            and rel.parts[1] in ORGANIZED_LIBRARY_TOPIC_DIRS
        ):
            continue
        if path.name.startswith(NON_LINK_TARGET_PREFIXES):
            continue
        if path.name.endswith(NON_LINK_TARGET_SUFFIXES):
            continue
        yield path


def classify_target(path: Path, min_content_words: int) -> TargetFile:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return TargetFile(path=path, size=0, word_count=0, is_stub=True, stub_reason=f"unreadable: {exc}")

    size = path.stat().st_size if path.exists() else 0
    if size == 0:
        return TargetFile(path=path, size=0, word_count=0, is_stub=True, stub_reason="empty file")

    # Strip frontmatter and bold metadata (`**ID:**`, `**Created:**`) before counting.
    body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
    body = re.sub(r"^\s*\*\*[^*]+\*\*\s*[^\n]*\n", "", body, flags=re.MULTILINE)
    body = re.sub(r"^#{1,6}\s+.*$", "", body, flags=re.MULTILINE)
    word_count = len(body.split())
    if word_count < min_content_words:
        return TargetFile(
            path=path,
            size=size,
            word_count=word_count,
            is_stub=True,
            stub_reason=f"title-only / low content ({word_count} body words)",
        )
    return TargetFile(path=path, size=size, word_count=word_count, is_stub=False)


def build_target_index(
    vault_root: Path,
    extra_exclude: Set[str],
    min_content_words: int,
    include_organized: bool = False,
) -> Tuple[Dict[str, List[TargetFile]], List[str]]:
    """Map basename (without .md) -> list of TargetFile candidates."""
    index: Dict[str, List[TargetFile]] = defaultdict(list)
    all_basenames: Set[str] = set()
    for path in iter_markdown_files(
        vault_root, extra_exclude, include_organized=include_organized
    ):
        target = classify_target(path, min_content_words=min_content_words)
        basename = path.stem
        index[basename].append(target)
        all_basenames.add(basename)
    return index, sorted(all_basenames)


def resolve_link(
    occurrence: WikilinkOccurrence,
    index: Dict[str, List[TargetFile]],
    all_basenames: List[str],
    suggestion_cutoff: float,
) -> WikilinkOccurrence:
    candidates = index.get(occurrence.target_basename, [])

    if not candidates:
        # No exact match. Try case-insensitive then fuzzy suggestion.
        fold = occurrence.target_basename.lower()
        ci = [name for name in all_basenames if name.lower() == fold]
        if ci:
            candidates = index.get(ci[0], [])
            occurrence.detail = "case-mismatch resolved"
            occurrence.suggestion = ci[0]
        else:
            best = difflib.get_close_matches(
                occurrence.target_basename, all_basenames, n=1, cutoff=suggestion_cutoff
            )
            occurrence.suggestion = best[0] if best else None
            occurrence.status = "broken"
            occurrence.detail = "no markdown file with that basename"
            return occurrence

    if len(candidates) > 1:
        occurrence.status = "shadowed"
        occurrence.candidates = [str(c.path) for c in candidates]
        occurrence.detail = f"{len(candidates)} files share this basename"
        non_stub = [c for c in candidates if not c.is_stub]
        chosen = non_stub[0] if non_stub else candidates[0]
        occurrence.resolved_path = str(chosen.path)
        if all(c.is_stub for c in candidates):
            occurrence.status = "stub"
            occurrence.detail += "; all duplicates are stubs"
        return occurrence

    target = candidates[0]
    occurrence.resolved_path = str(target.path)
    if target.is_stub:
        occurrence.status = "stub"
        occurrence.detail = target.stub_reason
    return occurrence


def collect_wikilinks(
    vault_root: Path,
    scope_paths: Iterable[Path],
) -> List[WikilinkOccurrence]:
    occurrences: List[WikilinkOccurrence] = []
    for path in scope_paths:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(path.relative_to(vault_root)) if vault_root in path.parents else str(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in WIKILINK_RE.finditer(line):
                raw = match.group(1)
                base, anchor = normalize_target(raw)
                occurrences.append(
                    WikilinkOccurrence(
                        source_file=rel,
                        line_number=line_no,
                        raw=raw,
                        target_basename=base,
                        target_anchor=anchor,
                    )
                )
    return occurrences


def detect_orphan_stubs(
    index: Dict[str, List[TargetFile]],
    vault_root: Path,
) -> List[Dict[str, str]]:
    """Surface zero-byte / title-only files that can shadow real OG content."""
    stubs: List[Dict[str, str]] = []
    for basename, targets in index.items():
        for target in targets:
            if not target.is_stub:
                continue
            try:
                rel = str(target.path.relative_to(vault_root))
            except ValueError:
                rel = str(target.path)
            stubs.append(
                {
                    "basename": basename,
                    "path": rel,
                    "size": str(target.size),
                    "word_count": str(target.word_count),
                    "reason": target.stub_reason,
                }
            )
    stubs.sort(key=lambda row: (row["basename"], row["path"]))
    return stubs


def detect_shadow_groups(
    index: Dict[str, List[TargetFile]],
    vault_root: Path,
) -> List[Dict[str, object]]:
    groups: List[Dict[str, object]] = []
    for basename, targets in index.items():
        if len(targets) < 2:
            continue
        rows: List[Dict[str, str]] = []
        for target in targets:
            try:
                rel = str(target.path.relative_to(vault_root))
            except ValueError:
                rel = str(target.path)
            rows.append(
                {
                    "path": rel,
                    "is_stub": "yes" if target.is_stub else "no",
                    "word_count": str(target.word_count),
                }
            )
        groups.append({"basename": basename, "files": rows})
    groups.sort(key=lambda row: row["basename"])
    return groups


def write_reports(
    output_dir: Path,
    occurrences: List[WikilinkOccurrence],
    stubs: List[Dict[str, str]],
    shadows: List[Dict[str, object]],
    write_csv: bool,
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "total_links": len(occurrences),
        "ok": sum(1 for o in occurrences if o.status == "ok"),
        "stub": sum(1 for o in occurrences if o.status == "stub"),
        "shadowed": sum(1 for o in occurrences if o.status == "shadowed"),
        "broken": sum(1 for o in occurrences if o.status == "broken"),
    }

    json_path = output_dir / "interlink_audit_report.json"
    json_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "stubs": stubs,
                "shadow_groups": shadows,
                "links": [asdict(o) for o in occurrences],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    md_lines: List[str] = ["# Interlink Audit", ""]
    md_lines.append("## Summary")
    for key, value in summary.items():
        md_lines.append(f"- {key}: {value}")
    md_lines.append("")

    if stubs:
        md_lines.append(f"## Stub / Shadow-Risk Files ({len(stubs)})")
        md_lines.append("These markdown files exist but have no real content. ")
        md_lines.append("Obsidian and the website builder may resolve a [[wikilink]] to one ")
        md_lines.append("of these instead of the OG file. Consider deleting or filling them.")
        md_lines.append("")
        for row in stubs:
            md_lines.append(f"- `{row['path']}` ({row['reason']})")
        md_lines.append("")

    if shadows:
        md_lines.append(f"## Duplicate Basenames ({len(shadows)})")
        md_lines.append("Multiple files share the same name. Wikilink targets are ambiguous.")
        md_lines.append("")
        for group in shadows:
            md_lines.append(f"### `[[{group['basename']}]]`")
            for row in group["files"]:
                stub_marker = " (stub)" if row["is_stub"] == "yes" else ""
                md_lines.append(f"- `{row['path']}`{stub_marker} — {row['word_count']} body words")
            md_lines.append("")

    broken = [o for o in occurrences if o.status == "broken"]
    if broken:
        md_lines.append(f"## Broken Links ({len(broken)})")
        for o in broken:
            suggestion = f" → suggest `{o.suggestion}`" if o.suggestion else ""
            md_lines.append(
                f"- `{o.source_file}:{o.line_number}` `[[{o.raw}]]`{suggestion}"
            )
        md_lines.append("")

    stub_links = [o for o in occurrences if o.status == "stub"]
    if stub_links:
        md_lines.append(f"## Links Pointing at Stubs ({len(stub_links)})")
        for o in stub_links:
            md_lines.append(
                f"- `{o.source_file}:{o.line_number}` `[[{o.raw}]]` → "
                f"`{o.resolved_path}` ({o.detail})"
            )
        md_lines.append("")

    md_path = output_dir / "interlink_audit.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    paths = {"json": json_path, "markdown": md_path}

    if write_csv:
        csv_path = output_dir / "interlink_audit_links.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "source_file",
                    "line_number",
                    "raw",
                    "target_basename",
                    "status",
                    "resolved_path",
                    "suggestion",
                    "detail",
                ],
            )
            writer.writeheader()
            for o in occurrences:
                writer.writerow(
                    {
                        "source_file": o.source_file,
                        "line_number": o.line_number,
                        "raw": o.raw,
                        "target_basename": o.target_basename,
                        "status": o.status,
                        "resolved_path": o.resolved_path or "",
                        "suggestion": o.suggestion or "",
                        "detail": o.detail,
                    }
                )
        paths["csv"] = csv_path

    return paths


def parse_scope(scope: str, vault_root: Path, include_organized: bool) -> List[Path]:
    if scope == "vault":
        return list(iter_markdown_files(vault_root, include_organized=include_organized))
    if scope == "rewritten":
        staging = vault_root / "organized_library" / "processed_archive" / "processed_notes"
        return sorted(staging.glob("rewritten_*.md"))
    if scope == "organized":
        organized = vault_root / "organized_library"
        return [
            p for p in organized.rglob("*.md")
            if "processed_archive" not in p.parts and "automation_tools" not in p.parts
        ]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Obsidian wikilinks.")
    parser.add_argument(
        "--vault-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Vault root directory",
    )
    parser.add_argument(
        "--output-dir",
        default=str(
            Path(__file__).resolve().parents[2] / "processed_archive" / "processed_notes"
        ),
        help="Where to write the audit reports",
    )
    parser.add_argument(
        "--scope",
        choices=["vault", "rewritten", "organized"],
        default="vault",
        help="Which file set to scan for wikilinks",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Additional directory name to exclude (repeatable)",
    )
    parser.add_argument(
        "--min-content-words",
        type=int,
        default=40,
        help="Files with fewer body words than this are flagged as stubs",
    )
    parser.add_argument(
        "--suggestion-cutoff",
        type=float,
        default=0.78,
        help="Fuzzy-match cutoff for broken-link suggestions",
    )
    parser.add_argument("--write-csv", action="store_true", help="Also emit a CSV report")
    parser.add_argument(
        "--include-organized",
        action="store_true",
        help=(
            "Also index the per-topic mirror folders under organized_library/. "
            "Default off because those are duplicate sorted-views and produce "
            "noisy false-positive shadow groups."
        ),
    )
    parser.add_argument(
        "--fail-on",
        choices=["never", "broken", "any"],
        default="never",
        help="Exit with code 1 when any of these conditions fire",
    )
    args = parser.parse_args()

    vault_root = Path(args.vault_root).resolve()
    if not vault_root.exists():
        print(f"Vault root not found: {vault_root}")
        return 2

    extra_exclude = set(args.exclude_dir)
    output_dir = Path(args.output_dir).resolve()

    print(f"Vault root: {vault_root}")
    print(f"Scope:      {args.scope}")

    index, all_basenames = build_target_index(
        vault_root,
        extra_exclude,
        args.min_content_words,
        include_organized=args.include_organized,
    )
    scope_paths = parse_scope(args.scope, vault_root, include_organized=args.include_organized)
    occurrences = collect_wikilinks(vault_root, scope_paths)
    for o in occurrences:
        resolve_link(o, index, all_basenames, args.suggestion_cutoff)

    stubs = detect_orphan_stubs(index, vault_root)
    shadows = detect_shadow_groups(index, vault_root)
    paths = write_reports(output_dir, occurrences, stubs, shadows, args.write_csv)

    summary = {
        "total_links": len(occurrences),
        "ok": sum(1 for o in occurrences if o.status == "ok"),
        "stub": sum(1 for o in occurrences if o.status == "stub"),
        "shadowed": sum(1 for o in occurrences if o.status == "shadowed"),
        "broken": sum(1 for o in occurrences if o.status == "broken"),
        "stub_files": len(stubs),
        "shadow_groups": len(shadows),
    }
    print("Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    for label, path in paths.items():
        print(f"  report.{label}: {path}")

    if args.fail_on == "broken" and summary["broken"]:
        return 1
    if args.fail_on == "any" and (
        summary["broken"] or summary["stub"] or summary["shadowed"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
