#!/usr/bin/env python3
"""Phase 1 tests for evidence refresh enhancements."""

import tempfile
import unittest
import time
import os
from pathlib import Path
from unittest.mock import patch

from organized_library.automation_tools.processing_scripts.process_fitness_library import (
    FitnessLibraryProcessor,
    NoteMetadata,
    StudyEvidence,
)


class TestProcessFitnessLibraryPhase1(unittest.TestCase):
    def setUp(self):
        self.processor = FitnessLibraryProcessor(api_key="test-key")

    def test_extract_search_terms(self):
        metadata = NoteMetadata(
            title="A20. Principle of Specificity (SAID)",
            note_id="A20",
            created_date="2024-01-01",
            file_path="/tmp/A20.md",
            section="A",
            word_count=250,
            has_links=True,
            links=["B1"],
        )
        terms = self.processor._extract_search_terms(metadata)
        self.assertTrue(any("Specificity" in term for term in terms))
        self.assertLessEqual(len(terms), 3)

    def test_extract_pub_date_year(self):
        self.assertEqual(self.processor._extract_pub_date_year("2025 Jan 10"), "2025")
        self.assertEqual(self.processor._extract_pub_date_year({"Year": "2024"}), "2024")
        self.assertEqual(self.processor._extract_pub_date_year("unknown"), "Unknown")

    def test_processing_report_includes_evidence_fields(self):
        results = {
            "processed": 1,
            "failed": 0,
            "skipped": 0,
            "details": [
                {
                    "file": "A20.md",
                    "status": "success",
                    "new_studies_found": 4,
                    "studies_used_in_revision": 3,
                    "major_changes_made": "Evidence-aware rewrite completed",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir)
            self.processor.generate_processing_report(results, "A", out)
            report = (out / "section_A_report.md").read_text(encoding="utf-8")
            self.assertIn("new_studies_found=4", report)
            self.assertIn("studies_used_in_revision=3", report)

    def test_process_section_skips_when_no_new_evidence(self):
        note_content = (
            "# A20. Principle of Specificity (SAID)\n"
            "**ID:** A20\n"
            "**Created:** 2024-01-01\n\n"
            + "word " * 130
            + "\n[[B2. Protein Requirements]]\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_dir = Path(tmp_dir) / "in"
            out_dir = Path(tmp_dir) / "out"
            in_dir.mkdir(parents=True, exist_ok=True)
            out_dir.mkdir(parents=True, exist_ok=True)
            (in_dir / "A20. Principle of Specificity (SAID).md").write_text(note_content, encoding="utf-8")

            with patch.object(self.processor, "discover_recent_evidence", return_value=[]):
                results = self.processor.process_section(
                    in_dir,
                    out_dir,
                    "A",
                    20,
                    20,
                    min_new_studies=1,
                    evidence_cache_max_age_days=7,
                )

            self.assertEqual(results["processed"], 0)
            self.assertEqual(results["skipped"], 1)
            self.assertIn("unchanged_reason", results["details"][0])

    def test_rank_studies_prefers_meta_analysis(self):
        studies = [
            StudyEvidence("Obs", "2026", None, "1", "J", "Observational", ""),
            StudyEvidence("RCT", "2024", None, "2", "J", "RCT", ""),
            StudyEvidence("MA", "2023", None, "3", "J", "Meta-analysis", ""),
        ]
        ranked = self.processor._rank_studies(studies, top_n=3)
        self.assertEqual(ranked[0].title, "MA")

    def test_describe_major_changes_detects_deltas(self):
        original = "Protocol should be light.\nDOI: https://doi.org/10.1000/old\n"
        rewritten = (
            "Protocol should be moderate intensity 3x/week.\n"
            "DOI: https://doi.org/10.1000/new\n"
            "PMID: https://pubmed.ncbi.nlm.nih.gov/12345\n"
        )
        summary = self.processor._describe_major_changes(original, rewritten, [])
        self.assertGreaterEqual(summary["citation_delta"], 1)
        self.assertGreater(summary["recommendation_delta"], 0)

    def test_refresh_only_stale_skips_recent_file(self):
        note_content = (
            "# A20. Principle of Specificity (SAID)\n"
            "**ID:** A20\n"
            "**Created:** 2024-01-01\n\n"
            + "word " * 130
            + "\n[[B2. Protein Requirements]]\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_dir = Path(tmp_dir) / "in"
            out_dir = Path(tmp_dir) / "out"
            in_dir.mkdir(parents=True, exist_ok=True)
            out_dir.mkdir(parents=True, exist_ok=True)
            note_path = in_dir / "A20. Principle of Specificity (SAID).md"
            note_path.write_text(note_content, encoding="utf-8")

            rewritten = out_dir / "rewritten_A20. Principle of Specificity (SAID).md"
            rewritten.write_text("existing", encoding="utf-8")
            now = time.time()
            os.utime(rewritten, (now, now))

            with patch.object(self.processor, "discover_recent_evidence", return_value=[]):
                results = self.processor.process_section(
                    in_dir,
                    out_dir,
                    "A",
                    20,
                    20,
                    min_new_studies=1,
                    evidence_cache_max_age_days=7,
                    refresh_only_stale=True,
                    stale_days=30,
                )
            self.assertEqual(results["processed"], 0)
            self.assertEqual(results["skipped"], 1)
            self.assertIn("stale-note policy", results["details"][0].get("unchanged_reason", ""))


if __name__ == "__main__":
    unittest.main()
