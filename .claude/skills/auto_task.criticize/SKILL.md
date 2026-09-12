---
description: Review a plan or GitHub issue for an `auto_task` before execution
model: haiku
---

# Goal
- The user will pass you a file or a GitHub issue number, and you will read carefully
  the content and make sure both the problem and the solution is clear

# Workflow

## Read Context
- Read the content (file or GitHub issue)
- Analyze the problem and the solution, reviewing it carefully

## Create a plan, if needed
- If the task is not perfectly clear:
  - Ask for clarifications
  - Propose changes to the file to clarify

# Conventions
- Follow `.claude/skills/coding.rules.md` when writing code
- Follow `.claude/skills/testing.rules.md` when writing testing code

# Verification
- [ ] The problem statement is clear and unambiguous
- [ ] The proposed solution is clear and unambiguous
- [ ] Any needed clarification was requested before the task moves to execution
