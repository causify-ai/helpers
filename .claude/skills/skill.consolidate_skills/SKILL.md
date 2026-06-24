---
description: Consolidate and rename skills to be more appropriate
model: haiku
---

# Goal
- Consolidate and rename skills by topics in order to be more organize, have less
  redundancy

## Step 1
- Read `.claude/skills/skill.rules.md`

## Step 2: Find All the Topics
- Find the topics by running
  ```
  > find .claude/skills -type d | sort | tail -n +2 | sed 's|^\.claude/skills/||' | awk -F'.' '{print $1}' | sort -u)
  ```

## Step 3: Process Skills For Each Topic

- For each `<TOPIC>` find all the associated skills
  in the format `.claude/skills/<TOPIC>.<ACTION>/SKILL.md`
  ```
  > mdm skill f <TOPIC>
  ```
- E.g.,
  ```
  > mdm skill f testing
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.add_end_to_end_tests/SKILL.md
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.fix_input_output_vars/SKILL.md
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.fix_mock_tests/SKILL.md
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.fix_unit_tests/SKILL.md
  ```

## Step 4: Propose Plan
- For each topic `<TOPIC>`
  - Check if there are redundant actions
  - Suggest how to rename to have clearer names

## Step 5: Execute Plan
- Ask user to approve the plan
- Implement the plan by:
  - Renaming files with `git mv`
  - Adding new files with `git add`
  - Removing files with `git rm`
