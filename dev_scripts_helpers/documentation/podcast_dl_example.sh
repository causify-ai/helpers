#!/bin/bash -xe

# Download and format a Lex Fridman episode (default action).
podcast_dl.py -a all --type lexfriedman --title lars-brownworth --output_dir ./transcripts1

# Download and format a Dwarkesh episode.
podcast_dl.py -a all --type dwarkesh --title andrej-karpathy --output_dir ./transcripts2

# Download only from PodcastTranscript.ai.
podcast_dl.py -a all --type podcasttranscript_ai --title andrej-karpathy-s-vision-of-software --output_dir ./transcripts3

# Format a transcript that was previously downloaded.
podcast_dl.py -a all --type podscripts_co --title andrej-karpathy-on-code-agents-autoresearch-and-the-loopy-era-of-ai --output_dir ./transcripts4
