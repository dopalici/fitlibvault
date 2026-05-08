#!/usr/bin/env python3
"""
Interactive, per-file promotion of rewritten notes into OG vault files.

Why this exists:

- ``promote_rewritten_to_og.py`` is all-or-nothing. This script lets you
  approve each rewrite individually, stamps the OG file with the actual
  promotion date, atomically replaces the file (so wikilinks never break
  mid-write), records a ``promotion_history.jsonl`` audit trail, and moves
  the accepted ``rewritten_*.md`` into a dated confirmed-archive so it
  cannot accidentally be re-promoted later.

For each rewritten file we show:

  - title / ID
  - structural validation (required sections, ID match)
  - wikilink integrity (every [[link]] resolves to a real, non-stub file)
  - citation/recommendation deltas vs the OG
  - a unified diff preview (truncated)

Then the user picks: accept (y) | skip (s) | open-diff (d) | quit (q).
A ``--auto-yes`` flag exists for headless runs (still respects validation
gates).

Invocation:

    python3 staged_promotion.py                       # dry-run queue summary
    python3 staged_promotion.py --interactive         # per-file prompts
    python3 staged_promotion.py --auto-yes            # accept every passing file
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
AUTOMATION_ROOT = REPO_ROOT / "organized_library" / "automation_tools"
DEFAULT_NOTES_DIR = REPO_ROOT / "organized_library" / "processed_archive" / "processed_notes"
DEFAULT_HISTORY = AUTOMATION_ROOT / "promotion_history.jsonl"
DEFAULT_CONFIRMED_ARCHIVE = (
    REPO_ROOT / "organized_library" / "processed_archive" / "confirmed_archive"
)

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


# Match the literal '(Updated: ...)' segment that lives next to **Created:**.
UPDATED_TAG_RE = re.compile(r"\(Updated:\s*[^)]+\)")
WIKILINK_RE = re.compile(r"\[\[([^\]\n]+?)\]\]")


@dataclass
class CandidateReview:
    rewritten_path: Path
    og_path: Path
    title: str
    note_id: str
    structure_issues: List[str] = field(default_factory=list)
    link_issues: List[str] = field(default_factory=list)
    citation_delta: int = 0
    recommendation_delta: int = 0
    new_doi_count: int = 0
    new_pmid_count: int = 0
    diff_preview: str = ""

    @property
    def is_blocked(self) -> bool:
        return bool(self.structure_issues) or bool(self.link_issues)


def extract_id(markdown: str) -> str:
    match = re.search(r"\*\*ID:\*\*\s*([^\n*]+?)(?:\s+\*\*Created:|\s*$)", markdown, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_title(markdown: str) -> str:
    match = re.search(r"^#{1,3}\s+(.+)$", markdown, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_structure(rewritten: str, og: str) -> List[str]:
    issues: List[str] = []
    for section in REQUIRED_SECTIONS:
        if section not in rewritten:
            issues.append(f"Missing section: {section}")
    if "[[" not in rewritten:
        issues.append("No wikilinks found; expected Obsidian cross-links")

    rid = extract_id(rewritten)
    cid = extract_id(og)
    if rid and cid and rid != cid:
        issues.append(f"ID mismatch (rewritten={rid}, canonical={cid})")
    return issues


def check_wikilinks(rewritten: str, target_index: Dict[str, List[Path]], stub_paths: set) -> List[str]:
    """Return a list of human-readable issues for any unresolved or stub-pointing wikilinks."""
    issues: List[str] = []
    seen: set = set()
    for match in WIKILINK_RE.finditer(rewritten):
        raw = match.group(1)
        base = raw.split("|", 1)[0].split("#", 1)[0].strip()
        if not base or base in seen:
            continue
        seen.add(base)
        candidates = target_index.get(base) or target_index.get(base.lower())
        if not candidates:
            issues.append(f"broken: [[{base}]]")
            continue
        if all(path in stub_paths for path in candidates):
            issues.append(f"stub: [[{base}]]")
    return issues


def build_target_index(vault_root: Path, min_words: int) -> Tuple[Dict[str, List[Path]], set]:
    """Map basename -> list of paths and return the set of stub paths."""
    index: Dict[str, List[Path]] = {}
    stubs: set = set()
    excluded_parts = {".git", ".obsidian", ".cache", "__pycache__", "node_modules", "web app fitlib"}
    for path in vault_root.rglob("*.md"):
        try:
            rel = path.relative_to(vault_root)
        except ValueError:
            continue
        if set(rel.parts) & excluded_parts:
            continue
        if path.name.startswith("rewritten_"):
            continue
        index.setdefault(path.stem, []).append(path)
        # Stub heuristic mirrors interlink_validator
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            stubs.add(path)
            continue
        if path.stat().st_size == 0:
            stubs.add(path)
            continue
        body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
        body = re.sub(r"^\s*\*\*[^*]+\*\*\s*[^\n]*\n", "", body, flags=re.MULTILINE)
        body = re.sub(r"^#{1,6}\s+.*$", "", body, flags=re.MULTILINE)
        if len(body.split()) < min_words:
            stubs.add(path)
    # Lowercase alias map for case-mismatch resolution.
    for stem, paths in list(index.items()):
        index.setdefault(stem.lower(), paths)
    return index, stubs


def extract_citation_set(text: str) -> Tuple[set, set]:
    dois = set(re.findall(r"https?://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", text, re.IGNORECASE))
    pmids = set(re.findall(r"https?://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", text, re.IGNORECASE))
    return {d.lower() for d in dois}, pmids


def extract_recommendation_signals(text: str) -> set:
    triggers = ("should", "recommend", "protocol", "dosage", "intensity", "frequency", "duration")
    out: set = set()
    for line in text.splitlines():
        lower = line.lower()
        if line.lstrip().startswith("-") or any(t in lower for t in triggers):
            normalized = re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s%-]", "", lower)).strip()
            if len(normalized) > 20:
                out.add(normalized[:200])
    return out


def build_diff_preview(og: str, rewritten: str, max_lines: int = 80) -> str:
    diff = difflib.unified_diff(
        og.splitlines(keepends=False),
        rewritten.splitlines(keepends=False),
        fromfile="OG",
        tofile="rewritten",
        lineterm="",
        n=2,
    )
    lines = list(diff)
    if len(lines) > max_lines:
        head = lines[:max_lines]
        head.append(f"... ({len(lines) - max_lines} more lines truncated; use --diff-lines to expand)")
        return "\n".join(head)
    return "\n".join(lines)


def stamp_metadata(rewritten_text: str, promotion_date: str, summary: str) -> str:
    """Insert/refresh the Updated tag and append an Update Log entry."""
    if UPDATED_TAG_RE.search(rewritten_text):
        new_text = UPDATED_TAG_RE.sub(f"(Updated: {promotion_date})", rewritten_text, count=1)
    else:
        new_text = re.sub(
            r"(\*\*Created:\*\*\s*[^\n]+)",
            r"\1 (Updated: " + promotion_date + ")",
            rewritten_text,
            count=1,
        )

    log_marker = "## Update Log"
    log_entry = f"- {promotion_date}: Promoted to OG. {summary}".rstrip()
    if log_marker in new_text:
        idx = new_text.index(log_marker) + len(log_marker)
        # Avoid duplicating an entry that already mentions today's date.
        tail = new_text[idx:]
        if promotion_date in tail.split("##", 1)[0]:
            return new_text
        return new_text[:idx] + "\n" + log_entry + "\n" + tail.lstrip("\n")
    return new_text.rstrip() + f"\n\n{log_marker}\n{log_entry}\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
        shutil.copystat(path, tmp_name) if path.exists() else None
        os.replace(tmp_name, path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def append_history(history_path: Path, payload: Dict[str, object]) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def review_candidate(
    rewritten_path: Path,
    vault_root: Path,
    target_index: Dict[str, List[Path]],
    stub_paths: set,
    diff_lines: int,
) -> Optional[CandidateReview]:
    canonical_name = rewritten_path.name.replace("rewritten_", "", 1)
    og_path = vault_root / canonical_name
    if not og_path.exists():
        return CandidateReview(
            rewritten_path=rewritten_path,
            og_path=og_path,
            title=canonical_name,
            note_id="",
            structure_issues=[f"OG file missing at vault root: {canonical_name}"],
        )

    rewritten = rewritten_path.read_text(encoding="utf-8")
    og = og_path.read_text(encoding="utf-8")

    review = CandidateReview(
        rewritten_path=rewritten_path,
        og_path=og_path,
        title=extract_title(rewritten) or canonical_name,
        note_id=extract_id(rewritten),
    )
    review.structure_issues = validate_structure(rewritten, og)
    review.link_issues = check_wikilinks(rewritten, target_index, stub_paths)

    og_dois, og_pmids = extract_citation_set(og)
    rw_dois, rw_pmids = extract_citation_set(rewritten)
    review.new_doi_count = len(rw_dois - og_dois)
    review.new_pmid_count = len(rw_pmids - og_pmids)
    review.citation_delta = review.new_doi_count + review.new_pmid_count

    og_recs = extract_recommendation_signals(og)
    rw_recs = extract_recommendation_signals(rewritten)
    review.recommendation_delta = len(og_recs.symmetric_difference(rw_recs))

    review.diff_preview = build_diff_preview(og, rewritten, max_lines=diff_lines)
    return review


def render_review(review: CandidateReview, idx: int, total: int) -> str:
    buf = io.StringIO()
    buf.write(f"\n[{idx}/{total}] {review.title}\n")
    buf.write(f"  ID:        {review.note_id or '(none)'}\n")
    buf.write(f"  rewritten: {review.rewritten_path}\n")
    buf.write(f"  OG:        {review.og_path}\n")
    buf.write(
        f"  deltas:    +{review.new_doi_count} DOI / +{review.new_pmid_count} PMID / "
        f"recs={review.recommendation_delta}\n"
    )
    if review.structure_issues:
        buf.write("  STRUCTURE ISSUES:\n")
        for issue in review.structure_issues:
            buf.write(f"    - {issue}\n")
    if review.link_issues:
        buf.write(f"  LINK ISSUES ({len(review.link_issues)} total, first 8 shown):\n")
        for issue in review.link_issues[:8]:
            buf.write(f"    - {issue}\n")
    buf.write("\n  --- diff preview ---\n")
    for line in review.diff_preview.splitlines():
        buf.write(f"    {line}\n")
    buf.write("  ---\n")
    return buf.getvalue()


def prompt_user(default_action: str) -> str:
    try:
        choice = input(
            f"  accept (y) / skip (s) / show full diff (d) / quit (q) [{default_action}]: "
        ).strip().lower()
    except EOFError:
        return "q"
    return choice or default_action


def show_full_diff(review: CandidateReview) -> None:
    og = review.og_path.read_text(encoding="utf-8")
    rewritten = review.rewritten_path.read_text(encoding="utf-8")
    print(build_diff_preview(og, rewritten, max_lines=10_000))


def promote_one(
    review: CandidateReview,
    promotion_date: str,
    confirmed_archive: Path,
    history_path: Path,
    dry_run: bool,
) -> Dict[str, object]:
    summary = (
        f"+{review.new_doi_count} DOI, +{review.new_pmid_count} PMID, "
        f"recommendation_delta={review.recommendation_delta}."
    )
    rewritten_text = review.rewritten_path.read_text(encoding="utf-8")
    stamped = stamp_metadata(rewritten_text, promotion_date, summary)

    record: Dict[str, object] = {
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "promotion_date": promotion_date,
        "file": review.og_path.name,
        "id": review.note_id,
        "title": review.title,
        "new_dois": review.new_doi_count,
        "new_pmids": review.new_pmid_count,
        "recommendation_delta": review.recommendation_delta,
        "rewritten_path": str(review.rewritten_path),
        "og_path": str(review.og_path),
        "dry_run": dry_run,
    }

    if dry_run:
        return record

    atomic_write(review.og_path, stamped)
    archive_dir = confirmed_archive / promotion_date
    archive_dir.mkdir(parents=True, exist_ok=True)
    target = archive_dir / review.rewritten_path.name
    if target.exists():
        target.unlink()
    shutil.move(str(review.rewritten_path), str(target))
    record["archived_to"] = str(target)
    append_history(history_path, record)
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Per-file confirmation promotion with date stamping and history."
    )
    parser.add_argument("--vault-root", default=str(REPO_ROOT))
    parser.add_argument("--rewritten-dir", default=str(DEFAULT_NOTES_DIR))
    parser.add_argument("--confirmed-archive", default=str(DEFAULT_CONFIRMED_ARCHIVE))
    parser.add_argument("--history", default=str(DEFAULT_HISTORY))
    parser.add_argument("--filter", help="Only process files matching this substring", default="")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt y/s/d/q per file (default with a TTY)",
    )
    parser.add_argument(
        "--auto-yes",
        action="store_true",
        help="Accept every file that passes validation (no prompts)",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Just show the queue and validation status; never write files",
    )
    parser.add_argument("--diff-lines", type=int, default=60, help="Diff preview line cap")
    parser.add_argument("--min-stub-words", type=int, default=40,
                        help="Files with fewer body words than this count as stubs")
    parser.add_argument("--allow-link-issues", action="store_true",
                        help="Don't block on broken/stub wikilinks (logs them anyway)")
    parser.add_argument("--allow-structure-issues", action="store_true",
                        help="Don't block on missing required sections")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    vault_root = Path(args.vault_root).resolve()
    rewritten_dir = Path(args.rewritten_dir).resolve()
    confirmed_archive = Path(args.confirmed_archive).resolve()
    history_path = Path(args.history).resolve()

    if not vault_root.exists():
        print(f"Vault root not found: {vault_root}")
        return 2
    if not rewritten_dir.exists():
        print(f"Rewritten directory not found: {rewritten_dir}")
        return 2

    rewritten_files = sorted(rewritten_dir.glob("rewritten_*.md"))
    if args.filter:
        rewritten_files = [p for p in rewritten_files if args.filter in p.name]
    if not rewritten_files:
        print("No rewritten_*.md files to review.")
        return 0

    print(f"Building vault link index from {vault_root} ...")
    target_index, stub_paths = build_target_index(vault_root, args.min_stub_words)
    print(f"  indexed {sum(len(v) for v in target_index.values())} files; {len(stub_paths)} flagged as stubs")

    promotion_date = dt.date.today().isoformat()
    interactive = args.interactive or (sys.stdin.isatty() and not args.auto_yes and not args.list_only)
    print(f"Mode: {'interactive' if interactive else ('auto-yes' if args.auto_yes else 'list-only')}")
    print(f"Promotion date stamp: {promotion_date}")

    accepted: List[Dict[str, object]] = []
    skipped: List[Dict[str, object]] = []
    blocked: List[CandidateReview] = []

    for idx, rewritten_path in enumerate(rewritten_files, start=1):
        review = review_candidate(
            rewritten_path,
            vault_root,
            target_index,
            stub_paths,
            args.diff_lines,
        )
        if review is None:
            continue

        print(render_review(review, idx, len(rewritten_files)))

        gating_issues: List[str] = []
        if review.structure_issues and not args.allow_structure_issues:
            gating_issues.extend(review.structure_issues)
        if review.link_issues and not args.allow_link_issues:
            gating_issues.extend(review.link_issues)

        if gating_issues:
            print(f"  -> BLOCKED ({len(gating_issues)} gating issues)")
            blocked.append(review)
            continue

        if args.list_only:
            continue

        action = "y" if args.auto_yes else "s"
        if interactive:
            action = "?"
            while action not in {"y", "s", "q"}:
                action = prompt_user(default_action="s")
                if action == "d":
                    show_full_diff(review)
                    action = "?"
                elif action == "q":
                    print("Quit requested. Stopping queue.")
                    break

        if action == "y":
            record = promote_one(
                review,
                promotion_date=promotion_date,
                confirmed_archive=confirmed_archive,
                history_path=history_path,
                dry_run=False,
            )
            accepted.append(record)
            print(f"  -> ACCEPTED. Archived to {record.get('archived_to', '(none)')}")
        elif action == "q":
            break
        else:
            skipped.append({"file": review.og_path.name, "reason": "user-skip"})
            print("  -> SKIPPED")

    print("\n=== Summary ===")
    print(f"  accepted: {len(accepted)}")
    print(f"  skipped:  {len(skipped)}")
    print(f"  blocked:  {len(blocked)}")
    if blocked:
        print("  blocked details:")
        for review in blocked:
            reason = "; ".join(review.structure_issues + review.link_issues[:3])
            print(f"    - {review.og_path.name}: {reason}")
    if accepted:
        print(f"  history: {history_path}")
        print(f"  archive: {confirmed_archive / promotion_date}")
    return 0 if not blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
