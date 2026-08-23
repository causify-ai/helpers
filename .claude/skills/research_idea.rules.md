Conventions for the research idea documents under `research/ideas/*.md`: their
file naming, template, and the `README.md` tracking table.

# Directory Layout

## Files
- Each research idea is one file `research/ideas/<STATUS>.<Idea_Name>.md`
- The shared template is `research/ideas/template.research_idea.md`
- The tracking index is `research/ideas/README.md`

## Status Prefixes
- `draft.*`: early-stage, incomplete idea
- `ready.*`: specs are complete, work has not started
- `in_progress.*`: actively being worked on
- `done.*`: project is completed
- Rename the file (change the prefix) when an idea's status changes; do not
  add a separate status field only

# Writing Conventions

## Formatting
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
- Fit body text in 80-90 character lines

## Template Usage
- Follow the template `research/ideas/template.research_idea.md` for the
  section structure of a research idea file
- Do not invent new top-level sections; reuse the template's sections
  (`Core Idea`, `Formalization`, `Key Examples`, `Questions`, `Research
  Topics`, `Next steps`, `Implementation plan`, `References`)

# README Tracking Table

## Table Columns
- The table in `research/ideas/README.md` uses this column order:
  `| File | Links | Status | Assignee | Specs Complete | GitHub Issue | Result |`
- Sort rows by descending `Specs Complete`

## Update Timestamp
- The end of `research/ideas/README.md` carries a comment recording when the
  table was last regenerated, e.g. `// Last update timestamp: "Aug 3 10:54"`
- Update this comment whenever the table changes
- Use the comment to find which idea files changed since the last update: any
  file in `research/ideas/*.md` modified or added after that timestamp needs a
  table row

# Examples
- `research/ideas/in_progress.RL_for_pickleball.md`: a research idea fully
  formatted per the template
