#!/usr/bin/env python3
"""
Safe file copy utility with filtering capabilities.
Copies directory trees while excluding unwanted files/directories.
"""

import os
import shutil
import hashlib
from pathlib import Path

def should_exclude(path, exclude_patterns):
    """Check if a path should be excluded based on patterns."""
    path_str = str(path)
    for pattern in exclude_patterns:
        if pattern in path_str:
            return True
    return False

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def copy_directory(src, dst, exclude_dirs=None, exclude_files=None, manifest_file=None):
    """
    Copy directory tree with exclusions.
    
    Args:
        src: Source directory path
        dst: Destination directory path
        exclude_dirs: List of directory names to exclude
        exclude_files: List of file patterns to exclude
        manifest_file: Path to manifest file to record copied files and hashes
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', 'venv', '.venv', 'build', 'dist', 'node_modules', 'workdir']
    
    if exclude_files is None:
        exclude_files = ['*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.exe']
    
    # Create destination directory
    os.makedirs(dst, exist_ok=True)
    
    # Initialize manifest
    manifest_entries = []
    
    # Walk source directory
    for root, dirs, files in os.walk(src):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d), exclude_dirs)]
        
        # Process files
        for file in files:
            src_file = os.path.join(root, file)
            
            # Check if file should be excluded
            if should_exclude(src_file, exclude_files):
                continue
            
            # Calculate relative path
            rel_path = os.path.relpath(src_file, src)
            dst_file = os.path.join(dst, rel_path)
            
            # Create destination directory if needed
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            
            # Copy file
            shutil.copy2(src_file, dst_file)
            
            # Calculate hash for manifest
            file_hash = get_file_hash(dst_file)
            manifest_entries.append({
                'path': rel_path,
                'hash': file_hash,
                'size': os.path.getsize(dst_file)
            })
    
    # Write manifest if requested
    if manifest_file:
        import json
        with open(manifest_file, 'w') as f:
            json.dump(manifest_entries, f, indent=2)
    
    return manifest_entries

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python safe_copy.py <source> <destination> [manifest_file]")
        print("Optional: [exclude_dirs] [exclude_files]")
        sys.exit(1)
    
    src = sys.argv[1]
    dst = sys.argv[2]
    manifest_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Default exclusions
    exclude_dirs = ['.git', '__pycache__', 'venv', '.venv', 'build', 'dist', 'node_modules']
    exclude_files = ['*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.exe']
    
    manifest = copy_directory(src, dst, exclude_dirs, exclude_files, manifest_file)
    print(f"Copied {len(manifest)} files to {dst}")
    if manifest_file:
        print(f"Manifest written to {manifest_file}")