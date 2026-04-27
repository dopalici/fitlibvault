#!/usr/bin/env python3
"""
Citation Validation Script for Fitness Library
Validates all DOI and PMID links in rewritten files and cross-references with research content
"""

import os
import re
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('citation_validation.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Citation:
    """Store citation information"""
    authors: str
    year: str
    title: str
    journal: str
    doi: Optional[str]
    pmid: Optional[str]
    key_finding: Optional[str]
    study_type: Optional[str]
    evidence_quality: Optional[str]
    file_origin: str
    context: str

class CitationValidator:
    """Validates research citations in fitness library files"""
    
    def __init__(self, rate_limit_delay: float = 1.0):
        self.rate_limit_delay = rate_limit_delay
        self.valid_dois = []
        self.invalid_dois = []
        self.valid_pmids = []
        self.invalid_pmids = []
        self.citations_without_links = []
        
    def validate_doi(self, doi: str) -> Tuple[bool, str]:
        """Validate a DOI by checking if it resolves"""
        try:
            url = f"https://doi.org/{doi}"
            response = requests.head(url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                return True, "Valid"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def validate_pmid(self, pmid: str) -> Tuple[bool, str]:
        """Validate a PMID by checking PubMed"""
        try:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            response = requests.head(url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                return True, "Valid"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def extract_citations_from_file(self, file_path: Path) -> List[Citation]:
        """Extract all citations from a markdown file"""
        citations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for research evidence section
            research_section = re.search(r'## Research Evidence\s*(.*?)(?=##|$)', content, re.DOTALL | re.IGNORECASE)
            if not research_section:
                return citations
            
            evidence_content = research_section.group(1)
            
            # Skip A23-style citations without links - we now require links for all citations
            
            # Extract enhanced format citations (with DOI and full details)
            enhanced_pattern = r'\*\*([^*]+)\.\*\*\s*([^*]+)\.\s*\*([^*]+)\*[^.]*\.\s*(?:DOI:\s*https://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)|PMID:\s*https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+))\s*(?:-\s*Key finding:\s*([^\n]*)\n)?(?:-\s*Study type:\s*([^\n]*)\n)?(?:-\s*Evidence quality:\s*([^\n]*)\n)?'
            enhanced_matches = re.finditer(enhanced_pattern, evidence_content, re.IGNORECASE | re.MULTILINE)
            
            for match in enhanced_matches:
                # Extract year from authors field if present
                authors_text = match.group(1).strip()
                year_match = re.search(r'\((\d{4})\)', authors_text)
                year = year_match.group(1) if year_match else "Unknown"
                authors = re.sub(r'\s*\(\d{4}\)', '', authors_text).strip()
                
                citation = Citation(
                    authors=authors,
                    year=year,
                    title=match.group(2).strip(),
                    journal=match.group(3).strip(),
                    doi=match.group(4) if match.group(4) else None,
                    pmid=match.group(5) if match.group(5) else None,
                    key_finding=match.group(6).strip() if match.group(6) else None,
                    study_type=match.group(7).strip() if match.group(7) else None,
                    evidence_quality=match.group(8).strip() if match.group(8) else None,
                    file_origin=str(file_path),
                    context=match.group(0)
                )
                citations.append(citation)
            
            # Fallback: Extract basic DOI citations (original format)
            basic_doi_pattern = r'\*\*([^*]+)\.\*\*\s*([^*]+)\.\s*\*([^*]+)\*[^.]*\.\s*DOI:\s*https://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'
            basic_doi_matches = re.finditer(basic_doi_pattern, evidence_content, re.IGNORECASE)
            
            for match in basic_doi_matches:
                # Skip if already captured by enhanced pattern
                if any(match.group(4) == c.doi for c in citations):
                    continue
                    
                # Extract year from authors field if present
                authors_text = match.group(1).strip()
                year_match = re.search(r'\((\d{4})\)', authors_text)
                year = year_match.group(1) if year_match else "Unknown"
                authors = re.sub(r'\s*\(\d{4}\)', '', authors_text).strip()
                
                citation = Citation(
                    authors=authors,
                    year=year,
                    title=match.group(2).strip(),
                    journal=match.group(3).strip(),
                    doi=match.group(4),
                    pmid=None,
                    key_finding=None,
                    study_type=None,
                    evidence_quality=None,
                    file_origin=str(file_path),
                    context=match.group(0)
                )
                citations.append(citation)
            
            # Extract PMID citations - Updated pattern for our format
            pmid_pattern = r'\*\*([^*]+)\.\*\*\s*([^*]+)\.\s*\*([^*]+)\*[^.]*\.\s*PMID:\s*https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)'
            pmid_matches = re.finditer(pmid_pattern, evidence_content, re.IGNORECASE)
            
            for match in pmid_matches:
                # Extract year from authors field if present
                authors_text = match.group(1).strip()
                year_match = re.search(r'\((\d{4})\)', authors_text)
                year = year_match.group(1) if year_match else "Unknown"
                authors = re.sub(r'\s*\(\d{4}\)', '', authors_text).strip()
                
                citation = Citation(
                    authors=authors,
                    year=year,
                    title=match.group(2).strip(),
                    journal=match.group(3).strip(),
                    doi=None,
                    pmid=match.group(4),
                    key_finding=None,
                    study_type=None,
                    evidence_quality=None,
                    file_origin=str(file_path),
                    context=match.group(0)
                )
                citations.append(citation)
            
            # CRITICAL: Find citations without mandatory DOI/PMID links
            citation_without_links_pattern = r'\*\*([^*]+)\.\*\*\s*([^*]+)\.\s*\*([^*]+)\*[^.]*\.(?!\s*(?:DOI|PMID):)'
            citations_without_links = re.finditer(citation_without_links_pattern, evidence_content, re.IGNORECASE)
            
            for match in citations_without_links:
                authors_text = match.group(1).strip()
                year_match = re.search(r'\((\d{4})\)', authors_text)
                year = year_match.group(1) if year_match else "Unknown"
                authors = re.sub(r'\s*\(\d{4}\)', '', authors_text).strip()
                
                citation = Citation(
                    authors=authors,
                    year=year,
                    title=match.group(2).strip(),
                    journal=match.group(3).strip(),
                    doi=None,
                    pmid=None,
                    key_finding=None,
                    study_type=None,
                    evidence_quality=None,
                    file_origin=str(file_path),
                    context=match.group(0)
                )
                self.citations_without_links.append(citation)
            
        except Exception as e:
            logger.error(f"Error extracting citations from {file_path}: {e}")
        
        return citations
    
    def validate_file(self, file_path: Path) -> Dict:
        """Validate all citations in a single file"""
        logger.info(f"Validating citations in {file_path.name}")
        
        citations = self.extract_citations_from_file(file_path)
        results = {
            "file": str(file_path),
            "total_citations": len(citations),
            "valid_dois": 0,
            "invalid_dois": 0,
            "valid_pmids": 0,
            "invalid_pmids": 0,
            "citations_without_links": 0,
            "details": []
        }
        
        for citation in citations:
            detail = {
                "authors": citation.authors,
                "year": citation.year,
                "title": citation.title,
                "journal": citation.journal,
                "doi": citation.doi,
                "pmid": citation.pmid,
                "key_finding": citation.key_finding,
                "study_type": citation.study_type,
                "evidence_quality": citation.evidence_quality,
                "status": "unknown",
                "error": None
            }
            
            if citation.doi:
                is_valid, error = self.validate_doi(citation.doi)
                if is_valid:
                    results["valid_dois"] += 1
                    detail["status"] = "valid_doi"
                    self.valid_dois.append(citation)
                else:
                    results["invalid_dois"] += 1
                    detail["status"] = "invalid_doi"
                    detail["error"] = error
                    self.invalid_dois.append(citation)
                
                time.sleep(self.rate_limit_delay)
            
            elif citation.pmid:
                is_valid, error = self.validate_pmid(citation.pmid)
                if is_valid:
                    results["valid_pmids"] += 1
                    detail["status"] = "valid_pmid"
                    self.valid_pmids.append(citation)
                else:
                    results["invalid_pmids"] += 1
                    detail["status"] = "invalid_pmid"
                    detail["error"] = error
                    self.invalid_pmids.append(citation)
                
                time.sleep(self.rate_limit_delay)
            
            results["details"].append(detail)
        
        # Count citations without links
        file_citations_without_links = [c for c in self.citations_without_links if c.file_origin == str(file_path)]
        results["citations_without_links"] = len(file_citations_without_links)
        
        return results
    
    def validate_directory(self, directory: Path, pattern: str = "rewritten_A*.md") -> Dict:
        """Validate all rewritten files in directory"""
        files = list(directory.glob(pattern))
        logger.info(f"Found {len(files)} files to validate")
        
        overall_results = {
            "total_files": len(files),
            "total_citations": 0,
            "total_valid_dois": 0,
            "total_invalid_dois": 0,
            "total_valid_pmids": 0,
            "total_invalid_pmids": 0,
            "total_citations_without_links": 0,
            "file_results": []
        }
        
        for file_path in sorted(files):
            if "A30" <= file_path.stem.split("_")[1][:3] <= "A65":  # Only A30-A65 range
                file_result = self.validate_file(file_path)
                overall_results["file_results"].append(file_result)
                
                # Aggregate totals
                overall_results["total_citations"] += file_result["total_citations"]
                overall_results["total_valid_dois"] += file_result["valid_dois"]
                overall_results["total_invalid_dois"] += file_result["invalid_dois"]
                overall_results["total_valid_pmids"] += file_result["valid_pmids"]
                overall_results["total_invalid_pmids"] += file_result["invalid_pmids"]
                overall_results["total_citations_without_links"] += file_result["citations_without_links"]
        
        return overall_results
    
    def generate_report(self, results: Dict, output_path: Path):
        """Generate a detailed validation report"""
        total_citations = results["total_citations"]
        total_with_links = results["total_valid_dois"] + results["total_invalid_dois"] + results["total_valid_pmids"] + results["total_invalid_pmids"]
        total_valid = results["total_valid_dois"] + results["total_valid_pmids"]
        
        success_rate = (total_valid / total_with_links * 100) if total_with_links > 0 else 0
        
        report = f"""# Citation Validation Report
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

## Summary
- **Files Validated:** {results['total_files']}
- **Total Citations:** {total_citations}
- **Citations with Links:** {total_with_links}
- **❌ CRITICAL: Citations without Links:** {results['total_citations_without_links']}
- **Valid Citations:** {total_valid}
- **Success Rate:** {success_rate:.1f}%

⚠️ **IMPORTANT**: All citations must have working DOI or PMID links going forward.

## DOI Validation
- **Valid DOIs:** {results['total_valid_dois']}
- **Invalid DOIs:** {results['total_invalid_dois']}

## PMID Validation  
- **Valid PMIDs:** {results['total_valid_pmids']}
- **Invalid PMIDs:** {results['total_invalid_pmids']}

## File-by-File Results

"""
        
        for file_result in results["file_results"]:
            file_name = Path(file_result["file"]).name
            report += f"### {file_name}\n"
            report += f"- Citations: {file_result['total_citations']}\n"
            report += f"- Valid DOIs: {file_result['valid_dois']}\n"
            report += f"- Invalid DOIs: {file_result['invalid_dois']}\n"
            report += f"- Valid PMIDs: {file_result['valid_pmids']}\n"
            report += f"- Invalid PMIDs: {file_result['invalid_pmids']}\n"
            report += f"- Without Links: {file_result['citations_without_links']}\n\n"
            
            # Show invalid citations
            invalid_citations = [d for d in file_result["details"] if "invalid" in d["status"]]
            if invalid_citations:
                report += "**Invalid Citations:**\n"
                for citation in invalid_citations:
                    report += f"- {citation['authors']} ({citation['year']}) - {citation['error']}\n"
                report += "\n"
            
            # Show enhanced citation details for valid citations
            valid_citations = [d for d in file_result["details"] if "valid" in d["status"]]
            if valid_citations:
                report += "**Valid Citations with Enhanced Details:**\n"
                for citation in valid_citations:
                    report += f"- **{citation['authors']} ({citation['year']})** {citation['title']}\n"
                    if citation['key_finding']:
                        report += f"  - Key finding: {citation['key_finding']}\n"
                    if citation['study_type']:
                        report += f"  - Study type: {citation['study_type']}\n"
                    if citation['evidence_quality']:
                        report += f"  - Evidence quality: {citation['evidence_quality']}\n"
                report += "\n"
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Validation report saved to {output_path}")

def main():
    """Main function"""
    validator = CitationValidator(rate_limit_delay=1.0)
    
    # Define paths
    processed_dir = Path("processed_notes")
    report_path = Path("citation_validation_report.md")
    
    if not processed_dir.exists():
        logger.error(f"Directory {processed_dir} does not exist")
        return
    
    # Validate all files
    results = validator.validate_directory(processed_dir)
    
    # Generate report
    validator.generate_report(results, report_path)
    
    # Save detailed results as JSON
    with open("citation_validation_results.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"""
Validation Complete!
📊 Total Citations: {results['total_citations']}
✅ Valid Citations: {results['total_valid_dois'] + results['total_valid_pmids']}
❌ Invalid Citations: {results['total_invalid_dois'] + results['total_invalid_pmids']}
⚠️  Without Links: {results['total_citations_without_links']}
""")

if __name__ == "__main__":
    main()