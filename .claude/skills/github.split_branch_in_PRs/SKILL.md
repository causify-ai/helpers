---
description: Split the current 
---

# Goal

- Propose how to split the current Git branch / PR into smaller one to minimize
  - The review complexity
  - The risk of breaking the unit tests

- If the task is not perfectly clear or complex, you MUST not perform it, but ask
  for clarifications and create a plan for review
  - Create a `plan.md` with 5 bullet points explaining what the plan is

## Step 1: Read rules

- Read rules about:
  - Coding: `.claude/skills/coding.rules.md`
  - Unit tests: `.claude/skills/testing.rules.md`

## Step 2: Read the changes in the current Git branch

- Analyze the changes and propose a set of PRs that decompose the changes in
   coherent and tightly coupled changes

- Prefer PRs that have the changes to an entire file instead of having to split
  changes in a file across multiple PRs

- Make sure that changes to files and their testing files are 

## Step 3: Report the output in the following format

- Create a file `github.PR_plan.md` with the following content
  ```
  # Info
  - Branch: <branch name>
  - Dir: <current dir>

  # [ ] PR1: <One line description>

  ## Complexity: low / medium / high

  ## Files
  - File1
  ...
  - File...

  # [ ] PR2: <One line description>

  ## Complexity: low / medium / high

  ## Files
  - File1
  ...
  - File...
  #```
