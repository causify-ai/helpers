Extend `invoke gh_issue_create` to accept a --gh_issue_body_file 

Extend `invoke git_branch_create` to accept a --pr-ready to make
the created PR ready for review

Extend dev_scripts_helpers/git/git_create_issue_and_branch.py to accept 

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm
