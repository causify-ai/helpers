Write a skill to .claude/skills/coding.write_doc/SKILL.md about documenting
code

The user passes a file <file>

The skill needs to create a new file README.<file>.md or update it
if already exists

Follow .claude/skill.rules.md

Have a short description of what the goal is

What are the main functions and how the call each other

# Short description

# 
Use C4 diagrams to document architecture

Add a section about critique and improvement the architecture

* Use Markdown.
* Organize content by C4 levels.
* Include Mermaid diagrams where possible.
* Reference actual code artifacts when available.
* Distinguish facts derived from code from assumptions.
* Focus on maintainability, extensibility, and operational understanding.

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
