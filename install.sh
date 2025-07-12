#!/bin/bash

# MacSweep Installation Script
# The Ultimate macOS File Cleanup Wizard

echo "🧹 Welcome to MacSweep - The Ultimate macOS File Cleanup Wizard!"
echo "================================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Make the script executable
chmod +x macsweep.py

# Create a symlink to make it globally accessible (optional)
read -p "Would you like to install MacSweep globally? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if /usr/local/bin exists and is writable
    if [ -w /usr/local/bin ]; then
        ln -sf "$(pwd)/macsweep.py" /usr/local/bin/macsweep
        echo "✅ MacSweep installed globally! You can now run 'macsweep' from anywhere."
    else
        echo "⚠️  Cannot write to /usr/local/bin. Trying with sudo..."
        sudo ln -sf "$(pwd)/macsweep.py" /usr/local/bin/macsweep
        echo "✅ MacSweep installed globally! You can now run 'macsweep' from anywhere."
    fi
else
    echo "ℹ️  MacSweep is ready to use! Run it with: python3 macsweep.py"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Quick start:"
echo "  python3 macsweep.py --dry-run    # Safe preview mode"
echo "  python3 macsweep.py --quick      # Quick scan"
echo "  python3 macsweep.py --help       # Show all options"
echo ""
echo "Happy cleaning! 🧹✨" 