In linters2/lint_cc.py replace _find_rule with a call
hmarsele.extract_rule_from_file(rule)
and update the documentation

In extract_rule_from_file if the format doesn't match any allowed format 
call rigrule

rigrule dassert

make sure there is a single match and then use the resulting single match

E.g.,
.claude/skills/testing.rules.md:657:## Do Not Use `hdbg.dassert` to Test Assertions

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
