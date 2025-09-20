#!/usr/bin/env python3
"""
Generate PowerShell deletion script for safe numbered duplicates.
Identifies files with (1), (2), etc. suffixes that are browser download duplicates.
"""

import yaml
import re
from pathlib import Path
import sys

def is_numbered_duplicate(filepath1, filepath2):
    """Check if one file is a numbered duplicate of another (browser download style)."""
    path1 = Path(filepath1)
    path2 = Path(filepath2)
    
    # Extract base names (without extensions)
    name1 = path1.stem
    name2 = path2.stem
    
    # Pattern for numbered duplicates: " (1)", " (2)", etc.
    numbered_pattern = r'^(.+) \((\d+)\)$'
    
    # Check if one is numbered and the other is the base
    match1 = re.match(numbered_pattern, name1)
    match2 = re.match(numbered_pattern, name2)
    
    if match1 and not match2:
        # name1 is numbered, check if base matches name2
        return match1.group(1) == name2
    elif match2 and not match1:
        # name2 is numbered, check if base matches name1
        return match2.group(1) == name1
    elif match1 and match2:
        # Both are numbered, check if they have same base
        return match1.group(1) == match2.group(1)
    
    return False

def get_files_to_delete(duplicate_group):
    """Get list of safe files to delete from a duplicate group."""
    files = duplicate_group['files']
    paths = [f['path'] for f in files]
    
    # Find which files are numbered duplicates
    numbered_files = []
    base_files = []
    
    for path in paths:
        stem = Path(path).stem
        if re.match(r'^.+ \(\d+\)$', stem):
            numbered_files.append(path)
        else:
            base_files.append(path)
    
    # If we have both base and numbered files, delete the numbered ones
    if base_files and numbered_files:
        return numbered_files
    
    # If all are numbered, keep the one with lowest number, delete the rest
    if len(numbered_files) > 1:
        # Sort by number in parentheses
        def get_number(path):
            match = re.search(r'\((\d+)\)', Path(path).stem)
            return int(match.group(1)) if match else 0
        
        sorted_files = sorted(numbered_files, key=get_number)
        return sorted_files[1:]  # Keep first (lowest number), delete rest
    
    return []

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_deletion_script.py <scan_results.yaml>")
        sys.exit(1)
    
    scan_file = sys.argv[1]
    
    with open(scan_file, 'r', encoding='utf-8') as f:
        scan_data = yaml.safe_load(f)
    
    deletion_paths = []
    total_space_to_free = 0
    total_files_to_delete = 0
    files_already_deleted = 0
    
    for group in scan_data['duplicate_groups']:
        files_to_delete = get_files_to_delete(group)
        
        if files_to_delete:
            # Filter out files that no longer exist
            existing_files_to_delete = []
            files_in_group = {f['path']: f for f in group['files']}
            
            for file_path in files_to_delete:
                if Path(file_path).exists():
                    existing_files_to_delete.append(file_path)
                else:
                    files_already_deleted += 1
            
            if existing_files_to_delete:
                # Calculate space to free for existing files only
                group_space_freed = sum(files_in_group[path]['size_bytes'] 
                                      for path in existing_files_to_delete)
                
                total_space_to_free += group_space_freed
                total_files_to_delete += len(existing_files_to_delete)
                
                # Collect paths to emit into a portable Python deletion script
                deletion_paths.extend(existing_files_to_delete)
    
    # Emit a cross-platform Python deletion script if there are paths
    if deletion_paths:
        script_name = "deletions_from_scan.py"
        with open(script_name, 'w', encoding='utf-8') as out:
            out.write("#!/usr/bin/env python3\n")
            out.write("from pathlib import Path\n\n")
            out.write("FILES = [\n")
            for p in deletion_paths:
                out.write(f"    r'''{p}''',\n")
            out.write("]\n\n")
            out.write("def main():\n")
            out.write("    for p in FILES:\n")
            out.write("        try:\n")
            out.write("            Path(p).unlink()\n")
            out.write("            print('Deleted', p)\n")
            out.write("        except Exception as e:\n")
            out.write("            print('Failed to delete', p, '->', e)\n\n")
            out.write("if __name__ == '__main__':\n")
            out.write("    main()\n")

        print(f"Wrote deletion script: {script_name}")
        print(f"Total files to delete: {total_files_to_delete}")
        print(f"Total space to free: {total_space_to_free / 1024 / 1024 / 1024:.2f} GB")
        if files_already_deleted > 0:
            print(f"Files already deleted: {files_already_deleted}")
    else:
        print("No deletions necessary.")

if __name__ == "__main__":
    main()