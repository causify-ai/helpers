---
description: Make the code more readable and debuggable
model: haiku
---

# Goal
The user will pass you one of more files `<FILES>` and you will make the code
more readable and debuggable for humans.

# Workflow

## Add Comments
- Improve code readability by adding concise comments.
- Follow the section `# Comments` from the file `.claude/skills/coding.rules.md`

## Add Debug Logging for Function Entry, Execution, and Results
- Track function execution by adding `_LOG.debug` statements.
- Follow the section `# Logging` from the file `.claude/skills/coding.rules.md`

## Conventions
- Do not change the behavior of the code in any way
- You must follow the rules in `.claude/skills/coding.rules.md`
