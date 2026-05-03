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
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import anthropic
from datetime import datetime
import argparse
import logging
import httpx

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

class FitnessLibraryProcessor:
    """Main class for processing fitness library notes"""
    
    def __init__(self, api_key: str, rate_limit_delay: float = 2.0):
        """Initialize with Claude API key and rate limiting"""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.rate_limit_delay = rate_limit_delay
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # Load the SOP template
        self.rewrite_template = self._load_rewrite_template()
        
    def _load_rewrite_template(self) -> str:
        """Load the standardized rewrite template from SOP"""
        return """You are rewriting fitness/exercise science notes for better accessibility while maintaining scientific rigor. This is part of an interconnected Obsidian knowledge base.

CRITICAL REQUIREMENTS:
1. NEVER change the note title - this breaks links across the entire library
2. PRESERVE all existing [[links]] exactly as written - do not modify anything inside [[ ]]
3. MAINTAIN all scientific accuracy and citations
4. ADD practical applications if missing
5. ENSURE all key claims are backed by research citations
6. Use the exact structure provided below

STANDARD NOTE STRUCTURE:
```markdown
### [Original Title - NEVER CHANGE]
**ID:** [Keep original ID exactly as is]
**Created:** [Original date] (Updated: [Current date])

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
            
            # Extract ID
            id_match = re.search(r'\*\*ID:\*\*\s*(.+)$', content, re.MULTILINE)
            note_id = id_match.group(1).strip() if id_match else "NO-ID"
            logger.debug(f"Extracted ID: {note_id}")
            
            # Extract creation date
            date_match = re.search(r'\*\*Created:\*\*\s*([^(]+)', content, re.MULTILINE)
            created_date = date_match.group(1).strip() if date_match else "Unknown"
            logger.debug(f"Extracted date: {created_date}")
            
            # Extract section from filename or ID
            section = file_path.stem[0] if file_path.stem and file_path.stem[0].isalpha() else "Unknown"
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
            import requests
            url = f"https://doi.org/{doi}"
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def _validate_pmid(self, pmid: str) -> bool:
        """Validate a PMID by checking if it resolves to a valid PubMed URL"""
        try:
            import requests
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.status_code == 200
        except:
            return False

    def rewrite_note_with_claude(self, content: str) -> Optional[str]:
        """Use Claude to rewrite a note while preserving structure"""
        try:
            # Define the messages for the API call
            messages = [
                {"role": "user", "content": self.rewrite_template + content}
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

    def process_section(self, input_dir: Path, output_dir: Path, section: str, start_num: int = 1, end_num: int = 100) -> Dict:
        """Process all notes in a specific section (e.g., 'A', 'B', 'C')"""
        
        logger.info(f"Processing Section {section.upper()}")
        
        # Find all files in the section
        if section == "ALL":
            pattern = "*.md"
        else:
            # Handle both formats: "X11. Sprinting.md" and "X11*.md"
            pattern = f"{section}*.md"
        
        files = list(input_dir.glob(pattern))
        
        # Filter files by number range if start_num and end_num are provided
        if start_num is not None and end_num is not None:
            filtered_files = []
            for file_path in files:
                # Extract the number from the filename (e.g., A30. Biomechanics.md -> 30)
                match = re.match(rf"{section}(\d+)[\.\s].*\.md", file_path.name)
                if match:
                    file_num = int(match.group(1))
                    if start_num <= file_num <= end_num:
                        filtered_files.append(file_path)
            files = filtered_files

        if not files:
            logger.warning(f"No files found for section {section}")
            return {"processed": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"Found {len(files)} files for section {section}")
        
        results = {"processed": 0, "failed": 0, "skipped": 0, "details": []}
        
        for file_path in sorted(files):
            # Skip files in processed_notes directory
            if "processed_notes" in str(file_path):
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
                # Read original content
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Rewrite with Claude
                rewritten_content = self.rewrite_note_with_claude(original_content)
                
                if not rewritten_content:
                    logger.error(f"  Failed to rewrite {file_path.name}")
                    results["failed"] += 1
                    results["details"].append({"file": file_path.name, "status": "failed", "reason": "Claude API error"})
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
                
                logger.info(f"  ✅ Successfully processed {file_path.name}")
                results["processed"] += 1
                results["details"].append({"file": file_path.name, "status": "success", "output": str(output_file)})
                
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
    
    output_dir.mkdir(exist_ok=True)
    
    # Initialize processor
    processor = FitnessLibraryProcessor(api_key, args.rate_limit)
    
    if args.dry_run:
        logger.info("DRY RUN MODE - Analyzing files only")
        # TODO: Add dry run analysis
        return
    
    # Process the section
    results = processor.process_section(input_dir, output_dir, args.section, args.start_num, args.end_num)
    
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