---
description: Improve the slides adding tags and formatting to highlight certain words
model: haiku
---

# Goal
- Review the content of the file with slides `<FILE>` and add semantic tags (e.g.,
  `@Definition@), bold or italic

# Workflow

## Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`

## Read the Input
- Read the user's material

## Rewrite the Content
- Rewrite the content following the instructions in the sections from
  `.claude/skills/slides.rules.md`:
  - `## Use Tags for Slide Sections`
  - `## Use Bold`
  - `## Use Italic`

## Output
- Emit the improved output in markdown code (wrapped in 80 columns) without any
  other comment
