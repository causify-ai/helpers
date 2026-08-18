---
description: Update a skill or prompt so it captures the lessons learned from how a file changed across Git versions
argument-hint: <FILE> <PROMPT>
model: sonnet
---

# Goal

- The user gives you two arguments:
  - `<FILE>`: a path to a file that has been edited across one or more Git
    commits
  - `<PROMPT>`: a path to a skill (`SKILL.md`) or prompt file to improve
- The edits to `<FILE>` encode a lesson: someone had to fix something by hand
  that `<PROMPT>` should have gotten right the first time
- Your job is to update `<PROMPT>` so that, given the original `<FILE>`, it would
  now produce the final `<FILE>`
- Generalize: infer the underlying *rule*, do not hard-code the specific strings
  from this one diff

# Inputs

- If `<FILE>` or `<PROMPT>` is missing or ambiguous, stop and ask the user rather
  than guessing
- If `<FILE>` has no committed changes, report that and stop

# Workflow

## Step 1: Determine the changes

- Find the commits that touched `<FILE>`:
  ```bash
  > git log --oneline --follow -- <FILE>
  ```
- Identify the *first* and *last* relevant revisions. Default to the full history
  of the file; if the user named a range, use that instead
- Extract `<CHANGES>` as a unified diff:
  ```bash
  > git diff <FIRST_SHA> <LAST_SHA> -- <FILE>
  ```
  - If the diff is large, also read the final version in full so you
    understand the intended end state, not just the deltas:
    ```bash
    > git show <LAST_SHA>:<FILE>
    ```
- Do not use interactive commands (e.g. `git difftool`): they block

## Step 2: Read the prompt and the conventions

- Read `<PROMPT>` in full
- Read `.claude/skills/skill.rules.md` for the conventions and rules that
  govern how skills and prompts must be written
- Read any files `<PROMPT>` references, so you don't duplicate a rule that
  already lives elsewhere

## Step 3: Infer the rules

- For each meaningful hunk in `<CHANGES>`, write down:
  - what changed (before → after)
  - the general rule it implies
  - whether `<PROMPT>` already covers it (fully / partially / not at all)
- Drop hunks that are one-off content edits rather than repeatable rules
  (e.g. fixing a specific typo, updating a date): say explicitly which
  hunks you dropped and why
- Merge rules that are restatements of each other. Prefer one sharp rule
  over three overlapping ones

## Step 4: Improve the prompt

- Draft the minimal edit to `<PROMPT>` that encodes the inferred rules:
  - Amend an existing rule when one is close but imprecise
  - Add a new rule only when no existing rule covers the case
  - Keep the existing structure, heading style, and voice of `<PROMPT>`
  - State rules as imperatives, with a short before/after example when the
    rule is easy to misread
- Do not grow the prompt unnecessarily: if the new rule makes an old one
  redundant, remove the old one

## Step 5: Apply via skill.add

- Follow the approach in `.claude/skills/skill.add/SKILL.md`: propose the
  change to the user first, then apply it once approved

# Output

Report, in this order:

1. The commit range and files inspected
2. A table of inferred rules: change observed → rule → covered / new
3. The proposed diff to `<PROMPT>`
4. Anything you deliberately did not encode, and why
