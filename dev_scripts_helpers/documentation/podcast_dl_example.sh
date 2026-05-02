#!/bin/bash -xe

podcast_dl.py --type lexfridman --title lars-brownworth --output ./transcript1.md

podcast_dl.py --type dwarkesh --title andrej-karpathy --output ./transcript2.md

podcast_dl.py --type podscripts_co --title "no-priors-artificial-intelligence-technology-startups/andrej-karpathy-on-code-agents-autoresearch-and-the-loopy-era-of-ai" --output ./transcript3.md

# podcast_dl.py --type podcasttranscript_ai --title andrej-karpathy-s-vision-of-software --output ./transcript3.md
