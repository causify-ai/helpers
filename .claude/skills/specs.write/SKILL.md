---
description: Write specification to implement a software component given user request
model: opus
---

- Create a markdown document describing the specs to implement in Python the
  requested functionality
  - Save the result in a file `plan.<topic>.md` in the current directory
  - Follow the rules in `.claude/skills/markdown.rules.md`
  - Follow the template `.claude/templates/specs.template.md`

- Do not implement any code, only describe the architecture

# Step 1
- Understand the context:
  - Read related code in the codebase
  - Read existing code in the target directory
  - Read `.claude/skills/architecture.rules.md` about how we organize the architecture
    of software
  - Read the coding and unit test conventions in `.claude/skills/coding.rules.md`
    and `.claude/skills/testing.rules.md`

# Step 2

- Update an architecture file, if it exists, following the instructions in
  `.claude/skills/readme.write_architecture/SKILL.md`
  - Do not add too much details only what matters to understand how the pieces
    work together and not how the new component works
