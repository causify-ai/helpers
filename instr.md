In hunit_test.py when printng `The golden outcome doesn't exist` perform a git
add creating a function in hgit.py that finds the right directory including the
subrepo that that file belongs to, cd in that dir and perform the `git add` 
after doing the difference of the paths

Also print to screen, the files that are updated or created

Add unit tests for these functionalities

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

