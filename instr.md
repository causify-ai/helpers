Change use_llm_executable to "backend" become mode with 3 values
- "executable" which is equivalent to use_llm_executable = True
- "library" which is equivalent to use_llm_executable = False
- "mock" which replaces a call to the LLM by implementing something like
  _mock_apply_llm

Replace the --use_llm_executable with --backend

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
