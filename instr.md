Create a script in ./dev_scripts_helpers/git/create_git_worktree.py
that accepts

--gh_issue_title <title>
--gh_issue_body_file <body_file>
--gh_assignee <assignee> (@me by default)
--instr_file optional

that performs the following actions

  > gh issue create --title <title> --body-file <body_file> --assignee <assignee>

Get the issue number and the title

> i gh_issue_title -i 1290

Create branch and worktree
git branch $FEATURE_NAME master
> git worktree add $WORKTREE_PATH $FEATURE_NAME

Print the instructions on how to go in that 
> cd $WORKTREE_PATH
> dev_scripts_helpers/thin_client/tmux.py --index 1290

- Test using end-to-end with `## Use the Mocking Infrastructure`
	from `.claude/skills/testing.rules.md`

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

# Create a plan, if needed
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
