#!/bin/bash

TARGET_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "WARNING: This will permanently delete everything in:"
echo "$TARGET_DIR"
read -p "Are you sure? (y/n): " confirm

if [[ $confirm == [yY] ]]; then
    echo "Uninstalling..."
    # Move to temp directory so we can delete the folder
    cd /tmp
    # Run deletion in the background and exit immediately
    (sleep 1; rm -rf "$TARGET_DIR") &
    echo "Project removed."
    exit
else
    echo "Uninstallation cancelled."
fi
