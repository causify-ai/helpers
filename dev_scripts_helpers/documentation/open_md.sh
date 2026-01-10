#!/bin/bash
#
# Render a markdown using Pandoc and then open it in a browser.
#

# Check if a file name is passed as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

# The filename is expected to be the first argument
filename="$1"

# Check if the file exists
if [ ! -f "$filename" ]; then
    echo "Error: File '$filename' not found."
    exit 1
fi

# Process the file (you can replace the following line with your processing code)
echo "Processing file: $filename"

# render_images.py -i $filename

# Get the directory and basename of the input file
file_dir=$(dirname "$filename")
file_base=$(basename "$filename" .md)

# Create destination filename in the same directory as input
#dst_filename="${file_dir}/${file_base}.rendered.html"
dst_filename="${file_dir}/${file_base}.rendered.pdf"

pandoc $filename \
  -o $dst_filename \
    --resource-path=$file_dir \
  --pdf-engine=xelatex \
  -V papersize=A4 \
  -V fontsize=11pt \
  -V geometry:margin=1in \
  -V linestretch=1.15 \
  -V mainfont="Helvetica Neue"

echo "Saved to $dst_filename"
open $dst_filename
