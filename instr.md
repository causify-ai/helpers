- In linters2/fix_comments.py add directives to enable / disable the check
  # lint: disable=fix_comments

  # lint: enable=fix_comments

  Update the unit tests to use those directives around the unit tests that would
  be otherwise changed by linters2/fix_comments.py

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
