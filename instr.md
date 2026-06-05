In

./helpers/hcache_simple.py

Apply these changes

.claude/skills/coding.rules.md:848 ## Use Single Types With Meaningful Defaults for Parser Inputs
.claude/skills/coding.rules.md:584 ## Minimize Default Values of None in Function Interfaces

The goal is to replace in the functions
Optional[str] = None with str = ""
and Optional[int] with a suitable default int = XYZ

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
