---
description: Fix slide formatting: semantic tags, bold, LaTeX, punctuation, unicode, emoji
model: haiku
---

# Goal
- Given a markdown file with slides, fix formatting issues and add missing
  semantic tags, bold, and italic markup, without changing the content or
  structure
- Read `.claude/skills/slides.rules.md` and apply the formatting rules strictly

# Workflow

## Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`

## What to Fix

- **Semantic tags and bold labels**: Ensure every first-level bullet starts
  with an approved `@Tag@` label
  - See `slides.rules.md` → `# Slide Organization` → `## Use Tags for Slide
    Sections` for the approved tag list and ordering
  - Add a missing tag when a first-level bullet has none; do not invent a tag
    outside the approved list

- **Bold and italic emphasis**: Apply `**bold**` and `_italic_` where the
  rules call for them
  - See `slides.rules.md` → `# Slide Organization` → `## Use Bold` and
    `## Use Italic`
  - When both apply to the same phrase, bold takes precedence: see
    `slides.rules.md` → `### Emphasis Precedence: Bold Over Italic`

- **Unicode characters**: Replace non-ASCII characters with LaTeX equivalents
  - See `slides.rules.md` → `# Slide Organization` → `## General Formatting
    Rules` and `### Symbols and Characters`

- **Emoji**: Remove emoji characters per `slides.rules.md` → `# Slide
  Organization` → `## General Formatting Rules`

- **Page separators**: Remove `---` lines per `slides.rules.md` → `# Slide
  Organization` → `## General Formatting Rules` and `### Spacing and Breaks`

- **Punctuation**: Remove trailing periods from bullet point phrases per
  `slides.rules.md` → `# Slide Organization` → `## Slide Structure`

## Leave Structure and Content Unchanged
- Do not change the structure of the text (titles, bullet hierarchy, div
  fenced blocks)
- Do not change the substantive content: change only formatting

## Output
- Emit the improved output in markdown, wrapped to 80 columns (see
  `slides.rules.md` → `## Use 80 columns`), without any other comment
