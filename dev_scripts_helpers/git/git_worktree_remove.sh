# From the main repo (not the worktree)
git worktree remove ../my-feature-worktree

# Delete the branches
git branch -d my-feature
cd path/to/subrepo
git branch -d my-feature
