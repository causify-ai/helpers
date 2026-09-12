---
description: Find a title and a description for the current Pull Request
model: haiku
---

# Goal
- Given the current Git branch, find a title and a short description to push the
  changes as a Pull Request

# Workflow

## Read Rules

- Read rules about:
  - Coding: `.claude/skills/coding.rules.md`
  - Unit tests: `.claude/skills/testing.rules.md`

## Read the Changes in the Current Git Client

- Obtain the files that need to be merged with:
  ```bash
  git diff --name-status origin/master HEAD
  ...
  ```

- Analyze the difference between the current client and `master` (or
  `origin/master`):
  ```bash
  git diff master...HEAD --name-only
  # or if master is not available locally:
  git diff origin/master...HEAD --name-only
  ```

## Propose the Description of the PR
- Propose a one line title for the PR
  - It needs to be linux friendly so do not use & or non alphanumerical chars
- Save this into `pr_title.txt`

## Propose the Description of the PR
- Write a `pr_commit_msg.txt` containing a short list of changes in the format
  ```
  ## <Description of the change>
  - Change1
  - Change2
  ```
  where `<ChangeN>` are one or two line bullets describing what what changed
  related to `<Description of the change>`
- Do not use markdown formatting but only plaintext
- Do not use numbered bullets, but only nested bullets
- Use wrapped lines under 85 chars per line

### Example

```
This PR consolidates major infrastructure updates adding developer tools,
standardized documentation templates, and improved onboarding workflows for the
helpers_root ecosystem.

Stats: 192 files changed, 4985 insertions, 2218 deletions

- Documentation: Added CONTRIBUTING.md with contribution guidelines and
  task_instructions.md for task execution workflow
- Figure Creation Skills: Added 3 new figure-related skills (create_svg, create_tikz,
  make_professional) with rules
- Templates: Added github_PR_plan.template.md and architecture_doc.template.md for
  standardized documentation
- Tooling: Added scripts for figure compression, image downloading, and git utilities
  (find_junk.sh, git_backup_branch.sh)
- Onboarding: Added bounty spam prevention guide for team onboarding
- Skill Updates: Improved descriptions and workflows across 120+ skill files with
  consistent formatting
- Helper Improvements: Enhanced hdaemon.py and hselect_input_output.py with extended
  functionality
- Linting: Updated cc_lint.py with additional linting capabilities
- Documentation Cleanup: Removed legacy instr.md and consolidated command rules
```
