# 🧹 MacSweep - The Ultimate macOS File Cleanup Wizard

A powerful and intelligent command-line utility for finding and cleaning unnecessary files on macOS systems. MacSweep transforms your cluttered Mac into a clean, organized workspace with its smart detection algorithms and safe cleanup operations.

## ✨ Features

- 🔍 **Smart File Detection**: Automatically identifies different types of files that can be safely cleaned
- 🗂️ **Multiple Categories**: Organizes files into logical categories (cache, logs, backups, etc.)
- 📊 **Size Analysis**: Shows file counts and disk space usage for each category
- 🎯 **Interactive Selection**: Choose which categories to clean with an intuitive interface
- 🔒 **Safe Operations**: Dry-run mode lets you preview changes before applying them
- ⚡ **Fast Scanning**: Efficient directory traversal with configurable depth limits
- 🎨 **Clean Output**: Well-formatted terminal output with progress indicators

## Categories Detected

- **Cache Files**: `.cache`, `.tmp`, `.DS_Store`, temporary files
- **Log Files**: `.log`, `.out`, `.err` files
- **Backup Files**: `.bak`, `.backup`, `.old`, `.orig` files
- **Downloads**: Files in Downloads folder
- **Trash**: Files in Trash/trash folders
- **Development**: `node_modules`, `.git`, `__pycache__`, `.venv`, etc.
- **System**: macOS Library caches and logs
- **Browser**: Safari, Chrome, Firefox cache and data
- **Large Files**: Files over 100MB
- **Old Files**: Files older than 30 days

## Installation

1. **Clone or download** the script:
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd macsweep
   
   # Or download just the script file
   wget https://raw.githubusercontent.com/your-repo/macsweep/main/macsweep.py
   ```

2. **Make the script executable**:
   ```bash
   chmod +x macsweep.py
   ```

3. **Run the script**:
   ```bash
   python3 macsweep.py
   ```

## Usage

### Basic Usage

 ```bash
 # Scan your home directory
 python3 macsweep.py
 
 # Scan a specific directory
 python3 macsweep.py /path/to/directory
 
 # Dry run mode (preview only, no actual deletion)
 python3 macsweep.py --dry-run
 
 # Quick scan (common locations only)
 python3 macsweep.py --quick
 ```

### Command Line Options

 ```bash
 python3 macsweep.py [OPTIONS] [PATH]

Arguments:
  PATH                    Path to scan (default: home directory)

Options:
  --dry-run              Show what would be deleted without actually deleting
  --verbose, -v          Show detailed output during cleanup
  --depth N              Maximum scan depth (default: 3)
  --quick               Quick scan (common locations only)
  --help                Show help message
```

### Examples

 #### 1. Safe Preview Run
 ```bash
 python3 macsweep.py --dry-run
 ```
This will show you what files would be deleted without actually deleting them.

 #### 2. Scan Downloads Folder
 ```bash
 python3 macsweep.py ~/Downloads
 ```
Scan only the Downloads folder for cleanup candidates.

 #### 3. Quick System Clean
 ```bash
 python3 macsweep.py --quick --verbose
 ```
Perform a quick scan of common system locations with detailed output.

 #### 4. Deep Scan with Higher Depth
 ```bash
 python3 macsweep.py --depth 5 ~/Documents
 ```
Scan Documents folder with increased depth limit.

## Interactive Usage

When you run the script, you'll see:

1. **Scanning Phase**: The tool scans your selected directory
2. **Results Summary**: Shows categories found with file counts and sizes
3. **Category Selection**: Choose which categories to clean
4. **Confirmation**: Preview files to be deleted and confirm the operation
5. **Cleanup**: Files are safely removed with progress feedback

### Selection Options

- Enter numbers separated by commas: `1,3,5`
- Enter `all` to select all categories
- Enter `none` or `quit` to exit
- Use `Ctrl+C` to cancel at any time

## Safety Features

- **Dry Run Mode**: Preview changes without making them
- **Confirmation Prompts**: Always asks before deleting files
- **Safe Categorization**: Only suggests files that are typically safe to delete
- **Error Handling**: Gracefully handles permission errors and missing files
- **Detailed Logging**: Shows exactly what was deleted (in verbose mode)

## System Requirements

- **macOS**: Designed specifically for macOS file structure
- **Python 3.6+**: Uses only standard library modules
- **Permissions**: Some system directories may require admin access

## What Gets Cleaned

### Safe to Clean
- Cache files and temporary files
- Log files and crash reports
- Backup files (`.bak`, `.old`, etc.)
- Browser cache and temporary internet files
- Development artifacts (`node_modules`, `__pycache__`, etc.)
- Old downloads (you'll see the list before deletion)

### Never Touched
- System critical files
- User documents and personal files
- Application binaries
- Configuration files you've customized
- Files in use by running applications

 ## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve MacSweep!

 ## 📄 License

This project is open source and available under the [MIT License](LICENSE).

 ## ⚠️ Disclaimer

While MacSweep is designed to be safe, always:
- Run with `--dry-run` first to preview changes
- Back up important data before running cleanup tools
- Review the file list before confirming deletion
- Use at your own risk

 The authors are not responsible for any data loss resulting from the use of MacSweep. 