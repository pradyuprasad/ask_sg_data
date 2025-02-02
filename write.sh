#!/bin/bash

# Check if a directory is provided, otherwise use current directory
DIR="${1:-.}"

# Find all .py files recursively, excluding dot directories
find "$DIR" -type f -name "*.py" -not -path '*/\.*' | while read -r file; do
    # Print a header with the full file path
    echo "==================== START FILE: $file ===================="

    # Use cat to display file contents
    cat "$file"

    # Print a footer
    echo -e "\n==================== END FILE: $file ====================\n"
done
