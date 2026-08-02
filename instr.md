1) In cc_lint.py 

`--topic`, `--skill`, `--rule`, and `--mode` are orthogonal now since what to
process and how to process

2) Create unit tests to test `--mode` in all 3 ways (both with fake and with real
workload)

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
