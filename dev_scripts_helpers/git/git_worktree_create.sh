#!/bin/bash

# Pass
# feature_name (e.g., HelpersXYZ)
# worktree_path (e.g., /Users/saggese/src/umd_classes4), it should be found automatically
# subrepo_path (look for subrepos and add helpers)
#

gh issue create --title "Fix bug X" --body "Description here" --assignee @me

FEATURE_NAME="HelpersTask"
WORKTREE_PATH="../4-worktree"
SUBREPO_PATH="path/to/subrepo"  # Update this with your subrepo path

# Create branch and worktree in main repo
git branch $FEATURE_NAME
git worktree add $WORKTREE_PATH $FEATURE_NAME

cd $WORKTREE_PATH

# Update submodules
git submodule update --init --recursive

# Create and checkout branch in subrepo
cd $SUBREPO_PATH
git branch $FEATURE_NAME
git checkout $FEATURE_NAME

echo "✓ Worktree and branches created successfully!"
echo "Main repo worktree: $WORKTREE_PATH"
echo "Branch: $FEATURE_NAME (in both repos)"
