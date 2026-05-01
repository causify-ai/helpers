#!/bin/bash
# Example workflow: download a podcast transcript and format it

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Podcast Download & Format Workflow${NC}"
echo "===================================="

# Example 1: Lex Fridman
echo -e "\n${BLUE}Example 1: Downloading Lex Fridman episode${NC}"
./podcast_dl.py --type lexfriedman --title lars-brownworth --output_dir ./example_transcripts

echo -e "${GREEN}✓ Downloaded Lex Fridman transcript${NC}"

# Format the transcript
TRANSCRIPT=$(ls -t example_transcripts/*.txt | head -1)
echo -e "\n${BLUE}Formatting transcript: $TRANSCRIPT${NC}"
./transcript_formatter.py \
    --transcript "$TRANSCRIPT" \
    --url "https://lexfridman.com/lars-brownworth-transcript" \
    --output "./example_transcripts/lars-brownworth.md"

echo -e "${GREEN}✓ Formatted as: ./example_transcripts/lars-brownworth.md${NC}"

# Example 2: Dwarkesh
echo -e "\n${BLUE}Example 2: Downloading Dwarkesh episode${NC}"
./podcast_dl.py --type dwarkesh --title andrej-karpathy --output_dir ./example_transcripts

echo -e "${GREEN}✓ Downloaded Dwarkesh transcript${NC}"

TRANSCRIPT=$(ls -t example_transcripts/unknown-date_dwarkesh*.txt | head -1)
echo -e "\n${BLUE}Formatting transcript: $TRANSCRIPT${NC}"
./transcript_formatter.py \
    --transcript "$TRANSCRIPT" \
    --url "https://www.dwarkesh.com/p/andrej-karpathy" \
    --output "./example_transcripts/andrej-karpathy.md"

echo -e "${GREEN}✓ Formatted as: ./example_transcripts/andrej-karpathy.md${NC}"

echo -e "\n${GREEN}Workflow complete!${NC}"
echo "Check ./example_transcripts/ for formatted markdown files"
