#!/usr/bin/env python3
"""
Analysis Tools for Fitness Library Processing
Analyze progress, validate files, generate statistics
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

class FitnessLibraryAnalyzer:
    """Analyze fitness library processing status and quality"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.processed_notes_dir = self.base_dir / "processed_notes"
        
    def analyze_processing_status(self) -> Dict:
        """Analyze current processing status across all sections"""
        print("🔍 Analyzing processing status...")
        
        sections = {
            "A": {"range": (1, 65), "desc": "Foundational Concepts"},
            "B": {"range": (1, 78), "desc": "Resistance Training"},
            "C": {"range": (1, 105), "desc": "Nutrition & Diet"},
            "F": {"range": (5, 34), "desc": "Performance Testing"},
            "G": {"range": (4, 16), "desc": "Special Populations"},
            "J": {"range": (4, 10), "desc": "Technology in Fitness"},
            "K": {"range": (6, 15), "desc": "Elite Performance"},
            "M": {"range": (4, 8), "desc": "Recovery Strategies"},
            "N": {"range": (4, 8), "desc": "Long-Term Development"},
            "O": {"range": (4, 8), "desc": "Integrated Approaches"},
            "P": {"range": (5, 10), "desc": "Ethical Considerations"},
            "IX": {"range": (8, 15), "desc": "Health Conditions"},
            "X": {"range": (13, 20), "desc": "Sports-Specific"},
        }
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "sections": {},
            "totals": {
                "expected_files": 0,
                "processed_files": 0,
                "missing_files": 0,
                "completion_rate": 0
            }
        }
        
        for section, config in sections.items():
            start_num, end_num = config["range"]
            section_analysis = self._analyze_section(section, start_num, end_num)
            section_analysis["description"] = config["desc"]
            analysis["sections"][section] = section_analysis
            
            # Update totals
            analysis["totals"]["expected_files"] += section_analysis["expected_count"]
            analysis["totals"]["processed_files"] += section_analysis["processed_count"]
            analysis["totals"]["missing_files"] += section_analysis["missing_count"]
        
        # Calculate completion rate
        if analysis["totals"]["expected_files"] > 0:
            analysis["totals"]["completion_rate"] = (
                analysis["totals"]["processed_files"] / analysis["totals"]["expected_files"]
            ) * 100
        
        return analysis
    
    def _analyze_section(self, section: str, start_num: int, end_num: int) -> Dict:
        """Analyze processing status for a specific section"""
        expected_files = []
        processed_files = []
        missing_files = []
        
        for num in range(start_num, end_num + 1):
            # Check for original file
            original_patterns = [
                f"{section}{num}.*.md",
                f"{section}{num:02d}.*.md"
            ]
            
            original_found = False
            for pattern in original_patterns:
                if list(self.base_dir.glob(pattern)):
                    expected_files.append(f"{section}{num}")
                    original_found = True
                    break
            
            if not original_found:
                continue
            
            # Check for processed file
            processed_patterns = [
                f"rewritten_{section}{num}.*.md",
                f"rewritten_{section}{num:02d}.*.md"
            ]
            
            processed_found = False
            for pattern in processed_patterns:
                if list(self.processed_notes_dir.glob(pattern)):
                    processed_files.append(f"{section}{num}")
                    processed_found = True
                    break
            
            if not processed_found:
                missing_files.append(f"{section}{num}")
        
        completion_rate = (len(processed_files) / len(expected_files)) * 100 if expected_files else 0
        
        return {
            "expected_count": len(expected_files),
            "processed_count": len(processed_files),
            "missing_count": len(missing_files),
            "completion_rate": completion_rate,
            "expected_files": expected_files,
            "processed_files": processed_files,
            "missing_files": missing_files
        }
    
    def validate_processed_files(self) -> Dict:
        """Validate quality of processed files"""
        print("🔍 Validating processed files...")
        
        processed_files = list(self.processed_notes_dir.glob("rewritten_*.md"))
        
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(processed_files),
            "valid_files": 0,
            "invalid_files": 0,
            "validation_details": [],
            "common_issues": {}
        }
        
        issue_counts = {}
        
        for file_path in processed_files:
            file_validation = self._validate_file(file_path)
            validation_results["validation_details"].append(file_validation)
            
            if file_validation["is_valid"]:
                validation_results["valid_files"] += 1
            else:
                validation_results["invalid_files"] += 1
                
                # Count common issues
                for issue in file_validation["issues"]:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        validation_results["common_issues"] = issue_counts
        validation_results["validation_rate"] = (
            validation_results["valid_files"] / validation_results["total_files"]
        ) * 100 if validation_results["total_files"] > 0 else 0
        
        return validation_results
    
    def _validate_file(self, file_path: Path) -> Dict:
        """Validate a single processed file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # Check for required sections
            required_sections = ["Quick Takeaway", "Key Points", "Deep Dive"]
            for section in required_sections:
                if section not in content:
                    issues.append(f"Missing section: {section}")
            
            # Check for research evidence
            if "Research Evidence" not in content:
                issues.append("Missing Research Evidence section")
            
            # Check for DOI/PMID links
            has_doi = bool(re.search(r'DOI:\s*https://doi\.org/', content))
            has_pmid = bool(re.search(r'PMID:\s*https://pubmed\.ncbi\.nlm\.nih\.gov/', content))
            
            if not (has_doi or has_pmid):
                issues.append("No DOI or PMID links found")
            
            # Check for title preservation
            title_match = re.search(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
            if not title_match:
                issues.append("No title found")
            
            # Check for ID preservation
            id_match = re.search(r'\*\*ID:\*\*\s*(.+)$', content, re.MULTILINE)
            if not id_match:
                issues.append("No ID found")
            
            # Check minimum word count
            word_count = len(content.split())
            if word_count < 500:
                issues.append(f"Content too short: {word_count} words")
            
            return {
                "file": file_path.name,
                "is_valid": len(issues) == 0,
                "issues": issues,
                "word_count": word_count,
                "has_doi_pmid": has_doi or has_pmid
            }
            
        except Exception as e:
            return {
                "file": file_path.name,
                "is_valid": False,
                "issues": [f"File read error: {str(e)}"],
                "word_count": 0,
                "has_doi_pmid": False
            }
    
    def generate_progress_report(self, analysis: Dict, validation: Dict) -> Path:
        """Generate comprehensive progress report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Fitness Library Progress Report
Generated: {timestamp}

## Overall Progress
- **Expected Files:** {analysis['totals']['expected_files']:,}
- **Processed Files:** {analysis['totals']['processed_files']:,}
- **Missing Files:** {analysis['totals']['missing_files']:,}
- **Completion Rate:** {analysis['totals']['completion_rate']:.1f}%

## Quality Validation
- **Files Validated:** {validation['total_files']:,}
- **Valid Files:** {validation['valid_files']:,}
- **Invalid Files:** {validation['invalid_files']:,}
- **Validation Rate:** {validation['validation_rate']:.1f}%

## Section Breakdown
"""
        
        for section, data in analysis["sections"].items():
            status_emoji = "✅" if data["completion_rate"] == 100 else "🔄" if data["completion_rate"] > 0 else "⏳"
            
            report += f"""
### {status_emoji} Section {section}: {data['description']}
- **Progress:** {data['processed_count']}/{data['expected_count']} ({data['completion_rate']:.1f}%)
- **Missing Files:** {len(data['missing_files'])}
"""
            
            if data['missing_files']:
                missing_preview = ', '.join(data['missing_files'][:5])
                if len(data['missing_files']) > 5:
                    missing_preview += f" (and {len(data['missing_files']) - 5} more)"
                report += f"- **Missing:** {missing_preview}\n"
        
        # Quality issues
        if validation['common_issues']:
            report += "\n## Common Quality Issues\n"
            for issue, count in sorted(validation['common_issues'].items(), key=lambda x: x[1], reverse=True):
                report += f"- **{issue}:** {count} files\n"
        
        # Recommendations
        report += "\n## Recommendations\n"
        
        incomplete_sections = [s for s, d in analysis["sections"].items() if d["completion_rate"] < 100]
        if incomplete_sections:
            report += f"- **Priority Processing:** Sections {', '.join(incomplete_sections)}\n"
        
        if validation['invalid_files'] > 0:
            report += f"- **Quality Review:** {validation['invalid_files']} files need attention\n"
        
        if analysis['totals']['completion_rate'] >= 90:
            report += "- ✅ **Near completion!** Consider final quality review\n"
        
        # Save report
        report_file = self.processed_notes_dir / "progress_analysis_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save JSON data
        json_file = self.processed_notes_dir / "progress_analysis_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "analysis": analysis,
                "validation": validation
            }, f, indent=2, default=str)
        
        print(f"📊 Progress report saved: {report_file}")
        return report_file

def main():
    """CLI interface for analysis tools"""
    parser = argparse.ArgumentParser(description="Fitness Library Analysis Tools")
    parser.add_argument("--base-dir", default=".", help="Base directory")
    parser.add_argument("--action", choices=["status", "validate", "report"], default="report",
                       help="Analysis action to perform")
    
    args = parser.parse_args()
    
    analyzer = FitnessLibraryAnalyzer(args.base_dir)
    
    if args.action == "status":
        analysis = analyzer.analyze_processing_status()
        print(f"\n📊 PROCESSING STATUS")
        print(f"Completion: {analysis['totals']['completion_rate']:.1f}%")
        print(f"Files: {analysis['totals']['processed_files']}/{analysis['totals']['expected_files']}")
        
    elif args.action == "validate":
        validation = analyzer.validate_processed_files()
        print(f"\n🔍 VALIDATION RESULTS")
        print(f"Valid files: {validation['valid_files']}/{validation['total_files']}")
        print(f"Validation rate: {validation['validation_rate']:.1f}%")
        
    elif args.action == "report":
        analysis = analyzer.analyze_processing_status()
        validation = analyzer.validate_processed_files()
        report_file = analyzer.generate_progress_report(analysis, validation)
        
        print(f"\n📋 COMPREHENSIVE ANALYSIS COMPLETE")
        print(f"📊 Report: {report_file}")
        print(f"✅ Completion: {analysis['totals']['completion_rate']:.1f}%")
        print(f"🔍 Validation: {validation['validation_rate']:.1f}%")

if __name__ == "__main__":
    main()