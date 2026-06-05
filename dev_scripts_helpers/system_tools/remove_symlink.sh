#!/bin/bash -e
# """
# Replace symlink with the actual file.
# """

# Check if the user provided a file as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <symlink>"
    exit 1
fi

SYMLINK="$1"

# Check if the provided file is a symbolic link
if [ ! -L "$SYMLINK" ]; then
    echo "Error: $SYMLINK is not a symbolic link."
    exit 1
fi

# Get the real file path
TARGET=$(readlink -f "$SYMLINK")

# Ensure the target file exists
if [ ! -e "$TARGET" ]; then
    echo "Error: Target file $TARGET does not exist."
    exit 1
fi

echo "Replacing symlink: $SYMLINK -> $TARGET"

# Remove the symbolic link
rm "$SYMLINK"

# Copy the actual file to the original symlink location
cp -r "$TARGET" "$SYMLINK"

echo "Symlink replaced successfully."
