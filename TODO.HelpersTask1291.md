# Wishlist
- It will be nice to have everything running in a tmux so that it's easy to drop
  in and check the status

# Create list of tasks

- From master find the tasks to execute
  ```
  > rigtodo . py --todo ai_gp | tee cfile
  ./dev_scripts_helpers/testing/test/test_pytest_failed.py:48:        # TODO(ai_gp): Move the assertion into the helper.
  ./linters2/lint.py:316:    # TODO(ai_gp): Move this to _run_python_linting_actions
  ./linters2/test/test_lint.py:18:# TODO(ai_gp): Run skill /coding.factor_common_code
  ./linters2/test/test_lint.py:218:# TODO(ai_gp): Use the new mock for system capture_system_calls and
  ./helpers/hgraphviz.py:19:# TODO(ai_gp): Use import PIL if possible.
  ./helpers/hgit.py:406:    # TODO(ai_gp): Use system_to_one_line().
  ./helpers/hunit_test_utils.py:598:# TODO(ai_gp): Rename variables and functions using invocations -> sys_calls
  ./helpers/lib_tasks/lib_tasks_utils.py:242:# TODO(ai_gp): Use the one in ./helpers/hsystem.py
  ./helpers/test/test_hmodule.py:67:        # TODO(ai_gp): Use the new mock for system capture_system_calls and
  ./helpers/hunit_test.py:744:# TODO(ai_gp): Use the copy in helpers/hprint.py
  ./helpers/hdocker.py:771:        # TODO(ai_gp): Check that docker_cmd[2] starts with --user or use a
  ./helpers/hdocker.py:786:        # TODO(ai_gp): If it was pulled then skip building it.
  ./helpers/hmarkdown_coloring.py:227:# TODO(ai_gp): Use re.VERBOSE and comments
  ./helpers/hsystem.py:191:    # TODO(ai_gp): Rename "echo" -> "PRINT" and "echo_frame" -> "PRINT_FRAME"
  ./helpers/hsystem.py:419:# TODO(ai_gp): Move it to `helpers/printing.py`
  ./helpers/hsystem.py:948:# TODO(ai_gp): Move to hio.py
  ```

# Review list of tasks
- Review the list of potential tasks
  ```
  > vic
  ```
- Split and do `open cfile`
- Review the issues one by one
- Make sure that `cfile` is the desired one

# Create list of CC tasks
- Create the list of CC tasks from the cfile
  ```
  claude> /coding.create_auto_todo cfile
  ```
- Review and edit `plan.todo_janitor.md`
- This is the master list of what needs to be done

# Make sure that the list is updated

  ```
  claude> Look at the last merged git PRs in master and in the current repo and mark the completed issues in plan.todo_janitor.md
  ```

# Pick an Issue and Create the Branch

- Go in helpers1 tree (which is the one from which everything is orchestrated)

- Pick an issue from `plan.todo_janitor.md` and create a `todo_janitor.issue.md`

# Create CC Instructions

- Create instructions for CC from `todo_janitor.instr.md`

# Create the Branch / Worktree
  ```
  > create_git_worktree.py --gh_issue_title "Rename invocations to sys_calls Throughout Codebase" --gh_issue_body body.txt --instr_file instr2.md

  > create_git_worktree.py --gh_issue_id 1292 --instr_file instr2.md
  ```

- Create a GitHub issue in a certain repo
  > gh issue create --title "Fix bug X" --body "Description here" --assignee @me
  or 
  > gh issue create --title "Refactor Regex to Use re.VERBOSE and Comments" --body-file ...
  or
  > i gh_issue_title

GitHub issue link: https://github.com/causify-ai/helpers/issues/1290

- Get the name of the issue
```
> i gh_issue_title -i 1290
```
HelpersTask1290_Refactor_Regex_to_Use_re.VERBOSE_and_Comments

- Create a branch and a worktree
export WORKTREE_PATH=/Users/saggese/src/helpers1290
export FEATURE_NAME="HelpersTask1290_Refactor_Regex_to_Use_re.VERBOSE_and_Comments"

// Create branch and worktree in main repo
git branch $FEATURE_NAME master
> git worktree add $WORKTREE_PATH $FEATURE_NAME
Preparing worktree (checking out 'HelpersTask1290_Refactor_Regex_to_Use_re.VERBOSE_and_Comments')
HEAD is now at 614270bf gp_scratch_30 (#1289)

// Create a new iterm
> cd $WORKTREE_PATH
> dev_scripts_helpers/thin_client/tmux.py --index 1290

# Does i git_create_...

> git push
fatal: The current branch HelpersTask1292_Rename_invocations_to_sys_calls_Throughout_Codebase has no upstream branch.
To push the current branch and set the remote as upstream, use

    git push --set-upstream origin HelpersTask1292_Rename_invocations_to_sys_calls_Throughout_Codebase

Move the i git_create_branch to a script

./helpers/lib_tasks/lib_tasks_git.py def git_branch_create(

And create an empty branch in draft mode

i gh_create_pr --no-draft

#
Inject todo_janitor.current_issue.md into todo_janitor.template.md -> todo_janitor.instr.md

create_git_worktree.py --gh_issue_title 'Clean up' --gh_issue_body_file todo_janitor.current_issue.md

# Extend

i gh_watch

Make it i gh_workflow_list --daemon and make it exit when all the builds are done and
exit with error or not

> more instr2.md
- Wait that all the checks are complete and passing
  i gh_workflow_list

  - If the tests are passing, run all the tests locally
    pytest_multi_build.py --target .

    - If there are not issues, then mark the PR as ready
      gh pr  comment --body "All tests are passing"

      - Ask to review

# Update the CC task plan

orchestrate_task.py --plan ... --action

--action stage_todo calling create_git_worktree.py (
    - create the body and instr.md
    - update the todo

# Commit the changes
- TODO(gp): Need to figure out how to enable it for special trees

# Step 4: 
- Create a PR

# Step 5
- Test locally the PR for all the builds

# Step 6
- If everything is 

# Create a worktree for subrepo

```
SUBREPO_PATH="path/to/subrepo"  # Update this with your subrepo path
# Update submodules
git submodule update --init --recursive

# Create and checkout branch in subrepo
cd $SUBREPO_PATH
git branch $FEATURE_NAME
git checkout $FEATURE_NAME

echo "✓ Worktree and branches created successfully!"
echo "Main repo worktree: $WORKTREE_PATH"
echo "Branch: $FEATURE_NAME (in both repos)"
```
