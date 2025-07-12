#!/usr/bin/env python3
"""
MacSweep - The Ultimate macOS File Cleanup Wizard
A comprehensive terminal utility for finding and cleaning unnecessary files on macOS
"""

import os
import sys
import argparse
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import subprocess

class FileScanner:
    """Scans directories and identifies files that can be cleaned"""
    
    def __init__(self):
        self.file_types = {
            'cache': ['.cache', '.tmp', '.temp', '.DS_Store'],
            'logs': ['.log', '.out', '.err'],
            'backups': ['.bak', '.backup', '.old', '.orig'],
            'downloads': ['Downloads'],
            'trash': ['.Trash', '.trash'],
            'development': ['node_modules', '.git', '__pycache__', '.pytest_cache', '.venv', 'venv'],
            'system': ['Library/Caches', 'Library/Logs', 'Library/Application Support'],
            'browser': ['Library/Safari', 'Library/Application Support/Google/Chrome', 'Library/Application Support/Firefox']
        }
    
    def scan_directory(self, path: str, max_depth: int = 3) -> Dict[str, List[Tuple[str, int, datetime]]]:
        """Scan directory and categorize files for cleanup"""
        results = defaultdict(list)
        
        try:
            for root, dirs, files in os.walk(path):
                # Limit depth to avoid scanning too deep
                current_depth = root.replace(path, '').count(os.sep)
                if current_depth >= max_depth:
                    dirs[:] = []
                    continue
                
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') or d in ['.cache', '.tmp', '.trash', '.Trash']]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Categorize files
                        category = self.categorize_file(file_path, file)
                        if category:
                            results[category].append((file_path, size, mtime))
                    except (OSError, IOError):
                        continue
                
                # Check for directories that are cleanup candidates
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    category = self.categorize_directory(dir_path, dir_name)
                    if category:
                        try:
                            size = self.get_directory_size(dir_path)
                            mtime = datetime.fromtimestamp(os.path.getmtime(dir_path))
                            results[category].append((dir_path, size, mtime))
                        except (OSError, IOError):
                            continue
        
        except PermissionError:
            print(f"Permission denied: {path}")
        
        return results
    
    def categorize_file(self, file_path: str, filename: str) -> Optional[str]:
        """Categorize a file based on its path and extension"""
        file_lower = filename.lower()
        path_lower = file_path.lower()
        
        # Check file extensions and names
        for category, patterns in self.file_types.items():
            for pattern in patterns:
                if file_lower.endswith(pattern.lower()) or pattern.lower() in path_lower:
                    return category
        
        # Check for large files (over 100MB)
        try:
            if os.path.getsize(file_path) > 100 * 1024 * 1024:
                return 'large_files'
        except OSError:
            pass
        
        # Check for old files (older than 30 days)
        try:
            mtime = os.path.getmtime(file_path)
            if datetime.fromtimestamp(mtime) < datetime.now() - timedelta(days=30):
                return 'old_files'
        except OSError:
            pass
        
        return None
    
    def categorize_directory(self, dir_path: str, dirname: str) -> Optional[str]:
        """Categorize a directory based on its name and path"""
        dirname_lower = dirname.lower()
        path_lower = dir_path.lower()
        
        for category, patterns in self.file_types.items():
            for pattern in patterns:
                if dirname_lower == pattern.lower() or pattern.lower() in path_lower:
                    return category
        
        return None
    
    def get_directory_size(self, path: str) -> int:
        """Get the total size of a directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
        except (OSError, IOError):
            pass
        return total_size

class CleanupEngine:
    """Handles file cleanup operations"""
    
    def __init__(self):
        self.dry_run = False
        self.verbose = False
    
    def set_dry_run(self, dry_run: bool):
        """Set dry run mode"""
        self.dry_run = dry_run
    
    def set_verbose(self, verbose: bool):
        """Set verbose mode"""
        self.verbose = verbose
    
    def cleanup_files(self, files: List[str]) -> Tuple[int, int]:
        """Clean up selected files and return (files_removed, bytes_freed)"""
        files_removed = 0
        bytes_freed = 0
        
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    if not self.dry_run:
                        os.remove(file_path)
                    if self.verbose:
                        print(f"Removed file: {file_path} ({self.format_size(size)})")
                    files_removed += 1
                    bytes_freed += size
                elif os.path.isdir(file_path):
                    size = self.get_directory_size(file_path)
                    if not self.dry_run:
                        shutil.rmtree(file_path)
                    if self.verbose:
                        print(f"Removed directory: {file_path} ({self.format_size(size)})")
                    files_removed += 1
                    bytes_freed += size
            except (OSError, IOError) as e:
                if self.verbose:
                    print(f"Error removing {file_path}: {e}")
                continue
        
        return files_removed, bytes_freed
    
    def get_directory_size(self, path: str) -> int:
        """Get the total size of a directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
        except (OSError, IOError):
            pass
        return total_size
    
    @staticmethod
    def format_size(size: int) -> str:
        """Format size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

class TerminalUI:
    """Interactive terminal user interface"""
    
    def __init__(self):
        self.cleanup_engine = CleanupEngine()
    
    def display_categories(self, scan_results: Dict[str, List[Tuple[str, int, datetime]]]):
        """Display cleanup categories with file counts and sizes"""
        print("\n" + "="*60)
        print("CLEANUP SUGGESTIONS")
        print("="*60)
        
        total_files = 0
        total_size = 0
        
        for category, files in scan_results.items():
            if not files:
                continue
            
            category_size = sum(size for _, size, _ in files)
            total_files += len(files)
            total_size += category_size
            
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Files: {len(files)}")
            print(f"  Size: {self.cleanup_engine.format_size(category_size)}")
            
            # Show a few example files
            for i, (path, size, mtime) in enumerate(files[:3]):
                print(f"    • {os.path.basename(path)} ({self.cleanup_engine.format_size(size)})")
            
            if len(files) > 3:
                print(f"    ... and {len(files) - 3} more files")
        
        print(f"\nTOTAL: {total_files} files, {self.cleanup_engine.format_size(total_size)}")
        return total_files, total_size
    
    def select_categories(self, scan_results: Dict[str, List[Tuple[str, int, datetime]]]) -> List[str]:
        """Interactive category selection"""
        print("\n" + "="*60)
        print("SELECT CATEGORIES TO CLEAN")
        print("="*60)
        
        categories = [cat for cat, files in scan_results.items() if files]
        
        if not categories:
            print("No files found for cleanup.")
            return []
        
        print("\nAvailable categories:")
        for i, category in enumerate(categories, 1):
            file_count = len(scan_results[category])
            total_size = sum(size for _, size, _ in scan_results[category])
            print(f"{i}. {category.replace('_', ' ').title()} ({file_count} files, {self.cleanup_engine.format_size(total_size)})")
        
        print(f"\nOptions:")
        print("• Enter numbers separated by commas (e.g., 1,3,5)")
        print("• Enter 'all' to select all categories")
        print("• Enter 'none' or 'quit' to exit")
        
        while True:
            try:
                choice = input("\nYour selection: ").strip().lower()
                
                if choice in ['none', 'quit', 'q']:
                    return []
                
                if choice == 'all':
                    return categories
                
                # Parse comma-separated numbers
                selected_indices = []
                for part in choice.split(','):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(categories):
                            selected_indices.append(idx)
                        else:
                            print(f"Invalid selection: {part}")
                            break
                    else:
                        print(f"Invalid input: {part}")
                        break
                else:
                    # All parts were valid
                    return [categories[i] for i in selected_indices]
                
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return []
            except EOFError:
                print("\nOperation cancelled.")
                return []
    
    def confirm_cleanup(self, selected_files: List[str], total_size: int) -> bool:
        """Confirm cleanup operation"""
        print(f"\n{'='*60}")
        print("CONFIRM CLEANUP")
        print("="*60)
        
        print(f"Files to be removed: {len(selected_files)}")
        print(f"Total size: {self.cleanup_engine.format_size(total_size)}")
        
        print("\nSample files:")
        for i, file_path in enumerate(selected_files[:10]):
            print(f"  • {file_path}")
        
        if len(selected_files) > 10:
            print(f"  ... and {len(selected_files) - 10} more files")
        
        print(f"\n⚠️  WARNING: This operation cannot be undone!")
        
        while True:
            try:
                choice = input("\nProceed with cleanup? (y/N): ").strip().lower()
                if choice in ['y', 'yes']:
                    return True
                elif choice in ['n', 'no', '']:
                    return False
                else:
                    print("Please enter 'y' or 'n'")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return False
            except EOFError:
                print("\nOperation cancelled.")
                return False

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="MacSweep - The Ultimate macOS File Cleanup Wizard")
    parser.add_argument("path", nargs="?", default=os.path.expanduser("~"), 
                       help="Path to scan (default: home directory)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be deleted without actually deleting")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Show detailed output")
    parser.add_argument("--depth", type=int, default=3, 
                       help="Maximum scan depth (default: 3)")
    parser.add_argument("--quick", action="store_true", 
                       help="Quick scan (common locations only)")
    
    args = parser.parse_args()
    
    # Validate path
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(args.path):
        print(f"Error: Path '{args.path}' is not a directory.")
        sys.exit(1)
    
    print("🧹 MacSweep - The Ultimate macOS File Cleanup Wizard")
    print("="*60)
    print(f"Scanning: {args.path}")
    print(f"Max depth: {args.depth}")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
    
    # Initialize components
    scanner = FileScanner()
    ui = TerminalUI()
    ui.cleanup_engine.set_dry_run(args.dry_run)
    ui.cleanup_engine.set_verbose(args.verbose)
    
    # Scan for files
    print("\nScanning for files...")
    start_time = time.time()
    
    if args.quick:
        # Quick scan - common cleanup locations
        common_paths = [
            os.path.expanduser("~/Library/Caches"),
            os.path.expanduser("~/Library/Logs"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/.cache"),
            os.path.expanduser("~/.tmp")
        ]
        
        scan_results = defaultdict(list)
        for path in common_paths:
            if os.path.exists(path):
                results = scanner.scan_directory(path, args.depth)
                for category, files in results.items():
                    scan_results[category].extend(files)
    else:
        scan_results = scanner.scan_directory(args.path, args.depth)
    
    scan_time = time.time() - start_time
    print(f"Scan completed in {scan_time:.2f} seconds")
    
    # Display results
    if not any(scan_results.values()):
        print("\n✅ No files found for cleanup. Your system looks clean!")
        return
    
    total_files, total_size = ui.display_categories(scan_results)
    
    # Interactive selection
    selected_categories = ui.select_categories(scan_results)
    
    if not selected_categories:
        print("No categories selected. Exiting.")
        return
    
    # Collect files from selected categories
    selected_files = []
    selected_size = 0
    
    for category in selected_categories:
        for file_path, size, mtime in scan_results[category]:
            selected_files.append(file_path)
            selected_size += size
    
    # Confirm and execute cleanup
    if ui.confirm_cleanup(selected_files, selected_size):
        print("\n🧹 Starting cleanup...")
        start_time = time.time()
        
        files_removed, bytes_freed = ui.cleanup_engine.cleanup_files(selected_files)
        
        cleanup_time = time.time() - start_time
        print(f"\n✅ Cleanup completed in {cleanup_time:.2f} seconds")
        print(f"Files removed: {files_removed}")
        print(f"Space freed: {ui.cleanup_engine.format_size(bytes_freed)}")
        
        if args.dry_run:
            print("\n💡 This was a dry run. No files were actually deleted.")
            print("   Run without --dry-run to perform actual cleanup.")
    else:
        print("Cleanup cancelled.")

if __name__ == "__main__":
    main() 