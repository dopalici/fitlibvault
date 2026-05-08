#!/usr/bin/env python3
"""
Seamless end-to-end pipeline for rewriting and promoting markdown notes.

Sequence:
1) Rewrite notes (optional)
2) Audit citation links
3) Suggest DOI fixes
4) Validate promotion readiness (dry run)
5) Apply promotion (optional, gated on successful validation)
6) Build web content (optional)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


REPO_ROOT = Path(__file__).resolve().parents[3]
AUTOMATION_ROOT = REPO_ROOT / "organized_library" / "automation_tools"
DEFAULT_NOTES_DIR = REPO_ROOT / "organized_library" / "processed_archive" / "processed_notes"
WEB_APP_DIR = REPO_ROOT / "web app fitlib"

PROCESS_SCRIPT = AUTOMATION_ROOT / "processing_scripts" / "process_fitness_library.py"
AUDIT_SCRIPT = AUTOMATION_ROOT / "utility_scripts" / "citation_validation_audit.py"
DOI_FIX_SCRIPT = AUTOMATION_ROOT / "utility_scripts" / "citation_doi_fixer.py"
PROMOTE_SCRIPT = AUTOMATION_ROOT / "automation_scripts" / "promote_rewritten_to_og.py"
INTERLINK_SCRIPT = AUTOMATION_ROOT / "utility_scripts" / "interlink_validator.py"
STAGED_PROMOTE_SCRIPT = AUTOMATION_ROOT / "automation_scripts" / "staged_promotion.py"


def run_cmd(
    command: List[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    step_name: str,
) -> int:
    print(f"\n=== {step_name} ===")
    print("Running:", " ".join(command))
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, env=env)
    if result.returncode != 0:
        print(f"Step failed: {step_name} (exit code {result.returncode})")
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full markdown update pipeline reliably.")
    parser.add_argument("--section", default="A", help="Section to rewrite (A, B, C... or ALL)")
    parser.add_argument("--start-num", type=int, help="Start note number (e.g., 30 for A30)")
    parser.add_argument("--end-num", type=int, help="End note number (e.g., 65 for A65)")
    parser.add_argument("--input-dir", default=str(REPO_ROOT), help="Vault root with OG markdown files")
    parser.add_argument("--notes-dir", default=str(DEFAULT_NOTES_DIR), help="Directory holding rewritten notes")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY)")
    parser.add_argument("--rate-limit", type=float, default=2.0, help="Rewrite delay between API calls")
    parser.add_argument("--min-new-studies", type=int, default=1, help="Rewrite gate based on new evidence")
    parser.add_argument(
        "--evidence-cache-max-age-days",
        type=int,
        default=7,
        help="Max age for cached PubMed evidence",
    )
    parser.add_argument(
        "--refresh-only-stale",
        action="store_true",
        help="Only refresh notes when rewritten output is older than --stale-days",
    )
    parser.add_argument("--stale-days", type=int, default=30, help="Staleness threshold for rewritten outputs")
    parser.add_argument("--audit-timeout", type=int, default=10, help="Citation audit HTTP timeout")
    parser.add_argument("--audit-workers", type=int, default=12, help="Citation audit worker count")
    parser.add_argument(
        "--audit-file-glob",
        default="rewritten_*.md",
        help="File selection glob used by citation audit",
    )
    parser.add_argument("--apply", action="store_true", help="Apply OG promotion after successful validation")
    parser.add_argument(
        "--build-content",
        action="store_true",
        help="Run web content build after pipeline succeeds",
    )
    parser.add_argument("--skip-rewrite", action="store_true", help="Skip rewrite phase")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue later steps even if an earlier step fails",
    )
    parser.add_argument(
        "--validate-interlinks",
        action="store_true",
        help="Run interlink_validator.py before promotion to catch broken / stub wikilinks",
    )
    parser.add_argument(
        "--interlink-fail-on",
        choices=["never", "broken", "any"],
        default="never",
        help="Treat interlink-validator findings as a pipeline failure",
    )
    parser.add_argument(
        "--staged-apply",
        action="store_true",
        help=(
            "Use staged_promotion.py (per-file confirm + date stamping + history) "
            "instead of the all-or-nothing promote_rewritten_to_og.py. "
            "Requires a TTY for interactive prompts; pair with --staged-auto-yes for headless."
        ),
    )
    parser.add_argument(
        "--staged-auto-yes",
        action="store_true",
        help="When using --staged-apply, accept every file that passes validation",
    )
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.0,
        help="PubMed relevance gate forwarded to the rewrite phase",
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.0,
        help="PubMed quality gate forwarded to the rewrite phase",
    )
    parser.add_argument(
        "--top-studies",
        type=int,
        default=5,
        help="Number of top-ranked studies forwarded to Claude per note",
    )
    parser.add_argument(
        "--lookback-years",
        type=int,
        default=4,
        help="PubMed publication-date lookback window forwarded to the rewrite phase",
    )
    parser.add_argument(
        "--exclude-name-prefix",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Forwarded to process_fitness_library.py (repeatable)",
    )
    parser.add_argument(
        "--resume-from-name",
        default=None,
        metavar="NAME",
        help="Forwarded to process_fitness_library.py",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notes_dir = Path(args.notes_dir)
    input_dir = Path(args.input_dir)

    notes_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_rewrite and not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return 2

    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    env = os.environ.copy()
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key

    failures = []

    if not args.skip_rewrite:
        if not api_key:
            print("API key required for rewrite phase (use --api-key or ANTHROPIC_API_KEY).")
            return 2

        rewrite_cmd = [
            sys.executable,
            str(PROCESS_SCRIPT),
            "--section",
            args.section,
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(notes_dir),
            "--rate-limit",
            str(args.rate_limit),
            "--min-new-studies",
            str(args.min_new_studies),
            "--evidence-cache-max-age-days",
            str(args.evidence_cache_max_age_days),
            "--stale-days",
            str(args.stale_days),
            "--min-relevance",
            str(args.min_relevance),
            "--min-quality",
            str(args.min_quality),
            "--top-studies",
            str(args.top_studies),
            "--lookback-years",
            str(args.lookback_years),
        ]
        if args.start_num is not None:
            rewrite_cmd.extend(["--start-num", str(args.start_num)])
        if args.end_num is not None:
            rewrite_cmd.extend(["--end-num", str(args.end_num)])
        if args.refresh_only_stale:
            rewrite_cmd.append("--refresh-only-stale")

        for prefix in args.exclude_name_prefix:
            rewrite_cmd.extend(["--exclude-name-prefix", prefix])
        if args.resume_from_name:
            rewrite_cmd.extend(["--resume-from-name", args.resume_from_name])

        rewrite_rc = run_cmd(rewrite_cmd, cwd=REPO_ROOT, env=env, step_name="Rewrite Notes")
        if rewrite_rc != 0:
            failures.append("rewrite")
            if not args.continue_on_error:
                return rewrite_rc

    audit_cmd = [
        sys.executable,
        str(AUDIT_SCRIPT),
        "--input-dir",
        str(notes_dir),
        "--output-dir",
        str(notes_dir),
        "--timeout",
        str(args.audit_timeout),
        "--workers",
        str(args.audit_workers),
        "--file-glob",
        args.audit_file_glob,
    ]
    audit_rc = run_cmd(audit_cmd, cwd=REPO_ROOT, env=env, step_name="Citation Audit")
    if audit_rc != 0:
        failures.append("audit")
        if not args.continue_on_error:
            return audit_rc

    doi_cmd = [
        sys.executable,
        str(DOI_FIX_SCRIPT),
        "--report",
        str(notes_dir / "citation_audit_report.json"),
        "--output",
        str(notes_dir / "citation_doi_fix_suggestions.json"),
    ]
    doi_rc = run_cmd(doi_cmd, cwd=REPO_ROOT, env=env, step_name="DOI Fix Suggestions")
    if doi_rc != 0:
        failures.append("doi_fix")
        if not args.continue_on_error:
            return doi_rc

    if args.validate_interlinks:
        interlink_cmd = [
            sys.executable,
            str(INTERLINK_SCRIPT),
            "--vault-root",
            str(REPO_ROOT),
            "--scope",
            "rewritten",
            "--output-dir",
            str(notes_dir),
            "--fail-on",
            args.interlink_fail_on,
        ]
        interlink_rc = run_cmd(
            interlink_cmd, cwd=REPO_ROOT, env=env, step_name="Interlink Validation"
        )
        if interlink_rc != 0:
            failures.append("interlink_validation")
            if not args.continue_on_error:
                return interlink_rc

    validate_cmd = [
        sys.executable,
        str(PROMOTE_SCRIPT),
        "--vault-root",
        str(REPO_ROOT),
        "--rewritten-dir",
        str(notes_dir),
    ]
    validate_rc = run_cmd(validate_cmd, cwd=REPO_ROOT, env=env, step_name="Promotion Validation (Dry Run)")
    if validate_rc != 0:
        failures.append("promotion_validation")
        if args.apply:
            print("Promotion apply is blocked because dry-run validation failed.")
        if not args.continue_on_error:
            return validate_rc

    if args.apply and validate_rc == 0:
        if args.staged_apply:
            staged_cmd = [
                sys.executable,
                str(STAGED_PROMOTE_SCRIPT),
                "--vault-root",
                str(REPO_ROOT),
                "--rewritten-dir",
                str(notes_dir),
            ]
            if args.staged_auto_yes:
                staged_cmd.append("--auto-yes")
            else:
                staged_cmd.append("--interactive")
            apply_rc = run_cmd(
                staged_cmd, cwd=REPO_ROOT, env=env, step_name="Promotion Apply (Staged)"
            )
        else:
            apply_cmd = validate_cmd + ["--apply"]
            apply_rc = run_cmd(apply_cmd, cwd=REPO_ROOT, env=env, step_name="Promotion Apply")
        if apply_rc != 0:
            failures.append("promotion_apply")
            if not args.continue_on_error:
                return apply_rc

    if args.build_content:
        build_cmd = ["npm", "run", "content:build"]
        build_rc = run_cmd(build_cmd, cwd=WEB_APP_DIR, env=env, step_name="Build Website Content")
        if build_rc != 0:
            failures.append("content_build")
            if not args.continue_on_error:
                return build_rc

    if failures:
        print(f"\nPipeline completed with failures in: {', '.join(failures)}")
        return 1

    print("\nPipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
