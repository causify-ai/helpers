---
description: Format a research idea file to follow the standard template
model: sonnet
---

# Goal
- Given a file `<FILE>` with raw information about a research idea, apply the
  research idea template and write the result back into `<FILE>`

# Workflow

## Step 1: Read the Inputs
- Read `<FILE>`
- Read the template `research/ideas/template.research_idea.md`
- Read `.claude/skills/research_idea.rules.md` `# Examples` for a worked
  example

## Step 2: Apply the Template
- Map the content already in `<FILE>` onto the template's sections (`Status`,
  `Core Idea`, `Formalization`, `Key Examples`, `Questions`, `Research
  Topics`, `Next steps`, `Implementation plan`, `References`)
- Do not fabricate content for a section the input does not support; leave the
  template's placeholder bullets for that section instead
- Write the result back into `<FILE>`, replacing its previous content

# Conventions
- Follow `.claude/skills/research_idea.rules.md`

# Constraints
- Keep the file name and its status prefix unchanged; formatting does not
  change status
- Fit text in 80-90 character lines, per `.claude/skills/research_idea.rules.md`

# Examples
- `research/ideas/in_progress.RL_for_pickleball.md`

# Verification
- [ ] `<FILE>` follows the section order of `research/ideas/template.research_idea.md`
- [ ] No fabricated content was added for sections the input did not cover
- [ ] Lines fit in 80-90 characters
