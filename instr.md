Extend linters2/lint_cc.py to accept 

1) Execute a skill on selected files
--skill <skill>

Look for the full name of the skill using the same code as

mdm skill f <skill>

mdm skill f coding.fix_inline

Abort if there are more than one possible matches

Otherwise call claude code with a prompt like `/skill <file>`

2) Execute a rule on selected files

--rule <rule_match>

The rule is selected running

> rigrule | grep -i <rule_march>
.claude/skills/readme.rules.md:99:## Inline Commands
.claude/skills/slides.rules.md:154:## Use Inline Verbatim

Abort if there are more than one possible matches

Otherwise call claude code with a prompt like `Execute the rule <rule> on <file>`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`
