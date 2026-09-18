# Goals

- Create small PRs
  - Allow agents to work in parallel with minimal overlap
  - Make it easy for humans to review the code and merge
- Automate the workflow
  - Specs -> Branch -> Work -> PR -> Checks -> Review -> Merge

# Tools

## Script Location

- All GitHub workflow automation tools are provided via:
  - **Invoke tasks**:
    - Defined in `helpers_root/helpers/lib_tasks/lib_tasks_git.py` and
      `helpers_root/helpers/lib_tasks/lib_tasks_gh.py`
    - Run via `invoke <task_name>` from the repository root
  - **Script files**:
    - Defined in `helpers_root/dev_scripts_helpers/git`
  - **Agent skills**:
    - Defined in `.claude/skills/github.*/SKILL.md`
    - Run via `/<skill_name>` from Claude Code
- Invoke, scripts, and skills related to Git start with `git_`, while ones related to
  GitHub start with `gh_`

## Summary

| Category               | Task                                 | Type   | Description                                               |
| ---------------------- | ------------------------------------ | ------ | --------------------------------------------------------- |
| Git Branch Create      | `git_create_issue_and_branch`        | Script | Create GitHub issue and corresponding branch/worktree     |
|                        | `git_branch_create`                  | Invoke | Create and push upstream branch with optional draft PR    |
| Git Branch Copy/Rename | `git_branch_copy`                    | Invoke | Copy branch content to new auto-generated name            |
|                        | `git_branch_rename`                  | Invoke | Rename branch locally and remotely, recreate PR if exists |
| Git Branch Query       | `git_branch_next_name`               | Invoke | Generate unique branch name to avoid conflicts            |
|                        | `git_branch_is_merged`               | Invoke | Check if branch was merged into master                    |
| Git Branch Cleanup     | `git_branch_delete_merged`           | Invoke | Delete local and remote merged branches                   |
| Git Branch Review      | `git_branch_diff`                    | Invoke | Diff branch against base, master, HEAD, or hash           |
|                        | `git_branch_files`                   | Invoke | Show detailed status of changed files                     |
| GitHub Auth            | `gh_login`                           | Invoke | Login to GitHub with SSH key and auth token               |
| GitHub Issues          | `gh_issue_create`                    | Invoke | Create new GitHub issue with labels and assignees         |
|                        | `gh_issue_title`                     | Invoke | Print branch-name-compatible issue title                  |
| GitHub PRs             | `gh_create_pr`                       | Invoke | Create draft PR for current branch                        |
| GitHub Workflows       | `gh_workflow_list`                   | Invoke | Report GitHub workflow status with filtering              |
|                        | `gh_workflow_run`                    | Invoke | Manually trigger workflows on specified branch            |
|                        | `gh_delete_workflow_runs`            | Invoke | Delete workflow runs with optional age filtering          |
| GitHub Skills          | `/github.split_branch_in_PRs`        | Skill  | Split current changes into small, cohesive PRs            |
|                        | `/github.create_child_pr`            | Skill  | Build a child PR from the current branch                  |
|                        | `/github.find_name_for_pr`           | Skill  | Find a title and description for the current PR           |
|                        | `/github.get_pr_ready_to_merge`      | Skill  | Get the current PR ready to be reviewed and merged        |
|                        | `/github.get_pr_to_pass_local_tests` | Skill  | Make local unit tests pass for the current PR             |
|                        | `/github.get_pr_to_pass_ci_tests`    | Skill  | Make the CI pass for the current PR                       |

## Git Branch Management

### Create and Initialize Branches

#### `git_create_issue_and_branch.py`

- Creates a GitHub issue and corresponding git branch/worktree in one operation
- Create issue and its initial branch

  ```bash
  > git_create_issue_and_branch.py --title "Fix bug in parser"
  ```

- Create with body, labels, and assignees

  ```bash
  > git_create_issue_and_branch.py \
    --title "Feature" \
    --body "Details" \
    --labels "enhancement" \
    --assignees "user1"
  ```

- Create stacked branches (e.g., `_1`, `_2`) for splitting one issue across multiple
  PRs

  ```bash
  > git_create_issue_and_branch.py --title "Large feature" --suffix 1
  ```

#### `git_branch_create`

- Create and push upstream branch, optionally creating a draft PR
- Create branch from GitHub issue

  ```bash
  > invoke git_branch_create --issue-id 123
  ```

- Create branch with explicit name

  ```bash
  > invoke git_branch_create --branch-name "MyTask456_Feature_description"
  ```

- Create branch without auto-creating draft PR

  ```bash
  > invoke git_branch_create --branch-name "MyTask456_Feature" --no-create-pr
  ```

### Copy and Rename Branches

#### `git_branch_copy`

- Create a new branch with the same content as the current branch (squash merge)
- Copy current branch to new auto-generated name

  ```bash
  > invoke git_branch_copy
  ```

- Copy with explicit new name

  ```bash
  > invoke git_branch_copy --new-branch-name "MyTask456_Feature_v2"
  ```

- Copy without merging master first

  ```bash
  > invoke git_branch_copy --skip-git-merge-master
  ```

#### `git_branch_rename`

- Rename current branch locally and remotely. If a PR exists, recreates it under the
  new name
- Rename current branch

  ```bash
  > invoke git_branch_rename --new-branch-name "MyTask456_Better_description"
  ```

### Query Branch Status

#### `git_branch_next_name`

- Generate a unique branch name derived from current branch to avoid conflicts
- Show next available name

  ```bash
  > invoke git_branch_next_name
  ```

- Generate name from specific branch

  ```bash
  > invoke git_branch_next_name --branch-name "MyTask456_Feature"
  ```

- Use GitHub API method (faster)

  ```bash
  > invoke git_branch_next_name --method github_api
  ```

#### `git_branch_is_merged`

- Check if current branch was merged into master using GitHub API and git
- Check merge status

  ```bash
  > invoke git_branch_is_merged
  ```

### Clean Up Branches

#### `git_branch_delete_merged`

- Remove (both local and remote) branches that have been merged into master
- Delete merged branches with user confirmation

  ```bash
  > invoke git_branch_delete_merged
  ```

- Delete without confirmation

  ```bash
  > invoke git_branch_delete_merged --no-confirm-delete
  ```

### Review Changes

#### `git_branch_diff`

- Diff files of current branch against a specified point (base, master, HEAD, or
  hash)
- Diff against branch point

  ```bash
  > invoke git_branch_diff --target base
  ```

- Diff against origin/master

  ```bash
  > invoke git_branch_diff --target master
  ```

- Diff uncommitted changes

  ```bash
  > invoke git_branch_diff --target head
  ```

- Diff against specific hash

  ```bash
  > invoke git_branch_diff --target hash --hash-value abc123def
  ```

- Diff last commit

  ```bash
  > invoke git_branch_diff --target last_commit
  ```

- Only Python files

  ```bash
  > invoke git_branch_diff --target base --file-types py
  ```

- Skip documentation files

  ```bash
  > invoke git_branch_diff --target base --skip-file-types txt,md
  ```

- Show files without opening vimdiff

  ```bash
  > invoke git_branch_diff --target base --only-print-files
  ```

#### `git_branch_files`

- Report detailed status of files changed in current branch (added, modified,
  deleted)
- Show file changes with status

  ```bash
  > invoke git_branch_files
  ```

## GitHub Workflow Management

### Authentication

#### `gh_login`

- Login to GitHub with configured SSH key and authentication token
- Login with default account

  ```bash
  > invoke gh_login
  ```

- Login with specific account

  ```bash
  > invoke gh_login --account myorg
  ```

- Print auth status

  ```bash
  > invoke gh_login --print-status
  ```

### Issue Management

#### `gh_issue_create`

- Create a new GitHub issue with optional body, labels, assignees, and project
- Simple issue

  ```bash
  > invoke gh_issue_create --title "Fix bug in parser"
  ```

- Issue with details

  ```bash
  > invoke gh_issue_create \
    --title "Add new feature" \
    --body "Description here" \
    --labels "enhancement,priority-high" \
    --assignees "user1,user2"
  ```

- Create issue and first branch (with suffix for stacking)

  ```bash
  > invoke gh_issue_create --title "Large feature" --suffix 1
  ```

#### `gh_issue_title`

- Print the branch-name-compatible title of a GitHub issue
- Get and copy to clipboard

  ```bash
  > invoke gh_issue_title --issue-id 123
  ```

- Get without clipboard copy

  ```bash
  > invoke gh_issue_title --issue-id 123 --no-pbcopy
  ```

### Pull Request Management

#### `gh_create_pr`

- Create a draft PR for the current branch with optional body, labels, and reviewers
- Create draft PR with branch name as title

  ```bash
  > invoke gh_create_pr
  ```

- Create PR with custom title

  ```bash
  > invoke gh_create_pr --title "My Custom PR Title" --draft
  ```

- Create ready-to-review PR

  ```bash
  > invoke gh_create_pr --draft False
  ```

- Create PR with reviewers and labels

  ```bash
  > invoke gh_create_pr --reviewer user1,user2 --labels "needs-review,enhancement"
  ```

- Create PR with auto-merge enabled

  ```bash
  > invoke gh_create_pr --auto-merge
  ```

### Workflow Management

#### `gh_workflow_list`

- Report the status of GitHub workflows with filtering and optional daemon mode for
  continuous monitoring
- Check current branch workflows

  ```bash
  > invoke gh_workflow_list
  ```

- Check master branch workflows

  ```bash
  > invoke gh_workflow_list --filter-by-branch master
  ```

- Check all branches

  ```bash
  > invoke gh_workflow_list --filter-by-branch all
  ```

- Filter by completed status

  ```bash
  > invoke gh_workflow_list --filter-by-completed failure
  ```

- Monitor workflows continuously (updates every 60s)

  ```bash
  > invoke gh_workflow_list --daemon
  ```

- Monitor with custom interval (every 30s)

  ```bash
  > invoke gh_workflow_list --daemon --interval 30
  ```

#### `gh_workflow_run`

- Manually trigger GitHub workflows for a branch
- Run all workflows on current branch

  ```bash
  > invoke gh_workflow_run --branch current_branch
  ```

- Run all workflows on master

  ```bash
  > invoke gh_workflow_run --branch master
  ```

- Run specific workflow

  ```bash
  > invoke gh_workflow_run --branch current_branch --workflows fast_tests
  ```

#### `gh_delete_workflow_runs`

- Delete workflow runs, optionally filtered by age
- Delete all runs for a workflow (with confirmation)

  ```bash
  > invoke gh_delete_workflow_runs --workflow-name "Fast tests"
  ```

- Delete runs older than 30 days

  ```bash
  > invoke gh_delete_workflow_runs --workflow-name "Slow tests" --older-than-days 30
  ```

- Preview what would be deleted

  ```bash
  > invoke gh_delete_workflow_runs --workflow-name "Fast tests" --dry-run
  ```

- Delete without confirmation prompt

  ```bash
  > invoke gh_delete_workflow_runs --workflow-name "Fast tests" --no-confirmation
  ```

## GitHub Agent Skills

- Higher-level automation skills that combine several invoke tasks and scripts into
  one command, run via `/<skill_name>` from Claude Code

### Splitting and Naming PRs

#### `github.split_branch_in_PRs`

- Split current git changes into small, cohesive PRs to simplify merging
- Analyze current branch and generate a PR split plan (`github_pr_plan.md`)

  ```bash
  claude> /github.split_branch_in_PRs
  ```

#### `github.create_child_pr`

- Write instructions to build a child PR from the current branch
- Create the next child PR from a split plan

  ```bash
  claude> /github.create_child_pr PR2
  ```

#### `github.find_name_for_pr`

- Find a title and a description for the current Pull Request
- Generate title and description for the current PR

  ```bash
  claude> /github.find_name_for_pr
  ```

### Preparing PRs for Merge

#### `github.get_pr_ready_to_merge`

- Get the current PR ready to be reviewed and merged
- Fix formatting, lint, pyright, local tests, and CI issues blocking a merge

  ```bash
  claude> /github.get_pr_ready_to_merge
  ```

#### `github.get_pr_to_pass_local_tests`

- Make the local unit tests pass for the current PR
- Fix failing local tests on the current PR

  ```bash
  claude> /github.get_pr_to_pass_local_tests
  ```

#### `github.get_pr_to_pass_ci_tests`

- Make the CI pass for the current PR
- Fix CI failures on the current PR

  ```bash
  claude> /github.get_pr_to_pass_ci_tests
  ```

# Workflows

### How to Split Large PRs

- When a single PR becomes too large or covers multiple independent features, split
  it into stacked PRs for easier review and faster merging
- This workflow uses Claude Code skills to automate the process as in the following
- **Start with your large branch** containing multiple independent changes
- **Run the split skill** to analyze and plan PR divisions:

  ```bash
  claude> /github.split_branch_in_PRs
  ```

  - This generates a `github_pr_plan.md` file with:
    - Proposed PR divisions (files grouped by feature/concern)
    - Stack order (dependencies and merge order)
    - Description for each PR
- **Review and edit the plan** in `github_pr_plan.md`:
  - Adjust which files go into each PR
  - Reorder PRs if needed
  - Update titles and descriptions
  - Mark dependencies if PR2 depends on PR1, etc
- **Create child PRs** for each planned branch:

  ```bash
  claude> /github.create_child_pr PR2
  cluade> /github.create_child_pr PR3
  ```

  For each PR number in the plan, this:
  - Creates a new branch with selected files
  - Opens a draft PR with the planned description
  - Maintains dependency links via PR body references
- **Review and merge sequentially**:
  - Merge PR1 first (base PR, usually depends on nothing)
  - Then merge PR2, PR3, etc. in order
  - Later PRs automatically include commits from earlier ones

### How to Peel Off a PR From a Personal Branch

- Use this flow when work has accumulated on a personal or scratch branch (e.g.,
  `gp`) and needs to become a proper, named PR ready for review and merge
- **Generate a PR title and description** for the current branch

  ```bash
  claude> /github.find_name_for_pr
  ```

  - Review the generated message

    ```bash
    > more pr_commit_msg.txt
    ```

- **Copy the branch to a task-named branch**, following the branch naming convention

  ```bash
  > invoke git_branch_copy --new-branch-name "UmdTask1346_Infrastructure_and_Developer_Experience_Improvements"
  ```

- **Clean up leftover tmp files** before staging

  ```bash
  > rm -rf tmp.precommit_output.txt
  ```

- **Stage all untracked files**

  ```bash
  > invoke git_add_all_untracked
  ```

- **Get the PR ready to merge**:
  - Fix CI failures

    ```bash
    /github.get_pr_to_pass_ci_tests
    ```

  - Fix failing local tests

    ```bash
    claude> /github.get_pr_to_pass_local_tests
    ```

  - Fix formatting, lint, and other commit-blocking issues

    ```bash
    claude> /github.get_pr_ready_to_merge
    ```

- **Merge and delete the branch**

  ```bash
  > gh pr merge -s --admin --delete-branch
  ```

### How to Create a Stacked Sub-Branch for an Existing Issue

- Use this flow when an issue already has a base branch/PR, and a new, independent
  chunk of work needs its own stacked sub-branch/sub-PR under the same issue
- **Create the base branch and PR** for a new issue

  ```bash
  > git_create_issue_and_branch.py --issue-id 1328
  ```

- **Force-create the next stacked sub-branch** for the issue

  ```bash
  > invoke git_branch_create --issue-id 1331 --suffix 1
  ```

  - Known limitation: this checks out the new branch immediately, with no option to
    create it without switching
- **Known limitation**: re-running the command for a suffix that already exists fails
  instead of finding the next free one

  ```text
  Branch 'HelpersTask1331_Implement_TODOs_1' already exists
  ```

- **Open question**: no command yet auto-detects and creates the next available
  suffix for an issue in one step
- **Known bug**: `invoke git_branch_next_name` does not return the expected name for
  an issue-based branch
  - Without `--branch-name`, it computes the next name from the current branch
    instead of the target task

    ```bash
    > invoke git_branch_next_name
    ...
    branch_next_name='gp_scratch_37_1'
    ```

  - With `--branch-name HelpersTask1331_Implement_TODOs`, it works via the GitHub API
    and finds the correct next free suffix

    ```bash
    > invoke git_branch_next_name --branch-name HelpersTask1331_Implement_TODOs
    ...
    branch_next_name='HelpersTask1331_Implement_TODOs_2'
    ```

# References

- `helpers_root/docs/work_organization/all.use_github.how_to_guide.md`