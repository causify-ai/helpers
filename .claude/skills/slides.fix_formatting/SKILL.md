---
description: Fix formatting conventions in slides (bold labels, LaTeX, punctuation, unicode, emoji)
model: haiku
---

# Goal
- Given a markdown file with slides, fix formatting issues without changing the
  content or structure
- Read `.claude/skills/slides.rules.md` and apply the formatting rules strictly

## What to Fix

- **Bold labels**: Ensure every first-level bullet starts with an approved bold
  label
  - See `slides.rules.md` → `# Slide Organization` → `## Use Bold for Slide
    Sections` for the approved list

- **Unicode characters**: Replace non-ASCII characters with LaTeX equivalents.
  - See `slides.rules.md` → `# Slide Organization` → `## General Formatting
    Rules` and `### Symbols and Characters`.

- **Emoji**: Remove emoji characters per `slides.rules.md` → `# Slide Organization`
  → `## General Formatting Rules`.

- **Page separators**: Remove `---` lines per `slides.rules.md` → `# Slide Organization`
  → `## General Formatting Rules` and `### Spacing and Breaks`.

- **Punctuation**: Remove trailing periods from bullet point phrases per
  `slides.rules.md` → `# Slide Organization` → `## Slide Structure`.

## Leave Structure and Content Unchanged
- Do not change the structure of the text (titles, bullet hierarchy, div fenced
  blocks)
- Do not change the substantive content: change only formatting
