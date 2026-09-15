#!/bin/bash -e

# """
# Print which side is "ours" and which is "theirs" for the git operation
# currently in progress (merge, rebase, cherry-pick, or revert).
#
# "Ours" / "theirs" flip meaning between merge and rebase:
# - merge: ours = current branch, theirs = branch being merged in
# - rebase: ours = onto target, theirs = original branch being replayed
# """

source helpers.sh

print_commit() {
  # """
  # Print the short hash and subject line for a git ref.

  # :param ref: git ref (branch, hash, HEAD, etc.)
  # """
  local ref=$1
  local hash
  hash=$(git rev-parse --short "$ref" 2>/dev/null) || {
    echo "    (could not resolve $ref)"
    return
  }
  local subject
  subject=$(git log -1 --format='%s' "$ref" 2>/dev/null) || subject=""
  echo "    $hash  $subject"
}

resolve_branch_name() {
  # """
  # Best-effort: turn a hash/ref into a branch name, if one points at it.

  # :param ref: git ref (branch, hash, HEAD, etc.)
  # """
  local ref=$1
  git name-rev --name-only --exclude='tags/*' "$ref" 2>/dev/null || echo "$ref"
}

GIT_DIR=$(git rev-parse --git-dir)

if [ -f "$GIT_DIR/MERGE_HEAD" ]; then
  echo "Operation: merge"
  ours_branch=$(git symbolic-ref --short HEAD 2>/dev/null) || ours_branch="HEAD (detached)"
  theirs_ref=$(cat "$GIT_DIR/MERGE_HEAD")
  echo "OURS   = $ours_branch (your current branch)"
  print_commit HEAD
  echo "THEIRS = $(resolve_branch_name "$theirs_ref") (branch being merged in)"
  print_commit "$theirs_ref"
elif [ -d "$GIT_DIR/rebase-merge" ] || [ -d "$GIT_DIR/rebase-apply" ]; then
  echo "Operation: rebase"
  rebase_dir="$GIT_DIR/rebase-merge"
  [ -d "$rebase_dir" ] || rebase_dir="$GIT_DIR/rebase-apply"
  onto=$(cat "$rebase_dir/onto" 2>/dev/null) || onto=""
  orig_branch=$(cat "$rebase_dir/head-name" 2>/dev/null | sed 's#refs/heads/##')
  echo "OURS   = onto target: $(resolve_branch_name "$onto") (where you are replaying commits)"
  if [ -n "$onto" ]; then
    print_commit "$onto"
  fi
  echo "THEIRS = your original branch: $orig_branch (commit being replayed now)"
  if [ -f "$GIT_DIR/REBASE_HEAD" ]; then
    print_commit "$(cat "$GIT_DIR/REBASE_HEAD")"
  elif [ -f "$rebase_dir/stopped-sha" ]; then
    print_commit "$(cat "$rebase_dir/stopped-sha")"
  fi
elif [ -f "$GIT_DIR/CHERRY_PICK_HEAD" ]; then
  echo "Operation: cherry-pick"
  echo "OURS   = current branch"
  print_commit HEAD
  echo "THEIRS = cherry-picked commit"
  print_commit "$(cat "$GIT_DIR/CHERRY_PICK_HEAD")"
elif [ -f "$GIT_DIR/REVERT_HEAD" ]; then
  echo "Operation: revert"
  echo "OURS   = current branch"
  print_commit HEAD
  echo "THEIRS = commit being reverted"
  print_commit "$(cat "$GIT_DIR/REVERT_HEAD")"
else
  echo "No merge/rebase/cherry-pick/revert in progress."
  exit 0
fi

echo
echo "Unmerged files:"
execute "git diff --name-only --diff-filter=U"
