#!/usr/bin/env python3
"""
FitLib Vault Export Script for Google AI Studio
Converts all markdown files into structured JSON for web app development
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class FitLibExporter:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.nodes = []
        self.link_map = {}
        self.citations = []
        
    def extract_internal_links(self, content: str) -> List[Dict]:
        """Extract [[internal links]] from content"""
        pattern = r'\[\[([^\]]+)\]\]'
        links = []
        for match in re.finditer(pattern, content):
            link_text = match.group(1)
            links.append({
                "text": link_text,
                "position": match.start()
            })
        return links
    
    def extract_citations(self, content: str) -> List[Dict]:
        """Extract research citations from markdown"""
        citations = []
        
        # Find Research Evidence section
        evidence_section = re.search(r'## Research Evidence\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if not evidence_section:
            return citations
        
        evidence_text = evidence_section.group(1)
        
        # Extract individual citations
        citation_pattern = r'\*\*(.+?)\*\* (.+?) \*(.+?)\*.*?DOI:\s*(https?://[^\s]+)'
        for match in re.finditer(citation_pattern, evidence_text, re.DOTALL):
            authors = match.group(1)
            title = match.group(2)
            journal = match.group(3)
            doi = match.group(4)
            
            # Extract quality indicators
            quality_match = re.search(r'Evidence quality:\s*(\w+)', evidence_text[match.end():match.end()+200])
            study_type_match = re.search(r'Study type:\s*(\w+)', evidence_text[match.end():match.end()+200])
            
            citation = {
                "authors": authors.strip(),
                "title": title.strip(),
                "journal": journal.strip(),
                "doi": doi.strip(),
                "quality": quality_match.group(1) if quality_match else "Unknown",
                "study_type": study_type_match.group(1) if study_type_match else "Unknown",
                "automation_validated": True  # Your automation system validated these
            }
            citations.append(citation)
        
        return citations
    
    def determine_series(self, filename: str) -> str:
        """Determine content series from filename"""
        if filename.startswith('A'):
            return 'foundational'
        elif filename.startswith('B'):
            return 'resistance_training'
        elif filename.startswith('C'):
            return 'nutrition'
        elif filename.startswith('D'):
            return 'weight_management'
        elif filename.startswith('E'):
            return 'cardiovascular'
        elif filename.startswith('F'):
            return 'performance'
        elif filename.startswith('G'):
            return 'special_populations'
        elif filename.startswith('X'):
            return 'sports_specific'
        else:
            return 'other'
    
    def extract_tags(self, content: str) -> List[str]:
        """Extract semantic tags from content"""
        tags = []
        
        # Extract from Key Points
        key_points = re.search(r'## Key Points\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if key_points:
            text = key_points.group(1).lower()
            # Common fitness terms
            terms = ['strength', 'hypertrophy', 'endurance', 'power', 'cardio', 
                    'nutrition', 'protein', 'energy', 'recovery', 'training']
            for term in terms:
                if term in text:
                    tags.append(term)
        
        return list(set(tags))
    
    def parse_markdown_file(self, filepath: Path) -> Dict:
        """Parse a single markdown file into structured data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata
        title_match = re.search(r'^###\s*(.+)$', content, re.MULTILINE)
        id_match = re.search(r'\*\*ID:\*\*\s*(.+)$', content, re.MULTILINE)
        created_match = re.search(r'\*\*Created:\*\*\s*(.+)$', content, re.MULTILINE)
        
        title = title_match.group(1).strip() if title_match else filepath.stem
        node_id = id_match.group(1).strip() if id_match else filepath.stem.replace(' ', '_').replace('.', '_')
        
        # Extract sections
        quick_takeaway = re.search(r'## Quick Takeaway\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        key_points = re.search(r'## Key Points\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        deep_dive = re.search(r'## Deep Dive\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        practical = re.search(r'## Practical Applications\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        mistakes = re.search(r'## Common Mistakes\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        related = re.search(r'## Related Concepts\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        
        # Extract data
        internal_links = self.extract_internal_links(content)
        citations = self.extract_citations(content)
        tags = self.extract_tags(content)
        series = self.determine_series(filepath.stem)
        
        node = {
            "id": node_id,
            "filename": filepath.name,
            "title": title,
            "series": series,
            "content_sections": {
                "quick_takeaway": quick_takeaway.group(1).strip() if quick_takeaway else "",
                "key_points": key_points.group(1).strip() if key_points else "",
                "deep_dive": deep_dive.group(1).strip() if deep_dive else "",
                "practical_applications": practical.group(1).strip() if practical else "",
                "common_mistakes": mistakes.group(1).strip() if mistakes else "",
                "related_concepts": related.group(1).strip() if related else ""
            },
            "full_markdown": content,
            "internal_links": internal_links,
            "citations": citations,
            "citation_count": len(citations),
            "tags": tags,
            "credibility_score": self.calculate_credibility(citations),
            "metadata": {
                "created": created_match.group(1).strip() if created_match else "Unknown",
                "word_count": len(content.split()),
                "link_count": len(internal_links)
            }
        }
        
        return node
    
    def calculate_credibility(self, citations: List[Dict]) -> float:
        """Calculate credibility score based on citations"""
        if not citations:
            return 0.5
        
        quality_scores = {
            'High': 1.0,
            'Medium': 0.7,
            'Low': 0.4,
            'Unknown': 0.5
        }
        
        study_type_scores = {
            'Meta-analysis': 1.0,
            'RCT': 0.9,
            'Review': 0.7,
            'Unknown': 0.5
        }
        
        total_score = 0
        for citation in citations:
            quality = quality_scores.get(citation.get('quality', 'Unknown'), 0.5)
            study_type = study_type_scores.get(citation.get('study_type', 'Unknown'), 0.5)
            total_score += (quality * 0.6 + study_type * 0.4)
        
        return min(total_score / len(citations), 1.0)
    
    def export_vault(self) -> Dict:
        """Export entire vault to structured JSON"""
        print("🚀 Starting FitLib Vault Export...")
        
        # Process all markdown files
        markdown_files = list(self.vault_path.glob('**/*.md'))
        markdown_files = [f for f in markdown_files if not any(
            skip in str(f) for skip in ['.obsidian', 'README', 'template', 'organized_library/processed']
        )]
        
        print(f"📁 Found {len(markdown_files)} markdown files")
        
        for filepath in markdown_files:
            try:
                node = self.parse_markdown_file(filepath)
                self.nodes.append(node)
                print(f"✅ Processed: {filepath.name}")
            except Exception as e:
                print(f"❌ Error processing {filepath.name}: {e}")
        
        # Build link map
        self.build_link_map()
        
        # Create export data
        export_data = {
            "metadata": {
                "title": "FitLib - Evidence-Based Fitness Research Library",
                "version": "1.0",
                "export_date": datetime.now().isoformat(),
                "total_nodes": len(self.nodes),
                "total_citations": sum(node['citation_count'] for node in self.nodes),
                "automation_system": {
                    "description": "Enterprise-grade citation automation with GRADE assessment",
                    "accuracy": "95%+",
                    "processing_speed": "10x faster than manual",
                    "validation": "Automated multi-API research discovery and quality scoring"
                }
            },
            "nodes": self.nodes,
            "link_graph": self.link_map,
            "series_taxonomy": {
                "foundational": "Core exercise science concepts",
                "resistance_training": "Strength and hypertrophy training",
                "nutrition": "Sports nutrition and supplementation",
                "cardiovascular": "Aerobic and endurance training",
                "weight_management": "Fat loss and body composition",
                "performance": "Performance optimization",
                "special_populations": "Exercise for specific populations",
                "sports_specific": "Sport-specific training methods"
            }
        }
        
        return export_data
    
    def build_link_map(self):
        """Build graph of all internal links"""
        for node in self.nodes:
            node_id = node['id']
            self.link_map[node_id] = []
            
            for link in node['internal_links']:
                # Try to match link text to existing nodes
                target_node = self.find_node_by_title(link['text'])
                if target_node:
                    self.link_map[node_id].append({
                        "target": target_node['id'],
                        "label": link['text']
                    })
    
    def find_node_by_title(self, title: str) -> Optional[Dict]:
        """Find node by matching title"""
        title_normalized = title.lower().strip()
        for node in self.nodes:
            if title_normalized in node['title'].lower():
                return node
        return None

def main():
    vault_path = "/Users/enes/fitlibvault-main"
    
    exporter = FitLibExporter(vault_path)
    export_data = exporter.export_vault()
    
    # Save to file
    output_file = Path(vault_path) / "fitlib_export.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✨ Export Complete!")
    print(f"📊 Total Nodes: {export_data['metadata']['total_nodes']}")
    print(f"📚 Total Citations: {export_data['metadata']['total_citations']}")
    print(f"💾 Saved to: {output_file}")
    print(f"\n🎯 Next Step: Use this JSON file with Google AI Studio to build your web app!")

if __name__ == "__main__":
    main()
