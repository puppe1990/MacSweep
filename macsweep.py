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
import mimetypes
import threading
import queue

class ProgressBar:
    """Simple progress bar for terminal output"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = time.time()
        self.bar_width = 50
    
    def update(self, increment: int = 1):
        """Update progress bar"""
        self.current += increment
        percentage = min(100, (self.current / self.total) * 100)
        
        # Calculate bar progress
        filled_width = int(self.bar_width * self.current // self.total)
        bar = '█' * filled_width + '-' * (self.bar_width - filled_width)
        
        # Calculate elapsed time and ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --"
        
        # Clear line and print progress
        print(f'\r{self.description}: [{bar}] {percentage:5.1f}% ({self.current}/{self.total}) {eta_str}', end='', flush=True)
    
    def finish(self):
        """Finish progress bar"""
        elapsed = time.time() - self.start_time
        print(f'\r{self.description}: [{"█" * self.bar_width}] 100.0% ({self.total}/{self.total}) Completed in {elapsed:.1f}s')

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
        
        # File format categories for Downloads analysis
        self.format_categories = {
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages', '.key', '.ppt', '.pptx', '.xls', '.xlsx'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.heic', '.raw', '.cr2', '.nef'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.mpg', '.mpeg'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.aiff', '.alac'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.dmg', '.iso'],
            'executables': ['.exe', '.app', '.dmg', '.pkg', '.deb', '.rpm', '.msi', '.bat', '.sh'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs', '.swift'],
            'data': ['.json', '.xml', '.csv', '.sql', '.db', '.sqlite', '.yaml', '.yml', '.toml', '.ini', '.conf'],
            'fonts': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
            'other': []  # For unknown formats
        }
    
    def count_files(self, path: str, max_depth: int = 3) -> int:
        """Count total files in directory for progress tracking"""
        total_files = 0
        try:
            for root, dirs, files in os.walk(path):
                # Limit depth to avoid scanning too deep
                current_depth = root.replace(path, '').count(os.sep)
                if current_depth >= max_depth:
                    dirs[:] = []
                    continue
                
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') or d in ['.cache', '.tmp', '.trash', '.Trash']]
                total_files += len(files)
        except PermissionError:
            pass
        return total_files
    
    def scan_directory(self, path: str, max_depth: int = 3, show_progress: bool = True) -> Dict[str, List[Tuple[str, int, datetime]]]:
        """Scan directory and categorize files for cleanup"""
        results = defaultdict(list)
        
        # Count files for progress bar
        if show_progress:
            print("Counting files for progress tracking...")
            total_files = self.count_files(path, max_depth)
            progress = ProgressBar(total_files, "Scanning files")
        else:
            progress = None
        
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
                        pass
                    
                    # Update progress
                    if progress:
                        progress.update()
                
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
        
        # Finish progress bar
        if progress:
            progress.finish()
        
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
    
    def analyze_downloads_formats(self, downloads_path: str = None, show_progress: bool = True) -> Dict[str, Dict[str, List[Tuple[str, int, datetime]]]]:
        """Analyze file formats in Downloads folder and categorize them"""
        if downloads_path is None:
            downloads_path = os.path.expanduser("~/Downloads")
        
        if not os.path.exists(downloads_path):
            return {}
        
        format_analysis = defaultdict(lambda: defaultdict(list))
        
        # Count files for progress tracking
        if show_progress:
            print("Counting Downloads files for progress tracking...")
            total_files = 0
            try:
                for root, dirs, files in os.walk(downloads_path):
                    total_files += len(files)
            except PermissionError:
                pass
            
            progress = ProgressBar(total_files, "Analyzing Downloads")
        else:
            progress = None
        
        try:
            for root, dirs, files in os.walk(downloads_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Get file extension
                        _, ext = os.path.splitext(file.lower())
                        
                        # Categorize by format
                        category = self.categorize_file_format(ext, file_path)
                        format_analysis[category][ext].append((file_path, size, mtime))
                        
                    except (OSError, IOError):
                        pass
                    
                    # Update progress
                    if progress:
                        progress.update()
        except PermissionError:
            print(f"Permission denied: {downloads_path}")
        
        # Finish progress bar
        if progress:
            progress.finish()
        
        return format_analysis
    
    def categorize_file_format(self, extension: str, file_path: str) -> str:
        """Categorize a file by its format"""
        # Check if extension matches known categories
        for category, extensions in self.format_categories.items():
            if extension in extensions:
                return category
        
        # Try to guess from MIME type for files without extensions
        if not extension:
            try:
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type:
                    if mime_type.startswith('image/'):
                        return 'images'
                    elif mime_type.startswith('video/'):
                        return 'videos'
                    elif mime_type.startswith('audio/'):
                        return 'audio'
                    elif mime_type.startswith('text/'):
                        return 'documents'
                    elif mime_type.startswith('application/'):
                        if 'pdf' in mime_type:
                            return 'documents'
                        elif 'zip' in mime_type or 'rar' in mime_type or '7z' in mime_type:
                            return 'archives'
                        else:
                            return 'other'
            except:
                pass
        
        return 'other'
    
    def collect_files_by_formats(self, format_analysis: Dict[str, Dict[str, List[Tuple[str, int, datetime]]]], 
                                selected_formats: List[str]) -> List[Tuple[str, int, datetime]]:
        """Collect files based on selected formats (categories or extensions)"""
        collected_files = []
        
        for category, extensions in format_analysis.items():
            for ext, files in extensions.items():
                # Check if this extension or category is selected
                if ext in selected_formats or category in selected_formats:
                    collected_files.extend(files)
        
        return collected_files

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
    
    def display_downloads_formats(self, format_analysis: Dict[str, Dict[str, List[Tuple[str, int, datetime]]]]):
        """Display Downloads folder format analysis"""
        print("\n" + "="*80)
        print("📁 DOWNLOADS FOLDER FORMAT ANALYSIS")
        print("="*80)
        
        if not format_analysis:
            print("No files found in Downloads folder.")
            return
        
        total_files = 0
        total_size = 0
        
        # Sort categories by total size
        category_sizes = {}
        for category, extensions in format_analysis.items():
            category_size = 0
            category_files = 0
            for ext, files in extensions.items():
                category_size += sum(size for _, size, _ in files)
                category_files += len(files)
            category_sizes[category] = (category_size, category_files)
            total_size += category_size
            total_files += category_files
        
        # Sort by size (largest first)
        sorted_categories = sorted(category_sizes.items(), key=lambda x: x[1][0], reverse=True)
        
        for category, (category_size, category_files) in sorted_categories:
            if category_files == 0:
                continue
                
            print(f"\n📂 {category.upper().replace('_', ' ')}:")
            print(f"   Total: {category_files} files, {self.cleanup_engine.format_size(category_size)}")
            print("   " + "-" * 60)
            
            # Get all extensions for this category
            extensions = format_analysis[category]
            sorted_extensions = sorted(extensions.items(), 
                                     key=lambda x: sum(size for _, size, _ in x[1]), 
                                     reverse=True)
            
            for ext, files in sorted_extensions:
                if not files:
                    continue
                    
                ext_size = sum(size for _, size, _ in files)
                ext_count = len(files)
                
                print(f"   {ext:>8} | {ext_count:>4} files | {self.cleanup_engine.format_size(ext_size):>10}")
                
                # Show sample files for this extension
                if ext_count <= 3:
                    for file_path, size, mtime in files:
                        filename = os.path.basename(file_path)
                        print(f"           • {filename} ({self.cleanup_engine.format_size(size)})")
                else:
                    # Show first 2 and last 1
                    for file_path, size, mtime in files[:2]:
                        filename = os.path.basename(file_path)
                        print(f"           • {filename} ({self.cleanup_engine.format_size(size)})")
                    print(f"           • ... and {ext_count - 3} more files")
                    if files:
                        last_file = files[-1]
                        filename = os.path.basename(last_file[0])
                        print(f"           • {filename} ({self.cleanup_engine.format_size(last_file[1])})")
        
        print(f"\n" + "="*80)
        print(f"📊 SUMMARY: {total_files} files, {self.cleanup_engine.format_size(total_size)} total")
        print("="*80)
    
    def select_downloads_formats(self, format_analysis: Dict[str, Dict[str, List[Tuple[str, int, datetime]]]]) -> List[str]:
        """Interactive Downloads format selection for cleanup"""
        print("\n" + "="*80)
        print("🗑️  SELECT DOWNLOADS FORMATS TO CLEAN")
        print("="*80)
        
        if not format_analysis:
            print("No files found in Downloads folder.")
            return []
        
        # Calculate totals for each category
        category_totals = {}
        for category, extensions in format_analysis.items():
            category_files = []
            category_size = 0
            for ext, files in extensions.items():
                category_files.extend(files)
                category_size += sum(size for _, size, _ in files)
            if category_files:
                category_totals[category] = (category_files, category_size)
        
        # Sort categories by size (largest first)
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1][1], reverse=True)
        
        print("\nAvailable categories:")
        for i, (category, (files, size)) in enumerate(sorted_categories, 1):
            print(f"{i}. {category.upper().replace('_', ' ')} ({len(files)} files, {self.cleanup_engine.format_size(size)})")
        
        print(f"\nOptions:")
        print("• Enter numbers separated by commas (e.g., 1,3,5)")
        print("• Enter 'all' to select all categories")
        print("• Enter 'none' or 'quit' to exit")
        print("• Enter 'formats' to select specific file extensions")
        
        while True:
            try:
                choice = input("\nYour selection: ").strip().lower()
                
                if choice in ['none', 'quit', 'q']:
                    return []
                
                if choice == 'all':
                    return [cat for cat, _ in sorted_categories]
                
                if choice == 'formats':
                    return self.select_specific_formats(format_analysis)
                
                # Parse comma-separated numbers
                selected_indices = []
                for part in choice.split(','):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(sorted_categories):
                            selected_indices.append(idx)
                        else:
                            print(f"Invalid selection: {part}")
                            break
                    else:
                        print(f"Invalid input: {part}")
                        break
                else:
                    # All parts were valid
                    return [sorted_categories[i][0] for i in selected_indices]
                
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return []
            except EOFError:
                print("\nOperation cancelled.")
                return []
    
    def select_specific_formats(self, format_analysis: Dict[str, Dict[str, List[Tuple[str, int, datetime]]]]) -> List[str]:
        """Select specific file extensions for cleanup"""
        print("\n" + "="*80)
        print("📁 SELECT SPECIFIC FILE EXTENSIONS")
        print("="*80)
        
        # Collect all extensions with their info
        all_extensions = []
        for category, extensions in format_analysis.items():
            for ext, files in extensions.items():
                if files:
                    total_size = sum(size for _, size, _ in files)
                    all_extensions.append((ext, len(files), total_size, category))
        
        # Sort by size (largest first)
        all_extensions.sort(key=lambda x: x[2], reverse=True)
        
        print(f"\nFound {len(all_extensions)} different file extensions:")
        for i, (ext, count, size, category) in enumerate(all_extensions, 1):
            print(f"{i:>3}. {ext:>8} | {count:>4} files | {self.cleanup_engine.format_size(size):>10} | {category}")
        
        print(f"\nOptions:")
        print("• Enter numbers separated by commas (e.g., 1,3,5)")
        print("• Enter 'all' to select all extensions")
        print("• Enter 'none' or 'quit' to exit")
        print("• Enter 'category:name' to select all extensions in a category (e.g., 'category:images')")
        
        while True:
            try:
                choice = input("\nYour selection: ").strip().lower()
                
                if choice in ['none', 'quit', 'q']:
                    return []
                
                if choice == 'all':
                    return [ext for ext, _, _, _ in all_extensions]
                
                if choice.startswith('category:'):
                    category_name = choice.split(':', 1)[1].strip()
                    selected_extensions = []
                    for ext, _, _, category in all_extensions:
                        if category == category_name:
                            selected_extensions.append(ext)
                    if selected_extensions:
                        print(f"Selected {len(selected_extensions)} extensions from category '{category_name}'")
                        return selected_extensions
                    else:
                        print(f"No extensions found in category '{category_name}'")
                        continue
                
                # Parse comma-separated numbers
                selected_indices = []
                for part in choice.split(','):
                    part = part.strip()
                    if part.isdigit():
                        idx = int(part) - 1
                        if 0 <= idx < len(all_extensions):
                            selected_indices.append(idx)
                        else:
                            print(f"Invalid selection: {part}")
                            break
                    else:
                        print(f"Invalid input: {part}")
                        break
                else:
                    # All parts were valid
                    return [all_extensions[i][0] for i in selected_indices]
                
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return []
            except EOFError:
                print("\nOperation cancelled.")
                return []

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
    parser.add_argument("--analyze-downloads", action="store_true",
                       help="Analyze file formats in Downloads folder")
    parser.add_argument("--clean-downloads", action="store_true",
                       help="Interactive Downloads cleanup with format selection")
    parser.add_argument("--no-progress", action="store_true",
                       help="Disable progress bars for minimal output")
    
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
    
    # Handle Downloads format analysis
    if args.analyze_downloads:
        print("\nAnalyzing Downloads folder formats...")
        start_time = time.time()
        
        format_analysis = scanner.analyze_downloads_formats(show_progress=not args.no_progress)
        
        scan_time = time.time() - start_time
        if not args.no_progress:
            print(f"Analysis completed in {scan_time:.2f} seconds")
        
        ui.display_downloads_formats(format_analysis)
        return
    
    # Handle Downloads cleanup with format selection
    if args.clean_downloads:
        print("\nAnalyzing Downloads folder for cleanup...")
        start_time = time.time()
        
        format_analysis = scanner.analyze_downloads_formats(show_progress=not args.no_progress)
        
        scan_time = time.time() - start_time
        if not args.no_progress:
            print(f"Analysis completed in {scan_time:.2f} seconds")
        
        if not format_analysis:
            print("No files found in Downloads folder.")
            return
        
        # Show summary first
        ui.display_downloads_formats(format_analysis)
        
        # Interactive format selection
        selected_formats = ui.select_downloads_formats(format_analysis)
        
        if not selected_formats:
            print("No formats selected. Exiting.")
            return
        
        # Collect files based on selection
        selected_files = scanner.collect_files_by_formats(format_analysis, selected_formats)
        
        if not selected_files:
            print("No files found matching your selection.")
            return
        
        # Convert to file paths and calculate total size
        file_paths = [file_path for file_path, _, _ in selected_files]
        total_size = sum(size for _, size, _ in selected_files)
        
        print(f"\nSelected {len(file_paths)} files ({ui.cleanup_engine.format_size(total_size)}) for cleanup")
        
        # Confirm and execute cleanup
        if ui.confirm_cleanup(file_paths, total_size):
            print("\n🧹 Starting Downloads cleanup...")
            start_time = time.time()
            
            files_removed, bytes_freed = ui.cleanup_engine.cleanup_files(file_paths)
            
            cleanup_time = time.time() - start_time
            print(f"\n✅ Downloads cleanup completed in {cleanup_time:.2f} seconds")
            print(f"Files removed: {files_removed}")
            print(f"Space freed: {ui.cleanup_engine.format_size(bytes_freed)}")
            
            if args.dry_run:
                print("\n💡 This was a dry run. No files were actually deleted.")
                print("   Run without --dry-run to perform actual cleanup.")
        else:
            print("Downloads cleanup cancelled.")
        
        return
    
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
                results = scanner.scan_directory(path, args.depth, show_progress=not args.no_progress)
                for category, files in results.items():
                    scan_results[category].extend(files)
    else:
        scan_results = scanner.scan_directory(args.path, args.depth, show_progress=not args.no_progress)
    
    scan_time = time.time() - start_time
    if not args.no_progress:
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