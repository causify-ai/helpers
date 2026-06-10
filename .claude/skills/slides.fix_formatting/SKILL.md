---
description: Fix formatting conventions in slides (bold labels, LaTeX, punctuation, unicode, emoji)
model: haiku
---

- Given a markdown file with slides, fix formatting issues without changing the
  content or structure

- Read `.claude/skills/slides.rules.md` and apply the formatting rules strictly

## Fix Bold Labels
- Ensure every first-level bullet point starts with a bold label from the
  approved list (e.g., **Definition**, **Example**, **Problem**, **Solution**,
  **Question**, etc.)
- See `slides.rules.md` → `# Slide Organization` → `## Use Bold for Slide Sections`
  for the complete list of approved labels

## Fix Unicode Characters
- Replace non-ASCII characters with LaTeX equivalents
  - `→` → `$\to$`
  - `ε` → `$\varepsilon$`
  - `∝` → `$\propto$`
  - `≈` → `$\approx$`
  - `∩` → `$\cap$`
  - `∪` → `$\cup$`

## Fix Emoji
- Remove emoji characters

## Fix Page Separators
- Remove `---` page separator lines

## Fix Punctuation
- Remove periods at the end of bullet point phrases
- Leave periods only where grammatically required (e.g., inside sentences, not
  at the end of bullet points)

## Leave Structure and Content Unchanged
- Do not change the structure of the text (titles, bullets, div fenced blocks)
- Do not change the substantive content — only formatting