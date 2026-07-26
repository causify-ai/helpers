## Goal
- Extend the invoke task `git_branch_copy` to support copying branches that
  branch from non-master parents (e.g., copy `gp_scratch_29` → `gp_scratch_31`
  where both branch from `gp_scratch`).

## Current Behavior
`git_branch_copy` in `./helpers/lib_tasks/lib_tasks_git.py:830`:
1. Cleans working tree (git clean -fd)
2. Merges master into current branch (optional: `--skip-git-merge-master`)
3. Creates new branch FROM master
4. Squash-merges source branch into new branch: `git merge --squash --ff <source>`
5. Resets HEAD (staged changes stay)
Result: new branch has same content as source, all commits compressed into
staging area, ready to commit.

Problem: always creates new branch from master, breaks branch hierarchies
(e.g., gp_scratch_29 → gp_scratch_31 should both branch from gp_scratch).

## Solution

### PR1: [ ] Extract logic into separate script

- Create `./dev_scripts_helpers/git/git_branch_copy.py` with extracted logic
  from `./helpers/lib_tasks/lib_tasks_git.py:830`
- Invoke target becomes wrapper calling the function
- Add unit tests following `.claude/skills/testing.rules.md`

### PR2: [ ] Generalize git_branch_copy to detect parent branch

**Detect Parent Branch**
- Add function to find parent branch:
  - Priority 1: use `--parent_branch` if specified (explicit override)
  - Priority 2: detect remote tracking branch via `git rev-parse --abbrev-ref <branch>@{u}`
  - Priority 3: fallback to master, warn user if auto-detection failed
- Return detected parent branch name

**Modify Merge Strategy**
- Keep squash-merge (current behavior: `git merge --squash --ff`)
- Create new branch from detected parent (not always from master)
- New branch inherits parent hierarchy

**Add Parameter**
- `--parent_branch`: explicit parent override (skip auto-detection)

**Update Branch Creation**
- Replace hardcoded master with detected parent branch
- Ensure new branch branches from same parent as source

**Add Tests**
- E2E: copy scratch branches (gp_scratch_29 → gp_scratch_31, both from gp_scratch)
- E2E: copy task branches (still work with master as parent)
- E2E: explicit `--parent_branch` override works
- E2E: warning issued when auto-detection fails and master used

## Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing testing code you must always follow the instructions in
  `.claude/skills/testing.rules.md`

## Create a plan, if needed
- If the task is not perfectly clear:
  - You MUST not perform it
  - Ask for clarifications
  - Create a `plan.md` in the same directory with 5 bullet points explaining what
    the plan is
  - Wait for the user to confirm
