#!/bin/bash -e

# """
# Run `git mergetool` so it always finds the files reported as unmerged (UU)
# by `git status`.
#
# Problem
# -------
# When `.git/MERGE_RR` exists (rerere is enabled and has run at least once
# during the current merge/rebase), `git mergetool` invoked with no path
# arguments takes a shortcut: instead of listing conflicts the normal way
# (same check `git status` uses), it calls `git rerere remaining` and trusts
# that result. If `MERGE_RR` is stale (e.g. left over from an earlier step of
# a multi-commit rebase), `git rerere remaining` can report nothing left to
# do even though `git status` still shows `UU` files. `git mergetool` then
# prints "No files need merging" and exits, even though real conflicts exist.
#
# You cannot fix this with `git config alias.mergetool ...`: git silently
# ignores any alias that hides an existing Git command (documented behavior),
# so an alias named `mergetool` never takes effect.
#
# Solution
# --------
# Pass an explicit pathspec (`.`) to `git mergetool`. Whenever path arguments
# are given, the script skips the `git rerere remaining` shortcut entirely
# and falls back to the same `git diff --name-only --diff-filter=U` check
# `git status` is based on, so the two commands always agree.
# """

source helpers.sh

execute "git mergetool -- . $*"
