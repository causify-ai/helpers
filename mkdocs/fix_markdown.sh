#!/bin/bash -e
# Usage: ./fix_markdown.sh <file.md>
# Cleans smart quotes, weird Unicode artifacts, and replacement chars.

if [ $# -eq 0 ]; then
    echo "Usage: $0 <file.md>"
    exit 1
fi

file="$1"

if [ ! -f "$file" ]; then
    echo "Error: File '$file' not found"
    exit 1
fi

echo "Processing $file..."

# Ensure UTF-8 and normalize line endings.
#iconv -f utf-8 -t utf-8 -c "$file" -o "$file.tmp" && mv "$file.tmp" "$file"

# Fix common malformed sequences first.
perl -pi -e 's/"\x27/\x27/g' "$file" 
perl -pi -e 's/""/"/g' "$file"       

# Replace curly quotes with straight quotes
perl -pi -e 's/[\x{201C}\x{201D}]/"/g' "$file"
perl -pi -e 's/[\x{2018}\x{2019}]/\x27/g' "$file"

# Replace em/en dashes with normal hyphen.
perl -pi -e 's/[–—]/-/g' "$file"

# Remove Unicode replacement characters (�) and stray byte sequences.
perl -pi -e 's/�//g' "$file"

# Fix doubled/tripled quotes like """, ""', or ""�.
perl -pi -e 's/""+/"/g' "$file"
perl -pi -e 's/\x27+/\x27/g' "$file"

# Remove any leftover weird artifacts (common encoding garbage).
perl -pi -e 's/[\xC2\xA0]/ /g' "$file"  

# Fix common spacing issues around quotes.
perl -pi -e 's/" +([a-z])/" $1/g' "$file"  
perl -pi -e 's/([a-z]) +"/$1"/g' "$file"   

echo "Cleaned $file"
