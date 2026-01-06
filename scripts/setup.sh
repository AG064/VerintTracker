#!/bin/bash
# Quick setup script for Verint Tracker

echo "======================================"
echo "Verint Tracker - Setup Script"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.7 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is available
echo "Checking pip for Python 3..."
if ! python3 -m pip --version &> /dev/null; then
    echo "Error: pip for Python 3 is not installed or not available."
    echo "Please install pip for Python 3 (e.g., 'python3 -m ensurepip --upgrade' or via your package manager)."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies."
    exit 1
fi

echo ""
echo "Installing Microsoft Edge browser driver..."
python3 -m playwright install msedge

if [ $? -ne 0 ]; then
    echo "Warning: Failed to install Edge driver."
    echo "You may need to install it manually."
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Run the verification test:"
echo "  python3 test_setup.py"
echo ""
echo "Start the tracker:"
echo "  python3 app.py"
echo ""

