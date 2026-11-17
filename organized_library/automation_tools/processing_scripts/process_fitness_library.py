#!/usr/bin/env python3
"""
Fitness Library Automation System
Restructures and expands fitness knowledge base using Claude API
Preserves Obsidian linking structure while improving accessibility
"""

import os
import re
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import anthropic
from datetime import datetime
import argparse
import logging
import requests

TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.append(str(TOOLS_ROOT))

from utility_scripts.note_metadata import read_metadata

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fitness_library_processing.log')
    ]
)
logger = logging.getLogger(__name__)

# Vault-root markdown that should never go through the rewriter (reports, placeholders).
_AUXILIARY_ROOT_MARKDOWN = frozenset({".md", "README.md", "fitlib.md"})


def _is_auxiliary_root_note(path: Path) -> bool:
    name = path.name
    if name in _AUXILIARY_ROOT_MARKDOWN:
        return True
    if name.startswith("FINAL_"):
        return True
    return False


@dataclass
class NoteMetadata:
    """Store metadata about a fitness note"""
    title: str
    note_id: str
    created_date: str
    file_path: str
    section: str
    word_count: int
    has_links: bool
    links: List[str]


@dataclass
class StudyEvidence:
    """Structured evidence item used for note refresh."""
    title: str
    year: str
    doi: Optional[str]
    pmid: Optional[str]
    journal: str
    study_type: str
    summary: str
    relevance_score: float = 0.0
    quality_score: float = 0.0
    composite_score: float = 0.0

class FitnessLibraryProcessor:
    """Main class for processing fitness library notes"""
    
    def __init__(self, api_key: str, rate_limit_delay: float = 2.0):
        """Initialize with Claude API key and rate limiting"""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.rate_limit_delay = rate_limit_delay
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.current_year = datetime.now().year
        tools_root = Path(__file__).resolve().parents[1]
        self.evidence_cache_dir = tools_root / ".cache"
        self.evidence_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load the SOP template
        self.rewrite_template = self._load_rewrite_template()
        
    def _load_rewrite_template(self) -> str:
        """Load the standardized rewrite template from SOP"""
        return """You are rewriting fitness/exercise science notes for better accessibility while maintaining scientific rigor. This is part of an interconnected Obsidian knowledge base.

CRITICAL REQUIREMENTS:
1. NEVER change the note title - this breaks links across the entire library
2. PRESERVE all existing [[links]] exactly as written - do not modify anything inside [[ ]]
2a. If an existing link target ends with `.md`, remove only the `.md` suffix (keep target, anchor, and alias unchanged)
3. MAINTAIN all scientific accuracy and citations
4. ADD practical applications if missing
5. ENSURE all key claims are backed by research citations
6. Use the exact structure provided below

STANDARD NOTE STRUCTURE:
```markdown
---
id: [Keep original ID exactly as is]
created: [Original date]
updated: [Current date]
section: [Section letter/roman numeral]
tags: [optional, comma-separated topical tags]
---
### [Original Title - NEVER CHANGE]

## Quick Takeaway
[Single sentence bottom line - what users need to know immediately]

## Key Points
- [3-5 factual bullet points explaining core concepts]
- [No performance percentages or claims like "increases by X%"]
- [Focus on what happens, not how much improvement]
- [Example: "Type I fibers are fatigue resistant and recruited first" not "Type I training improves endurance by 20%"]

## Deep Dive
[Your original detailed content - reorganized with subheadings]
[Preserve ALL scientific accuracy and mechanisms]
[Use clear subheadings for complex topics]
[Include inline citations for key claims]

### [Subheading as needed]
[Detailed explanations with citations]

## Research Evidence
[MANDATORY: Use the enhanced format below for ALL citations]
[CRITICAL: Every citation MUST have a working DOI or PMID link - no exceptions]

**Author et al. (Year).** Title. *Journal*, Volume(Issue), Pages. DOI: https://doi.org/[DOI]
- Key finding: [Specific measurable result or main conclusion]
- Study type: [RCT/Meta-analysis/Systematic review/Observational/Case study]  
- Evidence quality: [High/Medium/Low] ([Brief quality descriptor])

**Alternative format with PMID:**
**Author et al. (Year).** Title. *Journal*, Volume(Issue), Pages. PMID: https://pubmed.ncbi.nlm.nih.gov/[PMID]
- Key finding: [Specific measurable result or main conclusion]
- Study type: [RCT/Meta-analysis/Systematic review/Observational/Case study]
- Evidence quality: [High/Medium/Low] ([Brief quality descriptor])

[REQUIREMENTS:]
- Include ONLY citations with working DOI or PMID links
- Verify links work before including them
- Focus on 3-5 highest quality, most relevant studies
- Remove any citations that cannot be verified with working links

## Practical Applications
[How to actually implement this - ADD if missing]
[Specific examples, numbers, protocols]
[Real-world scenarios]

## Common Mistakes
⚠️ [What people typically get wrong]
⚠️ [Misconceptions to avoid]
⚠️ [Implementation errors]

## Related Concepts
[PRESERVE ALL EXISTING LINKS EXACTLY]
[Add contextual phrases around links where helpful]
[Example: "adequate protein intake [[B2. Protein Requirements]]" instead of just "[[B2. Protein Requirements]]"]

## Update Log
- [Date]: [What changed and why]
```

LINKING PRESERVATION RULES:
- Keep all [[Note Name]] links exactly as they appear
- Canonicalize malformed links by stripping a trailing `.md` from the target only
- You can add descriptive text around links: "adequate protein intake [[B2. Protein Requirements]]"
- Never modify what's inside the [[ ]] brackets
- Never change link destinations

RESEARCH CITATION RULES:
- CRITICAL: Every citation MUST have a working DOI or PMID link - NO EXCEPTIONS
- Use the ENHANCED RESEARCH EVIDENCE FORMAT with mandatory links
- Format: **Author et al. (Year).** Title. *Journal*, Volume(Issue), Pages. DOI: https://doi.org/[DOI]
- Follow each citation with:
  - Key finding: [Specific measurable result]
  - Study type: [RCT/Meta-analysis/Systematic review/Observational/Case study]
  - Evidence quality: [High/Medium/Low] ([Brief quality descriptor])
- VERIFY all DOI/PMID links work before including them
- If you cannot find working links, do NOT include the citation
- Better to have 2-3 citations with working links than 5 without links
- Focus on highest quality studies with verifiable sources
- Do NOT make up or guess DOI/PMID numbers

Here's the note to rewrite:

"""

    def extract_note_metadata(self, file_path: Path) -> Optional[NoteMetadata]:
        """Extract metadata from a markdown note"""
        try:
            logger.debug(f"Attempting to read file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title (first heading)
            title_match = re.search(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else file_path.stem
            logger.debug(f"Extracted title: {title}")
            
            metadata = read_metadata(content)

            # Extract ID
            note_id = metadata.note_id or "NO-ID"
            logger.debug(f"Extracted ID: {note_id}")
            
            # Extract creation date
            created_date = metadata.created or "Unknown"
            logger.debug(f"Extracted date: {created_date}")
            
            # Extract section from filename or ID
            section = (
                metadata.section
                or (file_path.stem[0] if file_path.stem and file_path.stem[0].isalpha() else "Unknown")
            )
            logger.debug(f"Extracted section: {section}")
            
            # Count words
            word_count = len(content.split())
            logger.debug(f"Word count: {word_count}")
            
            # Find all internal links
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            has_links = len(links) > 0
            logger.debug(f"Found {len(links)} links")
            
            return NoteMetadata(
                title=title,
                note_id=note_id,
                created_date=created_date,
                file_path=str(file_path),
                section=section,
                word_count=word_count,
                has_links=has_links,
                links=links
            )
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}", exc_info=True)
            return None

    def should_process_note(self, metadata: NoteMetadata, min_words: int = 100) -> Tuple[bool, str]:
        """Determine if a note should be processed"""
        logger.debug(f"Checking if should process note: {metadata.file_path}")
        
        # Skip if too short
        if metadata.word_count < min_words:
            logger.debug(f"Note too short: {metadata.word_count} words")
            return False, f"Too short ({metadata.word_count} words)"
        
        # Skip if it's just a section header
        if metadata.word_count < 200 and not metadata.has_links:
            logger.debug("Note appears to be section header only")
            return False, "Appears to be section header only"
        
        # Skip if title suggests it's a directory listing
        if any(keyword in metadata.title.lower() for keyword in ['section', 'appendix', 'overview']):
            if metadata.word_count < 300:
                logger.debug("Note appears to be directory/overview page")
                return False, "Appears to be directory/overview page"
        
        logger.debug("Note passed all checks, ready for processing")
        return True, "Ready for processing"

    def validate_research_citations(self, content: str) -> Tuple[bool, List[str]]:
        """Validate research citations and ensure they have proper DOIs or PMIDs with valid links"""
        issues = []
        
        # Look for DOI patterns
        doi_pattern = r'DOI:\s*https://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'
        dois = re.findall(doi_pattern, content, re.IGNORECASE)
        
        # Look for PMID patterns  
        pmid_pattern = r'PMID:\s*https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)'
        pmids = re.findall(pmid_pattern, content, re.IGNORECASE)
        
        # Look for research citations (Author et al. pattern)
        citation_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+et\s+al\.)?)\s*\(\d{4}\)'
        citations = re.findall(citation_pattern, content)
        
        # Check if we have citations but no DOIs or PMIDs
        if citations and not dois and not pmids:
            issues.append("Research citations found but no DOI or PMID links provided")
        
        # Validate DOI links
        for doi in dois:
            if not self._validate_doi(doi):
                issues.append(f"Invalid or broken DOI: {doi}")
        
        # Validate PMID links
        for pmid in pmids:
            if not self._validate_pmid(pmid):
                issues.append(f"Invalid or broken PMID: {pmid}")
        
        return len(issues) == 0, issues

    def _validate_doi(self, doi: str) -> bool:
        """Validate a DOI by checking if it resolves to a valid URL"""
        try:
            url = f"https://doi.org/{doi}"
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _validate_pmid(self, pmid: str) -> bool:
        """Validate a PMID by checking if it resolves to a valid PubMed URL"""
        try:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.status_code == 200
        except:
            return False

    SECTION_DOMAIN_HINTS = {
        "A": ["exercise physiology", "training adaptation"],
        "B": ["resistance training", "strength training"],
        "C": ["sports nutrition", "dietary intervention"],
        "D": ["cardiorespiratory training", "aerobic adaptation"],
        "E": ["endurance training", "interval training"],
        "F": ["performance testing", "fitness assessment"],
        "G": ["special populations", "clinical exercise"],
        "I": ["exercise endocrinology", "training stress"],
        "J": ["wearable technology", "sport technology"],
        "K": ["elite athlete performance", "high performance training"],
        "M": ["exercise recovery", "sleep recovery"],
        "N": ["long term athlete development", "youth training"],
        "O": ["integrated training", "concurrent training"],
        "P": ["exercise ethics", "doping policy"],
        "X": ["sport specific training", "tactical conditioning"],
    }

    STOPWORDS = {
        "the", "and", "with", "from", "into", "this", "that", "these", "those",
        "a", "an", "of", "for", "to", "in", "on", "by", "or", "is", "are",
        "training", "exercise",
    }

    def _tokenize_title(self, title: str) -> Set[str]:
        clean = re.sub(r"[^a-zA-Z0-9\s\-]", " ", title.lower())
        return {tok for tok in clean.split() if len(tok) > 2 and tok not in self.STOPWORDS}

    def _extract_search_terms(self, metadata: NoteMetadata) -> List[str]:
        """Build focused PubMed search terms from note metadata."""
        clean_title = re.sub(r"^[A-Z]+[\dIVX\-]*\.\s*", "", metadata.title).strip()
        clean_title = re.sub(r"\s*\([^)]*\)", "", clean_title).strip()
        base_terms: List[str] = []
        if clean_title:
            base_terms.append(clean_title)

        domain_hints = self.SECTION_DOMAIN_HINTS.get(metadata.section.upper(), [])
        base_terms.extend(domain_hints[:2])

        lower_title = clean_title.lower()
        keyword_map = {
            "nutrition": "sports nutrition",
            "protein": "protein intake athletes",
            "carbohydrate": "carbohydrate periodization",
            "recovery": "exercise recovery",
            "sleep": "athlete sleep",
            "hormone": "exercise endocrinology",
            "muscle": "skeletal muscle adaptation",
            "cardio": "aerobic exercise",
            "endurance": "endurance performance",
            "strength": "strength training",
            "hypertrophy": "muscle hypertrophy",
            "biomechanic": "biomechanics",
            "injury": "injury prevention",
            "vo2": "vo2max training",
            "lactate": "lactate threshold",
        }
        for needle, term in keyword_map.items():
            if needle in lower_title and term not in base_terms:
                base_terms.append(term)

        deduped: List[str] = []
        for term in base_terms:
            if term and term not in deduped:
                deduped.append(term)
        return deduped[:5]

    def _cache_path_for_note(self, metadata: NoteMetadata) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", Path(metadata.file_path).stem)
        return self.evidence_cache_dir / f"{safe_name}.json"

    def _load_cached_evidence(self, metadata: NoteMetadata, max_age_days: int = 7) -> Optional[List[StudyEvidence]]:
        cache_path = self._cache_path_for_note(metadata)
        if not cache_path.exists():
            return None
        age_seconds = time.time() - cache_path.stat().st_mtime
        if age_seconds > max_age_days * 86400:
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            studies = [StudyEvidence(**item) for item in payload.get("studies", [])]
            if studies:
                logger.debug(f"Using cached evidence for {metadata.title}")
                return studies
        except Exception as exc:
            logger.warning(f"Failed to parse evidence cache for {metadata.title}: {exc}")
        return None

    def _save_cached_evidence(self, metadata: NoteMetadata, studies: List[StudyEvidence]):
        cache_path = self._cache_path_for_note(metadata)
        payload = {
            "note_title": metadata.title,
            "cached_at": datetime.now().isoformat(),
            "studies": [study.__dict__ for study in studies],
        }
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def _infer_study_type(self, publication_types: List[str]) -> str:
        text = " ".join(publication_types).lower()
        if "meta-analysis" in text:
            return "Meta-analysis"
        if "systematic review" in text or "review" in text:
            return "Systematic review"
        if "randomized controlled trial" in text:
            return "RCT"
        if "clinical trial" in text:
            return "Clinical trial"
        return "Observational"

    def _study_priority(self, study: StudyEvidence) -> int:
        """Rank studies so higher-quality designs are prioritized."""
        study_type = (study.study_type or "").lower()
        if "meta-analysis" in study_type:
            return 5
        if "systematic review" in study_type:
            return 4
        if "rct" in study_type or "randomized" in study_type:
            return 3
        if "clinical trial" in study_type:
            return 2
        return 1

    HIGH_IMPACT_JOURNAL_HINTS = (
        "lancet", "nejm", "new england journal", "nature", "jama",
        "british journal of sports medicine", "bjsm",
        "medicine and science in sports", "med sci sports exerc",
        "sports medicine", "journal of strength and conditioning",
        "international journal of sport nutrition",
        "european journal of sport science",
        "journal of applied physiology",
        "european journal of applied physiology",
        "frontiers in physiology", "nutrients",
        "american journal of clinical nutrition",
    )

    def _journal_score(self, journal: str) -> float:
        if not journal:
            return 0.0
        lower = journal.lower()
        if any(hint in lower for hint in self.HIGH_IMPACT_JOURNAL_HINTS):
            return 1.0
        if "review" in lower:
            return 0.6
        if "journal" in lower or "international" in lower:
            return 0.4
        return 0.2

    def _recency_score(self, year_str: str) -> float:
        try:
            year = int(year_str)
        except (TypeError, ValueError):
            return 0.0
        gap = max(self.current_year - year, 0)
        if gap <= 1:
            return 1.0
        if gap <= 3:
            return 0.85
        if gap <= 5:
            return 0.65
        if gap <= 8:
            return 0.4
        return 0.15

    def _relevance_score(self, study_title: str, note_tokens: Set[str]) -> float:
        if not note_tokens:
            return 0.0
        study_tokens = self._tokenize_title(study_title)
        if not study_tokens:
            return 0.0
        overlap = note_tokens & study_tokens
        union = note_tokens | study_tokens
        return len(overlap) / len(union)

    def _quality_score(self, study: StudyEvidence) -> float:
        """0-1 score combining design strength + journal weight."""
        priority = self._study_priority(study)
        type_score = (priority - 1) / 4  # 0..1
        return round(0.6 * type_score + 0.4 * self._journal_score(study.journal), 4)

    def _score_studies(
        self,
        studies: List[StudyEvidence],
        note_tokens: Set[str],
    ) -> List[StudyEvidence]:
        for study in studies:
            study.relevance_score = round(self._relevance_score(study.title, note_tokens), 4)
            study.quality_score = self._quality_score(study)
            recency = self._recency_score(study.year)
            study.composite_score = round(
                0.5 * study.quality_score
                + 0.3 * study.relevance_score
                + 0.2 * recency,
                4,
            )
        return studies

    def _rank_studies(
        self,
        studies: List[StudyEvidence],
        top_n: int = 5,
        min_relevance: float = 0.0,
        min_quality: float = 0.0,
    ) -> List[StudyEvidence]:
        """Sort by composite score, gate on minimum relevance/quality, keep top_n."""
        filtered = [
            s for s in studies
            if s.relevance_score >= min_relevance and s.quality_score >= min_quality
        ]
        if not filtered:
            filtered = studies  # fall back so we don't starve the rewrite
        ranked = sorted(
            filtered,
            key=lambda s: (s.composite_score, s.quality_score, s.relevance_score),
            reverse=True,
        )
        return ranked[:top_n]

    def _extract_pub_date_year(self, pub_date) -> str:
        if isinstance(pub_date, dict) and pub_date.get("Year"):
            return str(pub_date.get("Year"))
        if isinstance(pub_date, str):
            match = re.search(r"\b(19|20)\d{2}\b", pub_date)
            if match:
                return match.group(0)
        return "Unknown"

    def _build_pubmed_query(self, search_terms: List[str], lookback_years: int) -> str:
        """Build a PubMed query that prioritises strong designs in humans."""
        quoted_terms = [f"\"{term}\"" if " " in term else term for term in search_terms]
        topic_clause = "(" + " OR ".join(quoted_terms) + ")"
        design_clause = (
            "(\"Randomized Controlled Trial\"[Publication Type] OR "
            "\"Meta-Analysis\"[Publication Type] OR "
            "\"Systematic Review\"[Publication Type] OR "
            "\"Clinical Trial\"[Publication Type] OR "
            "\"Review\"[Publication Type])"
        )
        species_clause = "humans[mh]"
        date_clause = f"{self.current_year - lookback_years}:{self.current_year}[pdat]"
        return f"{topic_clause} AND {design_clause} AND {species_clause} AND {date_clause}"

    def discover_recent_evidence(
        self,
        metadata: NoteMetadata,
        max_results: int = 12,
        cache_max_age_days: int = 7,
        min_relevance: float = 0.0,
        min_quality: float = 0.0,
        top_n: int = 5,
        lookback_years: int = 4,
    ) -> List[StudyEvidence]:
        """Discover and rank PubMed studies relevant to this note."""
        cached = self._load_cached_evidence(metadata, max_age_days=cache_max_age_days)
        if cached is not None:
            return cached

        search_terms = self._extract_search_terms(metadata)
        if not search_terms:
            return []

        primary_query = self._build_pubmed_query(search_terms, lookback_years)
        # Looser fallback if the strict query returns nothing.
        loose_query = (
            "(" + " OR ".join(search_terms) + f") AND humans[mh] AND "
            f"{self.current_year - lookback_years}:{self.current_year}[pdat]"
        )

        note_tokens = self._tokenize_title(metadata.title)

        try:
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            id_list: List[str] = []
            for query in (primary_query, loose_query):
                search_params = {
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": str(max_results),
                    "sort": "relevance",
                }
                search_res = requests.get(search_url, params=search_params, timeout=15)
                search_res.raise_for_status()
                id_list = search_res.json().get("esearchresult", {}).get("idlist", [])
                if id_list:
                    logger.debug(
                        "PubMed query returned %d ids for %s", len(id_list), metadata.title
                    )
                    break

            if not id_list:
                return []

            summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            summary_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
            }
            summary_res = requests.get(summary_url, params=summary_params, timeout=15)
            summary_res.raise_for_status()
            result = summary_res.json().get("result", {})
            studies: List[StudyEvidence] = []

            for pmid in id_list:
                item = result.get(pmid, {})
                article_ids = item.get("articleids", [])
                doi = None
                for article_id in article_ids:
                    if article_id.get("idtype") == "doi":
                        doi = article_id.get("value")
                        break
                study = StudyEvidence(
                    title=item.get("title", "Untitled"),
                    year=self._extract_pub_date_year(item.get("pubdate", {})),
                    doi=doi,
                    pmid=pmid,
                    journal=item.get("fulljournalname") or item.get("source", "Unknown Journal"),
                    study_type=self._infer_study_type(item.get("pubtype", [])),
                    summary="Recent study surfaced for evidence refresh.",
                )
                studies.append(study)

            self._score_studies(studies, note_tokens)
            ranked = self._rank_studies(
                studies,
                top_n=top_n,
                min_relevance=min_relevance,
                min_quality=min_quality,
            )
            self._save_cached_evidence(metadata, ranked)
            return ranked
        except Exception as exc:
            logger.warning(f"Evidence discovery failed for {metadata.title}: {exc}")
            return []

    def _build_evidence_brief(self, studies: List[StudyEvidence]) -> str:
        """Create structured evidence context for Claude (highest score first)."""
        if not studies:
            return "No recent studies were found from PubMed in this run."
        lines = [
            "Recent evidence packet (sorted by composite score). Prefer the top entries; "
            "skip any whose quality_score < 0.4 or relevance_score < 0.05 unless you have "
            "no better source."
        ]
        for idx, study in enumerate(studies, start=1):
            ref_link = (
                f"DOI: https://doi.org/{study.doi}" if study.doi
                else f"PMID: https://pubmed.ncbi.nlm.nih.gov/{study.pmid}"
            )
            lines.append(
                f"{idx}. {study.title} ({study.year}) | {study.journal} | "
                f"{study.study_type} | quality={study.quality_score:.2f} "
                f"relevance={study.relevance_score:.2f} composite={study.composite_score:.2f} "
                f"| {ref_link}"
            )
        return "\n".join(lines)

    def _extract_citation_tokens(self, content: str) -> Set[str]:
        doi_matches = re.findall(r"https://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", content, re.IGNORECASE)
        pmid_matches = re.findall(r"https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", content, re.IGNORECASE)
        tokens = {f"doi:{match.lower()}" for match in doi_matches}
        tokens.update({f"pmid:{match}" for match in pmid_matches})
        return tokens

    def _extract_recommendation_signals(self, content: str) -> Set[str]:
        """Extract recommendation-like statements to compare guidance changes."""
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        signals: Set[str] = set()
        trigger_words = ("should", "recommend", "protocol", "dosage", "intensity", "frequency", "duration")
        for line in lines:
            lower = line.lower()
            if line.startswith("-") or any(word in lower for word in trigger_words):
                normalized = re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s%-]", "", lower)).strip()
                if len(normalized) > 20:
                    signals.add(normalized[:200])
        return signals

    def _describe_major_changes(self, original: str, rewritten: str, studies: List[StudyEvidence]) -> Dict[str, object]:
        """Compare original vs rewritten and summarize substantive changes."""
        original_citations = self._extract_citation_tokens(original)
        rewritten_citations = self._extract_citation_tokens(rewritten)
        citations_added = sorted(rewritten_citations - original_citations)

        original_recs = self._extract_recommendation_signals(original)
        rewritten_recs = self._extract_recommendation_signals(rewritten)
        recommendation_changes = len(original_recs.symmetric_difference(rewritten_recs))

        major_parts: List[str] = []
        if citations_added:
            major_parts.append(f"Added {len(citations_added)} new citation links")
        if recommendation_changes > 0:
            major_parts.append(f"Recommendation signals changed: {recommendation_changes}")
        if studies and not major_parts:
            major_parts.append("Evidence packet reviewed; only minor phrasing updates")
        if not major_parts:
            major_parts.append("No substantive evidence-driven change detected")

        return {
            "citation_delta": len(citations_added),
            "recommendation_delta": recommendation_changes,
            "major_changes_made": "; ".join(major_parts),
            "new_citation_tokens": citations_added[:5],
        }

    def _is_stale_for_refresh(self, file_path: Path, output_dir: Path, stale_days: int) -> bool:
        """Treat note as stale if rewritten output missing or older than threshold."""
        rewritten_file = output_dir / f"rewritten_{file_path.name}"
        if not rewritten_file.exists():
            return True
        age_days = (time.time() - rewritten_file.stat().st_mtime) / 86400
        return age_days >= stale_days

    def rewrite_note_with_claude(self, content: str, evidence_brief: str) -> Optional[str]:
        """Use Claude to rewrite a note while preserving structure"""
        try:
            # Define the messages for the API call
            messages = [
                {
                    "role": "user",
                    "content": (
                        self.rewrite_template
                        + content
                        + "\n\nIMPORTANT EVIDENCE REFRESH INSTRUCTION:\n"
                        + evidence_brief
                        + "\n\nIf the evidence changes recommendations, update the note accordingly."
                    ),
                }
            ]

            # Call Claude API with the Messages API format
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514", # Using the model you specified earlier
                max_tokens=4000,
                temperature=0.7,
                system="You are a fitness science expert helping to improve the accessibility and clarity of exercise science notes while maintaining scientific accuracy.",
                messages=messages
            )

            # Extract the rewritten content from the Messages API response
            rewritten_content = response.content[0].text

            # Add rate limiting delay
            time.sleep(self.rate_limit_delay)

            return rewritten_content

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            return None

    def validate_rewritten_note(self, original: str, rewritten: str) -> Tuple[bool, List[str]]:
        """Validate that rewritten note preserves links and structure"""
        issues = []
        
        # Extract original links
        original_links = set(re.findall(r'\[\[([^\]]+)\]\]', original))
        rewritten_links = set(re.findall(r'\[\[([^\]]+)\]\]', rewritten))
        
        # Check for missing links
        missing_links = original_links - rewritten_links
        if missing_links:
            issues.append(f"Missing links: {missing_links}")
        
        # Check for required sections
        required_sections = ["Quick Takeaway", "Key Points", "Deep Dive"]
        for section in required_sections:
            if section not in rewritten:
                issues.append(f"Missing required section: {section}")
        
        # Check that title wasn't changed (simple check)
        original_title = re.search(r'^#{1,3}\s+(.+)$', original, re.MULTILINE)
        rewritten_title = re.search(r'^#{1,3}\s+(.+)$', rewritten, re.MULTILINE)
        
        if original_title and rewritten_title:
            if original_title.group(1).strip() != rewritten_title.group(1).strip():
                issues.append("Title was modified")
        
        return len(issues) == 0, issues

    def process_section(
        self,
        input_dir: Path,
        output_dir: Path,
        section: str,
        start_num: int = 1,
        end_num: int = 100,
        min_new_studies: int = 1,
        evidence_cache_max_age_days: int = 7,
        refresh_only_stale: bool = False,
        stale_days: int = 30,
        min_relevance: float = 0.0,
        min_quality: float = 0.0,
        top_studies: int = 5,
        lookback_years: int = 4,
        exclude_name_prefixes: Optional[List[str]] = None,
        resume_from_name: Optional[str] = None,
    ) -> Dict:
        """Process all notes in a specific section (e.g., 'A', 'B', 'C')"""
        
        logger.info(f"Processing Section {section.upper()}")
        
        # Find all files in the section
        if section == "ALL":
            pattern = "*.md"
        else:
            # Handle both formats: "X11. Sprinting.md" and "X11*.md"
            pattern = f"{section}*.md"
        
        files = list(input_dir.glob(pattern))
        
        # Filter files by number range if start_num and end_num are provided (single-letter sections).
        if section != "ALL" and start_num is not None and end_num is not None:
            filtered_files = []
            for file_path in files:
                # Extract the number from the filename (e.g., A30. Biomechanics.md -> 30)
                match = re.match(rf"{re.escape(section)}(\d+)[\.\s].*\.md", file_path.name)
                if match:
                    file_num = int(match.group(1))
                    if start_num <= file_num <= end_num:
                        filtered_files.append(file_path)
            files = filtered_files

        files = sorted(files)

        if exclude_name_prefixes:
            prefixes = tuple(exclude_name_prefixes)
            before_ct = len(files)
            files = [f for f in files if not any(f.name.startswith(p) for p in prefixes)]
            logger.info(
                "After --exclude-name-prefix: %s files (%s dropped)",
                len(files),
                before_ct - len(files),
            )

        if resume_from_name:
            before_ct = len(files)
            files = [f for f in files if f.name >= resume_from_name]
            logger.info(
                "After --resume-from-name (>=%r): %s files (%s dropped)",
                resume_from_name,
                len(files),
                before_ct - len(files),
            )

        if not files:
            logger.warning(f"No files found for section {section}")
            return {"processed": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"Found {len(files)} files for section {section}")
        
        results = {"processed": 0, "failed": 0, "skipped": 0, "details": []}
        
        for file_path in files:
            # Skip files in processed_notes directory
            if "processed_notes" in str(file_path):
                continue

            if _is_auxiliary_root_note(file_path):
                logger.info(f"  Skipping auxiliary/root file: {file_path.name}")
                results["skipped"] += 1
                results["details"].append(
                    {"file": file_path.name, "status": "skipped", "reason": "Auxiliary markdown (not a topic note)"}
                )
                continue
                
            logger.info(f"Processing: {file_path.name}")
            
            # Extract metadata
            metadata = self.extract_note_metadata(file_path)
            if not metadata:
                results["failed"] += 1
                continue
            
            # Check if should process
            should_process, reason = self.should_process_note(metadata)
            if not should_process:
                logger.info(f"  Skipping: {reason}")
                results["skipped"] += 1
                results["details"].append({"file": file_path.name, "status": "skipped", "reason": reason})
                continue
            
            try:
                if refresh_only_stale and not self._is_stale_for_refresh(file_path, output_dir, stale_days):
                    results["skipped"] += 1
                    results["details"].append(
                        {
                            "file": file_path.name,
                            "status": "skipped",
                            "reason": f"Recently refreshed (<{stale_days} days)",
                            "unchanged_reason": "Skipped by stale-note policy",
                        }
                    )
                    continue

                # Read original content
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()

                studies = self.discover_recent_evidence(
                    metadata,
                    cache_max_age_days=evidence_cache_max_age_days,
                    min_relevance=min_relevance,
                    min_quality=min_quality,
                    top_n=top_studies,
                    lookback_years=lookback_years,
                )
                evidence_brief = self._build_evidence_brief(studies)

                if len(studies) < min_new_studies:
                    logger.info(f"  Skipping rewrite for {file_path.name}: insufficient new evidence")
                    results["skipped"] += 1
                    results["details"].append(
                        {
                            "file": file_path.name,
                            "status": "skipped",
                            "reason": f"Only {len(studies)} studies found (minimum={min_new_studies})",
                            "new_studies_found": len(studies),
                            "studies_used_in_revision": 0,
                            "unchanged_reason": "No meaningful new evidence available",
                        }
                    )
                    continue

                # Rewrite with Claude
                rewritten_content = self.rewrite_note_with_claude(original_content, evidence_brief)
                
                if not rewritten_content:
                    logger.error(f"  Failed to rewrite {file_path.name}")
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "file": file_path.name,
                            "status": "failed",
                            "reason": "Claude API error",
                            "new_studies_found": len(studies),
                            "studies_used_in_revision": 0,
                        }
                    )
                    continue
                
                # Validate the rewrite
                is_valid, validation_issues = self.validate_rewritten_note(original_content, rewritten_content)
                
                # Also validate research citations
                citations_valid, citation_issues = self.validate_research_citations(rewritten_content)
                
                if not is_valid or not citations_valid:
                    all_issues = validation_issues + citation_issues
                    logger.error(f"  Validation failed for {file_path.name}: {all_issues}")
                    
                    # Try to fix structural issues
                    if "Missing links" in str(validation_issues):
                        missing_links = re.findall(r"'([^']+)'", str(validation_issues))
                        for link in missing_links:
                            rewritten_content += f"\n[[{link}]]"
                    
                    if "Title was modified" in str(validation_issues):
                        original_title = re.search(r'^#{1,3}\s+(.+)$', original_content, re.MULTILINE)
                        if original_title:
                            rewritten_content = re.sub(r'^#{1,3}\s+.+$', original_title.group(0), rewritten_content, flags=re.MULTILINE)
                    
                    # If citation issues persist, flag for manual review
                    if not citations_valid:
                        logger.warning(f"  Citation validation failed for {file_path.name}: {citation_issues}")
                        # Still save the file but add a warning comment
                        rewritten_content += f"\n\n<!-- VALIDATION WARNING: {'; '.join(citation_issues)} -->"
                
                # Save rewritten note
                output_file = output_dir / f"rewritten_{file_path.name}"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(rewritten_content)

                change_summary = self._describe_major_changes(original_content, rewritten_content, studies)
                
                logger.info(f"  ✅ Successfully processed {file_path.name}")
                results["processed"] += 1
                results["details"].append(
                    {
                        "file": file_path.name,
                        "status": "success",
                        "output": str(output_file),
                        "new_studies_found": len(studies),
                        "studies_used_in_revision": min(len(studies), 5),
                        "major_changes_made": change_summary["major_changes_made"],
                        "citation_delta": change_summary["citation_delta"],
                        "recommendation_delta": change_summary["recommendation_delta"],
                    }
                )
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"  Error processing {file_path.name}: {e}")
                results["failed"] += 1
                results["details"].append({"file": file_path.name, "status": "failed", "reason": str(e)})
        
        return results

    def generate_processing_report(self, results: Dict, section: str, output_dir: Path):
        """Generate a detailed processing report"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        total_attempted = results['processed'] + results['failed']
        success_rate = (results['processed']/total_attempted*100) if total_attempted > 0 else 0
        
        report = f"""# Section {section.upper()} Processing Report
Generated: {timestamp}

## Summary
- **Files Processed:** {results['processed']}
- **Files Failed:** {results['failed']}  
- **Files Skipped:** {results['skipped']}
- **Success Rate:** {success_rate:.1f}% (of attempted)

## Detailed Results
"""
        
        for detail in results.get('details', []):
            status_emoji = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(detail['status'], "❓")
            report += f"- {status_emoji} **{detail['file']}**: {detail['status']}"
            if 'reason' in detail:
                report += f" - {detail['reason']}"
            if "new_studies_found" in detail:
                report += f" | new_studies_found={detail['new_studies_found']}"
            if "studies_used_in_revision" in detail:
                report += f" | studies_used_in_revision={detail['studies_used_in_revision']}"
            if "major_changes_made" in detail:
                report += f" | major_changes_made={detail['major_changes_made']}"
            if "unchanged_reason" in detail:
                report += f" | unchanged_reason={detail['unchanged_reason']}"
            if "citation_delta" in detail:
                report += f" | citation_delta={detail['citation_delta']}"
            if "recommendation_delta" in detail:
                report += f" | recommendation_delta={detail['recommendation_delta']}"
            report += "\n"
        
        # Save report
        report_file = output_dir / f"section_{section}_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to {report_file}")

def main():
    """Main function to run the fitness library processor"""
    
    parser = argparse.ArgumentParser(description="Process Fitness Library Notes")
    parser.add_argument("--section", default="A", help="Section to process (A, B, C, etc. or ALL)")
    parser.add_argument("--input-dir", required=True, help="Input directory with original notes")
    parser.add_argument("--output-dir", required=True, help="Output directory for processed notes")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--rate-limit", type=float, default=2.0, help="Delay between API calls (seconds)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze notes without processing")
    parser.add_argument("--start-num", type=int, help="Starting number for file processing range (e.g., 30 for A30)")
    parser.add_argument("--end-num", type=int, help="Ending number for file processing range (e.g., 65 for A65)")
    parser.add_argument("--min-new-studies", type=int, default=1, help="Minimum number of recent studies needed before rewrite")
    parser.add_argument("--evidence-cache-max-age-days", type=int, default=7, help="Max cache age before PubMed refresh")
    parser.add_argument("--refresh-only-stale", action="store_true", help="Only refresh notes whose rewritten outputs are older than --stale-days")
    parser.add_argument("--stale-days", type=int, default=30, help="Staleness threshold for rewritten notes")
    parser.add_argument("--min-relevance", type=float, default=0.0,
                        help="Drop studies whose Jaccard relevance to note title is below this (0..1)")
    parser.add_argument("--min-quality", type=float, default=0.0,
                        help="Drop studies whose composite quality score is below this (0..1)")
    parser.add_argument("--top-studies", type=int, default=5,
                        help="Number of top-ranked studies to forward to Claude")
    parser.add_argument("--lookback-years", type=int, default=4,
                        help="PubMed publication-date lookback window (years)")
    parser.add_argument(
        "--exclude-name-prefix",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Skip vault-root notes whose filename starts with PREFIX (repeatable). Example: EXL",
    )
    parser.add_argument(
        "--resume-from-name",
        default=None,
        metavar="NAME",
        help=(
            "Only process notes whose filename sorts >= NAME (same order as the rewriter loop). "
            "Example: F1. skips EXL… and starts at F1. Sleep…. "
            "Use F. to include section overview files such as F. Optimal Performance…."
        ),
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("API key required. Use --api-key or set ANTHROPIC_API_KEY environment variable")
        return
    
    # Setup directories
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize processor
    processor = FitnessLibraryProcessor(api_key, args.rate_limit)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - Analyzing files only")
        # TODO: Add dry run analysis
        return
    
    # Process the section
    results = processor.process_section(
        input_dir,
        output_dir,
        args.section,
        args.start_num,
        args.end_num,
        args.min_new_studies,
        args.evidence_cache_max_age_days,
        args.refresh_only_stale,
        args.stale_days,
        min_relevance=args.min_relevance,
        min_quality=args.min_quality,
        top_studies=args.top_studies,
        lookback_years=args.lookback_years,
        exclude_name_prefixes=args.exclude_name_prefix or None,
        resume_from_name=args.resume_from_name,
    )
    
    # Generate report
    processor.generate_processing_report(results, args.section, output_dir)
    
    logger.info(f"""
Processing Complete!
✅ Processed: {results['processed']}
❌ Failed: {results['failed']}
⏭️ Skipped: {results['skipped']}
    """)

if __name__ == "__main__":
    main() 