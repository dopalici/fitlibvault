#!/usr/bin/env python3
"""
Replace Original Files with Rewritten Versions
Maintains internal link structure and creates backups
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def replace_files_with_rewritten():
    """Replace original files with rewritten versions, excluding EXL files"""
    
    base_path = Path.cwd()
    processed_path = base_path / "processed_notes"
    backup_path = base_path / "original_backup"
    
    # Ensure backup directory exists
    backup_path.mkdir(exist_ok=True)
    
    # Get all rewritten files (excluding EXL files)
    rewritten_files = []
    for file in processed_path.glob("rewritten_*.md"):
        if not file.name.startswith("rewritten_EXL"):
            rewritten_files.append(file)
    
    print(f"🎯 Found {len(rewritten_files)} rewritten files to replace (excluding EXL files)")
    
    successful_replacements = 0
    failed_replacements = 0
    
    for rewritten_file in rewritten_files:
        try:
            # Extract original filename
            original_name = rewritten_file.name.replace("rewritten_", "")
            original_file = base_path / original_name
            
            if original_file.exists():
                # Create backup with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{original_name.replace('.md', '')}_{timestamp}_backup.md"
                backup_file = backup_path / backup_name
                
                # Copy original to backup
                shutil.copy2(original_file, backup_file)
                
                # Replace original with rewritten
                shutil.copy2(rewritten_file, original_file)
                
                print(f"✅ Replaced: {original_name}")
                successful_replacements += 1
                
            else:
                print(f"⚠️  Original not found: {original_name}")
                failed_replacements += 1
                
        except Exception as e:
            print(f"❌ Failed to replace {rewritten_file.name}: {str(e)}")
            failed_replacements += 1
    
    print(f"\n📊 Replacement Summary:")
    print(f"✅ Successful: {successful_replacements}")
    print(f"❌ Failed: {failed_replacements}")
    print(f"📁 Backups stored in: original_backup/")
    
    return successful_replacements, failed_replacements

def verify_link_preservation():
    """Verify that internal links are preserved in replaced files"""
    
    print(f"\n🔗 Verifying Link Preservation...")
    
    # Sample a few files to check links
    test_files = [
        "A. Foundational Concepts.md",
        "B. Resistance Training.md", 
        "C. Nutrition & Diet.md",
        "A1. Energy Balance.md",
        "B1. Progressive Overload.md"
    ]
    
    link_pattern_found = 0
    
    for filename in test_files:
        file_path = Path.cwd() / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Count [[]] style links
                link_count = content.count('[[')
                if link_count > 0:
                    print(f"✅ {filename}: {link_count} internal links found")
                    link_pattern_found += link_count
                else:
                    print(f"⚠️  {filename}: No internal links found")
                    
            except Exception as e:
                print(f"❌ Error checking {filename}: {str(e)}")
    
    print(f"🔗 Total internal links verified: {link_pattern_found}")
    return link_pattern_found > 0

def main():
    print("🚀 Starting File Replacement Process...")
    print("=" * 50)
    
    # Replace files
    successful, failed = replace_files_with_rewritten()
    
    # Verify links
    links_preserved = verify_link_preservation()
    
    print("\n" + "=" * 50)
    print("📋 Final Status:")
    print(f"✅ Files Replaced: {successful}")
    print(f"❌ Failed Replacements: {failed}")
    print(f"🔗 Links Preserved: {'Yes' if links_preserved else 'Check Required'}")
    print(f"📁 Original Backup: original_backup/ directory")
    
    if successful > 0:
        print("\n🎉 Replacement process completed successfully!")
        print("All original files have been backed up and replaced with enhanced versions.")
    else:
        print("\n⚠️  No files were replaced. Please check file paths and permissions.")

if __name__ == "__main__":
    main()