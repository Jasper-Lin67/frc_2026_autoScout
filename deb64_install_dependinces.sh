#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Checking dependencies..."

# 1. Check for Tkinter (requires sudo if missing)
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "Tkinter not found. Installing system dependency (may require password)..."
    sudo apt update && sudo apt install -y python3-tk python3-venv
fi

# 2. Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate and install pip requirements
source .venv/bin/activate
echo "Updating pip and installing requirements..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# 4. Launch the GUI
echo "Launching dev_gui.py..."
python3 dev_gui.py

deactivate
