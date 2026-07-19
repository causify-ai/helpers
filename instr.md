# Step 0

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

# Step
- vic
- Split open cfile
- Review the issues
- Make sure that cfile is the desired one

# Step
claude> /coding.create_auto_todo cfile

# Step 1: Pick an Issue and Create the Branch

- Go in helpers1 tree (which is the one from which everything is orchestrated)

- Pick the issue from plan.todo_janitor.md

- Create a GitHub issue in a certain repo
  > gh issue create --title "Fix bug X" --body "Description here" --assignee @me
  or 
  > gh issue create --title "Refactor Regex to Use re.VERBOSE and Comments" --body-file ...
  or
  > i gh_issue_title

GitHub issue link: https://github.com/causify-ai/helpers/issues/1290

- Get the name of the issue
i gh_issue_title -i 1290
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

# Step 2: Create Instructions
// Create instructions for CC
  ````
  - Fix the following issue following the conventions

  - When writing code you must always follow the instructions in
    `.claude/skills/coding.rules.md`

  - When testing code you must always follow the instructions in
    `.claude/skills/testing.rules.md`

  - If the task is not perfectly clear, you MUST not perform it, but ask for
    clarifications
    - When the task is complex, create a `plan.md` with 5 bullet points explaining
      what the plan is

  ## Issue
  ```
  ## [ ] Issue1: Refactor Regex to Use re.VERBOSE and Comments

  ### Info
  - Original description:
    `./helpers/hmarkdown_coloring.py:227:# TODO(ai_gp): Use re.VERBOSE and comments`

  ### Proposed Fix
  - Type: improvement/cosmetic
  - Reason: Current regex is hard to read. Using re.VERBOSE with inline comments
    improves maintainability
  - Proposed fix:
    - Replace `_COLOR_MARKER_REGEX = r"(?<!\w)@([^@\n]+)@"` with a verbose version
    - Add comments explaining each part of the pattern
  - Confidence in the fix: high
  - Fix complexity: low
  - Verification plan:
    - Run tests for `hmarkdown_coloring.py` to verify regex still works
    - Check that colorize functions still produce expected output

  ### Status
  - Status: filed
  - GitHub issue link: https://github.com/causify-ai/helpers/issues/1290
  - Git worktree:
  - PR link:
  ```

  ````
- Update the master plan

# Step 3: Commit the changes
- TODO(gp): Need to figure out how to enable it for special trees

# Step 4: 
- Create a PR

# Step 5
- Test locally the PR for all the builds

# Step 6
- If everything is p

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
