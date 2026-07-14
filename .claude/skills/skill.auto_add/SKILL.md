---
description: Add a rule to the set of rules
model: haiku
---

# Goal
- The user passes you a file `<FILE>` and you need to find the changes between
  the generation of the file from LLM and the human corrections

# Workflow

## Step 1: Determined the Changes
- Look at the changes in Git to `<FILE>` and determine when the file was
  first generated and when the file was corrected by the human
- Print a Git command to diff `<FILE>`
  ```bash
  > git difftool ...
  ```

<!--
## Step 1: Read Skill Rules
- Read `.claude/skills/skill.rules.md` about conventions and rules to write
  skills

## Step 2: Determine Target Rule File
- If the user didn't specify `<TARGET_RULE_FILE>`, decide in which of the files
  `<TARGET_RULE_FILE>` the new rule needs to be added based on the content of
  `<CONTENT>`
- The available rules are:
  ```bash
  > ls -1 .claude/skills/*.rules.md
  ```

## Step 3: Read Target Rule File
- Read the target rules file `<TARGET_RULE_FILE>` to understand its structure and
  existing rules

## Step 4: Update the Rules
- Create the proposed rule `<CONTENT>` to be added, following the conventions in:
  - `.claude/skills/markdown.rules.md`
  - `.claude/skills/text.rules.md`

## Step 5: Add the new Rule
- Find the proper header H1 that is related to the `<CONTENT>`
  - See `.claude/skills/skill.rules.md` `## Keep Rules Organized in the Rule File`
- Add the rule `<CONTENT>` to the file `<TARGET_RULE_FILE>` following the conventions in
  `.claude/skills/skill.rules.md`
- Make sure there is no overlap with other rules
-->
