Split ./dev_scripts_helpers/llms/llm_cli.py into a lib_llm_cli.py
with the library functions, leaving only _main and _parse in
llm_cli.py so that there is a clear separation between CLI
and code implementing it

Split the code in ./dev_scripts_helpers/llms/test/test_llm_cli.py
to follow the conventions, testing lib vs CLI

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
