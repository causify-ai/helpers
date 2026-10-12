---
description: Format a research idea file to follow the standard template
model: sonnet
---

# Goal
- Given a file `<FILE>` with raw information about a research idea, apply the
  research idea template and write the result back into `<FILE>`

# Workflow

## Read the Inputs
- Read `<FILE>`
- Read the template `.claude/templates/research_idea.template.md`
- Read `.claude/skills/research_idea.rules.md` `# Examples` for a worked
  example

## Apply the Template
- Map the content already in `<FILE>` onto the template's sections (`Status`,
  `Core Idea`, `Formalization`, `Key Examples`, `Questions`, `Research
  Topics`, `Next steps`, `Implementation plan`, `References`)
- Do not leave the template's placeholder bullets in a section: fill it from the
  idea's own content, or remove the empty bullets
- Do not invent facts, results, or citations to fill a section; write only what
  follows from the idea (e.g., a hypothetical example marked as illustrative)
- Do not add an `Assignee` field: assignees live only in the README table
- Write references as `Author(s), _Title_. (Year)`
- Write the result back into `<FILE>`, replacing its previous content

# Conventions
- Follow `.claude/skills/research_idea.rules.md`

# Constraints
- Keep the file name and its status prefix unchanged; formatting does not
  change status
- Fit text in 85 character lines, per `.claude/skills/research_idea.rules.md`

# Examples
- `research/ideas/in_progress.RL_for_pickleball.md`

# Verification
- [ ] `<FILE>` follows the section order of `.claude/templates/research_idea.template.md`
- [ ] No template placeholder text is left in the file
- [ ] No fabricated facts or citations were added
- [ ] No `Assignee` line; references use `Author(s), _Title_. (Year)`
- [ ] Lines fit in 85 characters
