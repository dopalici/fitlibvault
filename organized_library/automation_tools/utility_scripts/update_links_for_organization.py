#!/usr/bin/env python3
"""
Update Internal Links for Organized Structure
Updates all internal links to work with the new folder organization
"""

import os
import re
from pathlib import Path

class LinkUpdater:
    def __init__(self):
        self.base_path = Path.cwd()
        self.organized_path = self.base_path / "organized_library"
        
        # Build mapping of files to their new locations
        self.file_location_map = {}
        self.build_file_location_map()
    
    def build_file_location_map(self):
        """Build a mapping of filename to its folder location"""
        
        for folder in self.organized_path.iterdir():
            if folder.is_dir() and folder.name != "original_backup":
                for file in folder.glob("*.md"):
                    if file.name != "README.md":
                        # Store relative path from organized_library root
                        relative_path = f"{folder.name}/{file.name}"
                        self.file_location_map[file.name] = relative_path
        
        print(f"📁 Mapped {len(self.file_location_map)} files to their new locations")
    
    def update_links_in_file(self, file_path: Path) -> int:
        """Update all internal links in a single file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all [[link]] patterns
            link_pattern = r'\[\[([^\]]+)\]\]'
            links_found = re.findall(link_pattern, content)
            
            if not links_found:
                return 0
            
            updated_content = content
            updates_made = 0
            
            for link_text in links_found:
                # Try to find the file this link refers to
                target_filename = None
                
                # Try exact match first
                if f"{link_text}.md" in self.file_location_map:
                    target_filename = f"{link_text}.md"
                else:
                    # Try to find partial matches
                    for filename in self.file_location_map:
                        if link_text in filename:
                            target_filename = filename
                            break
                
                if target_filename:
                    # Get the target's location
                    target_location = self.file_location_map[target_filename]
                    
                    # Calculate relative path from current file to target
                    current_folder = file_path.parent.name
                    target_folder = target_location.split('/')[0]
                    
                    if current_folder == target_folder:
                        # Same folder - just use filename
                        new_link = f"[[{target_filename.replace('.md', '')}]]"
                    else:
                        # Different folder - use relative path
                        new_link = f"[[../{target_location.replace('.md', '')}]]"
                    
                    # Only update if it's actually different
                    old_link = f"[[{link_text}]]"
                    if old_link != new_link:
                        updated_content = updated_content.replace(old_link, new_link)
                        updates_made += 1
            
            # Write back if changes were made
            if updates_made > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
            
            return updates_made
            
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
            return 0
    
    def update_all_links(self):
        """Update links in all files in the organized structure"""
        
        print("🔗 Starting link update process...")
        
        total_files = 0
        total_updates = 0
        
        for folder in self.organized_path.iterdir():
            if folder.is_dir() and folder.name not in ["original_backup", "processed_archive"]:
                folder_updates = 0
                folder_files = 0
                
                for file in folder.glob("*.md"):
                    if file.name != "README.md":
                        updates = self.update_links_in_file(file)
                        folder_updates += updates
                        folder_files += 1
                        total_files += 1
                
                if folder_files > 0:
                    print(f"📁 {folder.name}/: {folder_updates} links updated in {folder_files} files")
                    total_updates += folder_updates
        
        return total_files, total_updates

def main():
    print("🚀 Starting Link Update Process...")
    print("=" * 50)
    
    updater = LinkUpdater()
    total_files, total_updates = updater.update_all_links()
    
    print("\n" + "=" * 50)
    print("📋 Link Update Summary:")
    print(f"📁 Files processed: {total_files}")
    print(f"🔗 Links updated: {total_updates}")
    
    if total_updates > 0:
        print("✅ Internal links updated for new folder structure")
    else:
        print("ℹ️  No link updates needed (links may already be compatible)")

if __name__ == "__main__":
    main()