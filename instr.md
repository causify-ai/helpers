Create a function mock_apply_llm in llm_cli that allows to mock apply_llm and
returns the digest of concatenation of the strings input_str and system_prompt

This function should be usable with a with mock_apply_llm():

by tests to avoid to call llm

Add a short explanation of how to use this idiom

Use this new function in dev_scripts_helpers/llms/test/test_llm_cli.py

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- When implementing notebooks follow the instructions in
  - `.claude/skills/notebook.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
