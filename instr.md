From each issue plan.todo_janitor.md

- Create a GitHub issue in a certain repo
  gh issue create --title "Fix bug X" --body "Description here" --assignee @me
  --title <title>
  --body <file>

gh issue create --title "Refactor Regex to Use re.VERBOSE and Comments" --body-file ...

or i gh_issue_title
GitHub issue link: https://github.com/causify-ai/helpers/issues/1290

- Get the name of the issue
i gh_issue_title -i 1290
HelpersTask1290_Refactor_Regex_to_Use_re.VERBOSE_and_Comments

- Create a branch and a worktree

```
#!/bin/bash

# Pass
# feature_name (e.g., HelpersXYZ)
# worktree_path (e.g., /Users/saggese/src/umd_classes4), it should be found automatically
# subrepo_path (look for subrepos and add helpers)

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
```


# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`
- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
