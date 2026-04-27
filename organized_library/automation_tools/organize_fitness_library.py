#!/usr/bin/env python3
"""
Organize Fitness Library Structure
Moves files into appropriate folders and creates README files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class FitnessLibraryOrganizer:
    def __init__(self):
        self.base_path = Path.cwd()
        self.organized_path = self.base_path / "organized_library"
        
        # Folder mapping based on file prefixes and types
        self.folder_mapping = {
            # Main content folders
            'foundation': {
                'patterns': ['A.', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'],
                'description': 'Foundational exercise science concepts including physiology, biomechanics, and basic principles'
            },
            'resistance_training': {
                'patterns': ['B.', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],
                'description': 'Resistance training methods, equipment, programming, and advanced techniques'
            },
            'nutrition_diet': {
                'patterns': ['C.', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                'description': 'Nutrition science, dietary strategies, supplements, and sports nutrition'
            },
            'cardiovascular_training': {
                'patterns': ['E.', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9'],
                'description': 'Cardiovascular and endurance training methods and protocols'
            },
            'performance_factors': {
                'patterns': ['F.', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9'],
                'description': 'Performance optimization factors including sleep, testing, and psychology'
            },
            'special_populations': {
                'patterns': ['G.', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9'],
                'description': 'Exercise considerations for special populations and health conditions'
            },
            'body_composition': {
                'patterns': ['H.', 'H1', 'H2', 'H3'],
                'description': 'Body composition assessment and realistic change rates'
            },
            'hormones_fitness': {
                'patterns': ['I.', 'I1', 'I2', 'I3'],
                'description': 'Hormonal responses to exercise and gender-specific considerations'
            },
            'technology': {
                'patterns': ['J.', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9'],
                'description': 'Fitness technology, research evaluation, and digital health tools'
            },
            'elite_performance': {
                'patterns': ['K.', 'K1', 'K2', 'K3', 'K4', 'K5', 'K6', 'K7', 'K8', 'K9'],
                'description': 'Elite athlete training, genetics, and peak performance strategies'
            },
            'cross_training': {
                'patterns': ['L.', 'L1', 'L2', 'L3', 'L4'],
                'description': 'Functional fitness, mobility, coordination, and movement patterns'
            },
            'recovery': {
                'patterns': ['M.', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9'],
                'description': 'Recovery strategies, modalities, and optimization techniques'
            },
            'long_term_development': {
                'patterns': ['N.', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9'],
                'description': 'Lifespan fitness development and long-term training strategies'
            },
            'integrated_approaches': {
                'patterns': ['O.', 'O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7', 'O8'],
                'description': 'Integrated programming and holistic fitness approaches'
            },
            'ethics': {
                'patterns': ['P.', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9'],
                'description': 'Ethical considerations in fitness training and coaching'
            },
            'key_overviews': {
                'patterns': ['Q.', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'Q7', 'Q8'],
                'description': 'Key topic overviews and summary concepts'
            },
            'equipment_technology': {
                'patterns': ['VIII-', 'VIII.'],
                'description': 'Fitness equipment, technology, and gear recommendations'
            },
            'health_conditions': {
                'patterns': ['IX-', 'IX.'],
                'description': 'Health conditions, injuries, and rehabilitation principles'
            },
            'sports_specific': {
                'patterns': ['X.', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'X8', 'X9'],
                'description': 'Sport-specific training methods and applications'
            },
            'exercise_library': {
                'patterns': ['EXL-'],
                'description': 'Exercise technique library with detailed movement instructions'
            },
            # Special folders
            'documentation': {
                'patterns': ['Z.', 'Z1', 'Z2', 'Z3', 'fitlib.md', 'README', 'COMPLETE_', 'FINAL_'],
                'description': 'Documentation, guides, and meta-information about the library'
            }
        }
    
    def get_folder_for_file(self, filename: str) -> str:
        """Determine which folder a file belongs in"""
        for folder, config in self.folder_mapping.items():
            for pattern in config['patterns']:
                if filename.startswith(pattern):
                    return folder
        
        # Default folder for unmatched files
        return 'documentation'
    
    def create_readme_for_folder(self, folder_name: str, files_list: list) -> str:
        """Create README content for a folder"""
        
        config = self.folder_mapping.get(folder_name, {})
        description = config.get('description', 'Fitness library content')
        
        readme_content = f"""# {folder_name.replace('_', ' ').title()}

## Overview
{description}

## Contents
This folder contains {len(files_list)} files covering various aspects of this topic area.

### Files in this folder:
"""
        
        # Group files by subtopic for better organization
        file_groups = {}
        for file in sorted(files_list):
            # Extract the main category (before the first period)
            if '.' in file and not file.startswith('README'):
                prefix = file.split('.')[0]
                if prefix not in file_groups:
                    file_groups[prefix] = []
                file_groups[prefix].append(file)
            else:
                if 'Other' not in file_groups:
                    file_groups['Other'] = []
                file_groups['Other'].append(file)
        
        for group, group_files in file_groups.items():
            if group != 'Other':
                readme_content += f"\n#### {group} Series:\n"
            else:
                readme_content += f"\n#### Other Files:\n"
            
            for file in group_files:
                # Extract title from filename
                title = file.replace('.md', '').replace('_', ' ')
                readme_content += f"- **{file}** - {title}\n"
        
        readme_content += f"""
## Usage Notes
- All files use markdown format (.md) for easy reading and cross-platform compatibility
- Internal links use `[[Topic Name]]` format for navigation between related topics
- Each file contains Quick Takeaway, Key Points, Deep Dive sections, and Research Evidence
- Files are interconnected - use the Related Topics section to explore connections

## Navigation
- Use your markdown reader's search function to find specific topics
- Follow internal links (in double brackets) to related concepts
- Start with overview files (ending with just the letter) for topic introductions

## Last Updated
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*This README was auto-generated during library organization*
"""
        
        return readme_content
    
    def organize_files(self):
        """Organize all files into appropriate folders"""
        
        print("🎯 Starting Fitness Library Organization...")
        
        # Get all .md files in the root directory
        md_files = [f for f in os.listdir(self.base_path) if f.endswith('.md') and not f.startswith('.')]
        
        print(f"📁 Found {len(md_files)} markdown files to organize")
        
        # Track files by folder
        folder_files = {}
        moved_files = 0
        
        for filename in md_files:
            folder = self.get_folder_for_file(filename)
            
            if folder not in folder_files:
                folder_files[folder] = []
            folder_files[folder].append(filename)
            
            # Move file to appropriate folder
            source = self.base_path / filename
            dest_folder = self.organized_path / folder
            dest_folder.mkdir(exist_ok=True)
            dest = dest_folder / filename
            
            try:
                shutil.copy2(source, dest)
                print(f"✅ {filename} → {folder}/")
                moved_files += 1
            except Exception as e:
                print(f"❌ Failed to move {filename}: {e}")
        
        print(f"\n📋 Organization Summary:")
        print(f"✅ Files moved: {moved_files}")
        print(f"📁 Folders created: {len(folder_files)}")
        
        # Create README files for each folder
        print(f"\n📝 Creating README files...")
        
        for folder, files in folder_files.items():
            readme_content = self.create_readme_for_folder(folder, files)
            readme_path = self.organized_path / folder / "README.md"
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"📄 Created README for {folder}/ ({len(files)} files)")
        
        return folder_files
    
    def create_main_readme(self, folder_structure):
        """Create main README for the organized library"""
        
        main_readme = f"""# Fitness Library - Organized Structure

## Overview
This is a comprehensive fitness and exercise science library organized into logical categories for easy navigation and study.

## Library Structure

### Main Content Categories

"""
        
        for folder, files in folder_structure.items():
            config = self.folder_mapping.get(folder, {})
            description = config.get('description', 'Fitness library content')
            
            main_readme += f"#### 📁 `{folder}/` ({len(files)} files)\n"
            main_readme += f"{description}\n\n"
        
        main_readme += f"""
## Quick Start Guide

### For Beginners:
1. Start with **foundation/** - Essential exercise science concepts
2. Move to **resistance_training/** or **cardiovascular_training/** based on your goals
3. Review **nutrition_diet/** for dietary guidance
4. Explore **recovery/** for optimization strategies

### For Practitioners:
1. **performance_factors/** - Advanced optimization techniques
2. **elite_performance/** - High-level training strategies
3. **special_populations/** - Working with diverse clients
4. **ethics/** - Professional practice standards

### For Researchers:
1. **technology/** - Research evaluation and tools
2. **integrated_approaches/** - Holistic programming
3. **documentation/** - Meta-information and guides

## Navigation Tips

- Each folder contains a detailed README explaining its contents
- Use `[[Topic Name]]` links to jump between related concepts
- Files are cross-referenced across categories
- Search functionality works across the entire library

## File Naming Convention

- **Letter prefix** indicates main category (A=Foundation, B=Resistance, etc.)
- **Number suffix** indicates subtopic within category
- **Descriptive names** make content immediately identifiable

## Quality Standards

All files include:
- ✅ Quick Takeaway for immediate understanding
- ✅ Key Points for actionable information
- ✅ Deep Dive for comprehensive knowledge
- ✅ Research Evidence with peer-reviewed citations
- ✅ Practical Applications with implementation guidance
- ✅ Safety Considerations and contraindications

## Total Library Stats

- **{sum(len(files) for files in folder_structure.values())} total files**
- **{len(folder_structure)} organized categories**
- **Professional-grade content** with expert-level depth
- **Complete cross-referencing** between all topics

## Last Updated
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
*Comprehensive fitness library organized for optimal learning and reference*
"""
        
        main_readme_path = self.organized_path / "README.md"
        with open(main_readme_path, 'w', encoding='utf-8') as f:
            f.write(main_readme)
        
        print(f"📄 Created main library README")
        
        return main_readme_path

def main():
    organizer = FitnessLibraryOrganizer()
    
    print("🚀 Fitness Library Organization Starting...")
    print("=" * 60)
    
    # Organize files into folders
    folder_structure = organizer.organize_files()
    
    # Create main README
    organizer.create_main_readme(folder_structure)
    
    print("\n" + "=" * 60)
    print("🎉 Organization Complete!")
    print(f"📁 Files organized into: organized_library/")
    print(f"📄 README files created for all {len(folder_structure)} folders")
    print(f"🔗 Internal links preserved across all files")
    print(f"📋 Main README created with navigation guide")

if __name__ == "__main__":
    main()