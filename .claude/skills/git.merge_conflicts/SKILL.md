---
description: Resolve git merge, rebase, or cherry-pick conflicts and finalize the operation
model: haiku
---

# Goal
- Given a repo with unresolved Git conflicts, understand why each conflict happened,
  resolve it, verify the result, and finalize the in-progress operation

# Workflow

## Identify the Operation In Progress
- Determine whether the repo is in the middle of a `merge`, `rebase`, or
  `cherry-pick`, since finalizing the resolution differs by operation
  ```
  > ls -a .git | grep -E "MERGE_HEAD|rebase-merge|rebase-apply|CHERRY_PICK_HEAD"
  ```
- Note `<SOURCE>`, the branch/commit being merged, rebased, or cherry-picked in, and
  `<TARGET>`, the branch that already contains history (e.g., `main` during a merge,
  or the branch being rebased onto)

## Find the Files with Conflicts
- Find the files with conflicts running
  ```
  > git diff --name-only --diff-filter=U
  ```

## Understand the Context
- Understand the context, e.g., by looking at the PR description, if present
  ```
  > gh pr view
  ```
  - If there is no open PR, `gh pr view` fails: skip it and rely on commit history
    instead
- Look at the previous commits on `<SOURCE>` and `<TARGET>` that lead to the
  conflict, to understand the intent behind each side
  ```
  > git log <TARGET>..<SOURCE>
  > git log <SOURCE>..<TARGET>
  ```

## Propose Fixes
- For each file with conflicts:
  - List every conflict hunk in the file (a file can have more than one `<<<<<<<` /
    `=======` / `>>>>>>>` block)
  - For each hunk (or set of similar hunks), explain why the conflict happened and
    propose what needs to be done

- Example
  ```verbatim
  1. tutorials/GitHub_Stats/Master_GitHub_analysis.py
     - Issue: Jupytext version conflict.
     - Resolution: Use <TARGET>, it's the newer version.

  2. tutorials/GitHub_Stats/docker_jupyter.sh
     - Issue: <SOURCE> adds -e GITHUB_ACCESS_TOKEN to Docker env; <TARGET>
       removes it.
     - Resolution: Use <TARGET> (remove the line)
  ```

- If unsure what to do, prefer the changes from `<SOURCE>` over `<TARGET>`
  - `<TARGET>`'s history is already saved, while discarding `<SOURCE>`'s changes
    could lose them permanently

## Ask User and Apply the Changes
- Ask the user which resolution to apply for each ambiguous case
- Edit each conflicted file to remove the conflict markers and apply the chosen
  resolution
- Confirm no conflict markers remain in any resolved file
  ```
  > grep -rn '^<<<<<<<\|^=======\|^>>>>>>>' <RESOLVED_FILES>
  ```
- Stage each resolved file
  ```
  > git add <FILE>
  ```

## Finalize the Operation
- You MUST ask for user permission before finalizing, per the repo rule of never
  committing without permission
- Once approved, finalize based on the operation identified above:
  - `merge`: `git commit`
  - `rebase`: `git rebase --continue`
  - `cherry-pick`: `git cherry-pick --continue`
- Do not skip hooks (e.g., `--no-verify`) or force anything unless the user
  explicitly asks for it

## Verification
- Run the related unit tests to make sure everything is fine
- Make sure there are no conflict markers `<<<<<<<` / `=======` / `>>>>>>>`
- Confirm the operation finished cleanly
  ```
  > git status
  ```

# Ask for Help If Unsure How to Do
- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a plan.md with 5 bullet points explaining
    what the plan is
