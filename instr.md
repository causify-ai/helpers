1) When running `mdm skill l skill` the output is garbled

```
skills
skills
skills
skills
skills
skills
skills
skills
skills
skills
skills
skills
skills
skill.add
skill.improve_text
skill.move_to_rules
skill.reorganize_rules
skills
skills
skills
skills
skills
skills
```

Find out why and fix it

2) -v DEBUG doesn't work for mdm. Maybe because the logger sets the verbosity
  for the current file instead of setting it for the librig.py
- Fix it

- Find the root cause and propose a solution

- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
