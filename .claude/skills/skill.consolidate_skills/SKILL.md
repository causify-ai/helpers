---
description: Consolidate and rename skills by topic to remove redundancy
model: haiku
---

# Goal
- Consolidate and rename skills by topic to make the skill set better
  organized and less redundant

# Workflow

## Read Skill Rules
- Read `.claude/skills/skill.rules.md`

## Find All the Topics
- Find the topics by running
  ```bash
  > find .claude/skills -type d | sort | tail -n +2 | sed 's|^\.claude/skills/||' | awk -F'.' '{print $1}' | sort -u
  ```

## Process Skills for Each Topic
- For each `<TOPIC>`, find all the associated skills in the format
  `.claude/skills/<TOPIC>.<ACTION>/SKILL.md`
  ```bash
  > mdm skill f <TOPIC>
  ```
- E.g.,
  ```bash
  > mdm skill f testing
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.add_end_to_end_tests/SKILL.md
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.fix_input_output_vars/SKILL.md
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.fix_mock_tests/SKILL.md
  /Users/saggese/src/umd_classes1/helpers_root/.claude/skills/testing.fix_unit_tests/SKILL.md
  ```

## Propose the Plan
- For each topic `<TOPIC>`:
  - Check for redundant actions
  - Suggest clearer names for the skills

## Execute the Plan
- Ask the user to approve the plan
- Implement the plan:
  - Rename files with `git mv`
  - Add new files with `git add`
  - Remove files with `git rm`

# Verification
- [ ] The user approved the plan before any file was changed
- [ ] Every renamed or removed skill directory still has a valid `SKILL.md`,
      or was intentionally removed
- [ ] No reference elsewhere in `.claude/skills` points to a renamed or
      removed skill's old path
