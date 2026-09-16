#!/bin/bash -xe
vimdiff .claude/settings.json ~/.claude/settings.json 
vimdiff .claude/settings.json .claude/settings.local.json
vimdiff .claude/hooks/check_git_auth.sh ~/.claude/hooks/check_git_auth.sh
vimdiff CLAUDE.md ~/.claude/CLAUDE.md
