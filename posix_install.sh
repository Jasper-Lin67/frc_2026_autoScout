#!/usr/bin/env bash

echo "[1/2] Detecting Environment and Package Manager..."

# Function to install on Nix
install_nix() {
    echo "Nix detected. Installing Python 3.12 and Tkinter..."
    # nix-env is the standard for imperative installs on Nix
    nix-env -iA nixpkgs.python312 nixpkgs.python312Packages.tkinter
}

# Check for Nix first, as it can exist on top of other distros
if command -v nix-env >/dev/null 2>&1; then
    install_nix
elif [ "$OSTYPE" == "darwin"* ]; then
    echo "macOS detected. Using Homebrew..."
    brew install python@3.12
elif command -v apt-get >/dev/null 2>&1; then
    echo "Debian/Ubuntu detected. Installing de-bundled components..."
    sudo apt-get update
    sudo apt-get install -y python3.12 python3.12-tk python3.12-venv python3.12-dev
elif command -v dnf >/dev/null 2>&1; then
    echo "Fedora/RHEL detected..."
    sudo dnf install -y python3.12-devel python3.12-tkinter
elif command -v pacman >/dev/null 2>&1; then
    echo "Arch Linux detected..."
    sudo pacman -S --noconfirm python tk
else
    echo "[ERROR] Unsupported package manager. Please install Python 3.12, Tkinter, and Dev headers manually."
    exit 1
fi

echo "[2/2] System dependency check complete."