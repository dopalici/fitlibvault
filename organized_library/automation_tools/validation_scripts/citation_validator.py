#!/usr/bin/env python3
"""
Citation Validator for Fitness Library
Validates DOI/PMID links and citation quality
"""

import re
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
from datetime import datetime

class CitationValidator:
    """Validate citations and DOI/PMID links in processed files"""
    
    def __init__(self, timeout: int = 10, max_workers: int = 5):
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def validate_doi(self, doi: str) -> Dict:
        """Validate a single DOI"""
        try:
            url = f"https://doi.org/{doi}"
            response = self.session.head(url, allow_redirects=True, timeout=self.timeout)
            
            return {
                "doi": doi,
                "url": url,
                "status_code": response.status_code,
                "is_valid": response.status_code == 200,
                "final_url": response.url,
                "error": None
            }
        except requests.RequestException as e:
            return {
                "doi": doi,
                "url": f"https://doi.org/{doi}",
                "status_code": None,
                "is_valid": False,
                "final_url": None,
                "error": str(e)
            }
    
    def validate_pmid(self, pmid: str) -> Dict:
        """Validate a single PMID"""
        try:
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            response = self.session.head(url, allow_redirects=True, timeout=self.timeout)
            
            return {
                "pmid": pmid,
                "url": url,
                "status_code": response.status_code,
                "is_valid": response.status_code == 200,
                "final_url": response.url,
                "error": None
            }
        except requests.RequestException as e:
            return {
                "pmid": pmid,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "status_code": None,
                "is_valid": False,
                "final_url": None,
                "error": str(e)
            }
    
    def extract_citations_from_file(self, file_path: Path) -> Dict:
        """Extract all citations from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract DOIs
            doi_pattern = r'DOI:\s*https://doi\.org/(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'
            dois = re.findall(doi_pattern, content, re.IGNORECASE)
            
            # Extract PMIDs
            pmid_pattern = r'PMID:\s*https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)'
            pmids = re.findall(pmid_pattern, content, re.IGNORECASE)
            
            # Extract author citations
            author_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*(?:\s+et\s+al\.)?)\s*\((\d{4})\)'
            authors = re.findall(author_pattern, content)
            
            return {
                "file": file_path.name,
                "dois": list(set(dois)),  # Remove duplicates
                "pmids": list(set(pmids)),
                "authors": authors,
                "total_citations": len(set(dois)) + len(set(pmids)),
                "has_research_section": "Research Evidence" in content
            }
            
        except Exception as e:
            return {
                "file": file_path.name,
                "dois": [],
                "pmids": [],
                "authors": [],
                "total_citations": 0,
                "has_research_section": False,
                "error": str(e)
            }
    
    def validate_file_citations(self, file_path: Path) -> Dict:
        """Validate all citations in a single file"""
        print(f"🔍 Validating {file_path.name}...")
        
        citation_data = self.extract_citations_from_file(file_path)
        
        validation_results = {
            "file": file_path.name,
            "citation_count": citation_data["total_citations"],
            "has_research_section": citation_data["has_research_section"],
            "doi_validations": [],
            "pmid_validations": [],
            "valid_citations": 0,
            "invalid_citations": 0,
            "validation_rate": 0
        }
        
        # Validate DOIs
        for doi in citation_data["dois"]:
            result = self.validate_doi(doi)
            validation_results["doi_validations"].append(result)
            if result["is_valid"]:
                validation_results["valid_citations"] += 1
            else:
                validation_results["invalid_citations"] += 1
            time.sleep(0.5)  # Rate limiting
        
        # Validate PMIDs
        for pmid in citation_data["pmids"]:
            result = self.validate_pmid(pmid)
            validation_results["pmid_validations"].append(result)
            if result["is_valid"]:
                validation_results["valid_citations"] += 1
            else:
                validation_results["invalid_citations"] += 1
            time.sleep(0.5)  # Rate limiting
        
        # Calculate validation rate
        total_links = validation_results["valid_citations"] + validation_results["invalid_citations"]
        if total_links > 0:
            validation_results["validation_rate"] = (validation_results["valid_citations"] / total_links) * 100
        
        return validation_results
    
    def validate_directory_citations(self, directory: Path) -> Dict:
        """Validate citations in all processed files in directory"""
        print(f"🔍 Validating citations in {directory}...")
        
        processed_files = list(directory.glob("rewritten_*.md"))
        
        if not processed_files:
            print("❌ No processed files found")
            return {}
        
        print(f"📊 Found {len(processed_files)} files to validate")
        
        validation_summary = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(processed_files),
            "files_with_citations": 0,
            "files_without_citations": 0,
            "total_valid_citations": 0,
            "total_invalid_citations": 0,
            "overall_validation_rate": 0,
            "file_results": []
        }
        
        # Validate each file
        for file_path in processed_files:
            file_result = self.validate_file_citations(file_path)
            validation_summary["file_results"].append(file_result)
            
            if file_result["citation_count"] > 0:
                validation_summary["files_with_citations"] += 1
                validation_summary["total_valid_citations"] += file_result["valid_citations"]
                validation_summary["total_invalid_citations"] += file_result["invalid_citations"]
            else:
                validation_summary["files_without_citations"] += 1
        
        # Calculate overall rates
        total_citations = validation_summary["total_valid_citations"] + validation_summary["total_invalid_citations"]
        if total_citations > 0:
            validation_summary["overall_validation_rate"] = (
                validation_summary["total_valid_citations"] / total_citations
            ) * 100
        
        return validation_summary
    
    def generate_citation_report(self, validation_data: Dict, output_path: Path) -> Path:
        """Generate comprehensive citation validation report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Citation Validation Report
Generated: {timestamp}

## Summary
- **Files Validated:** {validation_data['total_files']}
- **Files with Citations:** {validation_data['files_with_citations']}
- **Files without Citations:** {validation_data['files_without_citations']}
- **Valid Citations:** {validation_data['total_valid_citations']}
- **Invalid Citations:** {validation_data['total_invalid_citations']}
- **Overall Validation Rate:** {validation_data['overall_validation_rate']:.1f}%

## Citation Quality Assessment
"""
        
        # Files without citations
        files_without_citations = [
            f["file"] for f in validation_data["file_results"] if f["citation_count"] == 0
        ]
        
        if files_without_citations:
            report += f"\n### ⚠️ Files Missing Citations ({len(files_without_citations)})\n"
            for filename in files_without_citations[:10]:  # Show first 10
                report += f"- {filename}\n"
            if len(files_without_citations) > 10:
                report += f"- ... and {len(files_without_citations) - 10} more\n"
        
        # Files with invalid citations
        files_with_invalid = [
            f for f in validation_data["file_results"] 
            if f["invalid_citations"] > 0
        ]
        
        if files_with_invalid:
            report += f"\n### ❌ Files with Invalid Citations ({len(files_with_invalid)})\n"
            for file_data in files_with_invalid[:10]:
                report += f"- **{file_data['file']}**: {file_data['invalid_citations']} invalid out of {file_data['citation_count']} total\n"
        
        # Detailed file results
        report += "\n## Detailed File Results\n"
        
        for file_data in validation_data["file_results"]:
            if file_data["citation_count"] > 0:
                status_emoji = "✅" if file_data["invalid_citations"] == 0 else "⚠️" if file_data["valid_citations"] > 0 else "❌"
                
                report += f"""
### {status_emoji} {file_data['file']}
- **Citations:** {file_data['citation_count']}
- **Valid:** {file_data['valid_citations']}
- **Invalid:** {file_data['invalid_citations']}
- **Rate:** {file_data['validation_rate']:.1f}%
- **Has Research Section:** {'✅' if file_data['has_research_section'] else '❌'}
"""
                
                # Show invalid DOIs/PMIDs
                invalid_dois = [d for d in file_data["doi_validations"] if not d["is_valid"]]
                invalid_pmids = [p for p in file_data["pmid_validations"] if not p["is_valid"]]
                
                if invalid_dois:
                    report += "- **Invalid DOIs:**\n"
                    for doi_data in invalid_dois:
                        report += f"  - `{doi_data['doi']}` (Error: {doi_data.get('error', 'HTTP ' + str(doi_data['status_code']))})\n"
                
                if invalid_pmids:
                    report += "- **Invalid PMIDs:**\n"
                    for pmid_data in invalid_pmids:
                        report += f"  - `{pmid_data['pmid']}` (Error: {pmid_data.get('error', 'HTTP ' + str(pmid_data['status_code']))})\n"
        
        # Recommendations
        report += "\n## Recommendations\n"
        
        if validation_data["files_without_citations"] > 0:
            report += f"- **Add Citations:** {validation_data['files_without_citations']} files need research citations\n"
        
        if validation_data["total_invalid_citations"] > 0:
            report += f"- **Fix Invalid Citations:** {validation_data['total_invalid_citations']} citations need correction\n"
        
        if validation_data["overall_validation_rate"] >= 90:
            report += "- ✅ **Excellent citation quality!** Consider spot-checking remaining issues\n"
        elif validation_data["overall_validation_rate"] >= 70:
            report += "- ⚠️ **Good citation quality** with room for improvement\n"
        else:
            report += "- ❌ **Citation quality needs attention** - systematic review recommended\n"
        
        # Save report
        report_file = output_path / "citation_validation_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save JSON data
        json_file = output_path / "citation_validation_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(validation_data, f, indent=2, default=str)
        
        print(f"📊 Citation validation report saved: {report_file}")
        return report_file

def main():
    """CLI interface for citation validator"""
    parser = argparse.ArgumentParser(description="Citation Validator for Fitness Library")
    parser.add_argument("--input-dir", default="processed_notes", help="Directory with processed files")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum concurrent requests")
    
    args = parser.parse_args()
    
    validator = CitationValidator(timeout=args.timeout, max_workers=args.max_workers)
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"❌ Directory not found: {input_dir}")
        return
    
    print("🔍 Starting citation validation...")
    
    # Validate all citations
    validation_data = validator.validate_directory_citations(input_dir)
    
    if not validation_data:
        print("❌ No validation data generated")
        return
    
    # Generate report
    report_file = validator.generate_citation_report(validation_data, input_dir)
    
    print(f"""
🏁 CITATION VALIDATION COMPLETE!
📊 Files: {validation_data['total_files']}
✅ Valid Citations: {validation_data['total_valid_citations']}
❌ Invalid Citations: {validation_data['total_invalid_citations']}
📈 Success Rate: {validation_data['overall_validation_rate']:.1f}%
📄 Report: {report_file}
    """)

if __name__ == "__main__":
    main()