In invoke git_branch_create also create an empty draft PR associated with that branch
add an option to not create the PR

In dev_scripts_helpers/git/create_git_worktree.py
replace creating a branch with git to using the invoke git_branch_create

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - Create a plan `plan.md` with 5 bullet points explaining what the plan is
  - Wait for the user to confirm
