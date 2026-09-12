# Given the target branch (e.g., origin/gp, origin/master) $TARGET
# Find files added and modified in this branch 
git diff --name-only --diff-filter=d $TARGET

# Find the files deleted.

# Compress the files added and modified.
tar czf diff_vs_origin_gp.tar.gz -T files.txt

tar xvzf diff_vs_origin_gp.tar.gz
