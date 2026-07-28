Extend 
.claude/control_cc_commit.py --enable
to remove all the lines in deny including "git commit" or "git push"
and save what's remove in a backup file

.claude/settings.local.json

-> 

.claude/settings.local.json.backup

For --disable use the content in .claude/settings.local.json.backup
and copy it to .claude/settings.local.json

Add a unit test to make sure that the round trip works

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
