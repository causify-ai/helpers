#!/bin/bash -xe
# """
# Diff each repo-scoped file (`.claude/...`) against its global counterpart
# (`~/.claude/...`) to keep the two locations organized.
#
# Convention:
# - The global file holds settings and instructions that apply to every repo
# - The repo file holds only what is specific to this repo. Move generic
#   content found in a repo file up to the global file, and move repo-specific
#   content out of the global file and down into the repo file.
# """
vimdiff .claude/settings.json ~/.claude/settings.json
vimdiff .claude/settings.json .claude/settings.local.json
vimdiff .claude/hooks/check_git_auth.sh ~/.claude/hooks/check_git_auth.sh
vimdiff CLAUDE.md ~/.claude/CLAUDE.md
