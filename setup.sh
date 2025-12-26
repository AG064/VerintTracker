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

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies."
    exit 1
fi

echo ""
echo "Installing Microsoft Edge browser driver..."
playwright install msedge

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
echo "  python3 verint_tracker.py"
echo ""
