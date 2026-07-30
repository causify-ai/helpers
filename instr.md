For pytest_failed_multi_build.py change the status to

Build         | Status              | Passed | Skipped | Failed | Total | Duration |
------------- | ------------------- | ------ | ------- | ------ | ----- | -------- |
docker        | INCOMPLETE | 0      | 0       | 0      | 0     | N/A      |
apple         | FAIL       | 3508   | 236     | 1      | 3745  | 576.53s  |
dev_container | PASS       | 632    | 12      | 0      | 644   | Nones    |

- NOT STARTED (gray) if Total is 0 and there was no pytest file
- IN PROGRESS (blue) if there was no pytest ending marker and total > 0

Add more space for status to fit the status

Add unit tests

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
