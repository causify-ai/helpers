---
description: Update research/ideas/README.md tracking table from idea files
model: haiku
---

# Goal
- Update `research/ideas/README.md` to reflect the current content of
  `research/ideas/*.md`

# Workflow

## Step 1: Find the Files to Process
- Extract the timestamp `<TIMESTAMP>` from the comment at the end of
  `research/ideas/README.md`, e.g. `// Last update timestamp: "Aug 3 10:54"`
- Find every file in `research/ideas/*.md` modified or added after
  `<TIMESTAMP>`, or not yet present as a row in the table
- Build the list of files to process, `<FILES>`

## Step 2: Read the Template
- Read `research/ideas/template.research_idea.md` to know what each idea file
  should contain

## Step 3: Update the Table
- For each file in `<FILES>`, add or update its row in
  `research/ideas/README.md` using the column order:
  `| File | Links | Status | Assignee | Specs Complete | GitHub Issue | Result |`
- Fill each column to the best of your ability from the file's content and
  status prefix
- Sort all rows by descending `Specs Complete`

## Step 4: Update the Timestamp
- Update the `// Last update timestamp: "..."` comment at the end of the file
  to the current timestamp

# Conventions
- Follow `.claude/skills/research_idea.rules.md`

# Constraints
- Only touch rows for files in `<FILES>`; do not rewrite rows for unchanged
  files beyond re-sorting the table
- Do not remove a row for a file that still exists in `research/ideas/*.md`

# Verification
- [ ] Every file in `<FILES>` has a row in the table
- [ ] Rows are sorted by descending `Specs Complete`
- [ ] The `// Last update timestamp: "..."` comment reflects the current time
