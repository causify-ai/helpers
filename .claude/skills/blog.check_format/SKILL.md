---
description: Check the format of a blog file
model: haiku
---

# Goal
- Check that all the actual and the draft blogs have the correct format

# Step 1: Find Files
- Look for all the markdown files both `SKILL.md` and `<TOPIC>.rules.md`
  ```
  > find website/docs/blog/post -name "*.md"
  ```

# Step 2: Read Context

- Read context about rules from
  - `.claude/skills/blog.rules.md`
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

# Step 3: Check Rules
- For each file apply all the following rules and report violations as described
  below

## Check File Exists
- Make sure the front matter matches the right format
  ```
  ---
  title: ...
  draft: true / false
  authors:
    - gpsaggese
  date: 2025-06-01
  categories:
    - Causal AI
    ...
  ---
  ```
- Make sure everything is correct
  - The title is catchy and good
  - The date matches when the file was first created
  - The categories are appropriate and match the ones in `website/mkdocs.yml`

## Check That Has a TLDR
- Make sure that there is a TL;DR in the format below right after the front
  matter
  - E.g.,
    ```
    TL;DR: Running blind experiments is expensive. Bayesian Optimization predicts
    where to look next and saves you millions.

    <!-- more -->
    ```
- If not report as a violation as described later

## Check for Other Violations
- Use the rules in `.claude/skills/blog.rules.md` to look for clear violations
- Report them only if you are really sure about it

# Step 4: Report Violations

- Report all the violations in a file `cfile` using the format in
  `.claude/skills/cfile.rules.md`

# Step 5: Ask Users Whether to Fix the Problems
- Ask for the user which problems should be fixed by printing a list of problem
  with indices
