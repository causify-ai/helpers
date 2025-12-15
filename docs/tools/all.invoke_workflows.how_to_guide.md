<!-- toc -->

- [Introduction](#introduction)
  * [Listing All the Tasks](#listing-all-the-tasks)
  * [Getting Help for a Specific Workflow](#getting-help-for-a-specific-workflow)
  * [Implementation Details](#implementation-details)
- [Task Categories](#task-categories)
- [Common Workflows](#common-workflows)
  * [Git Workflows](#git-workflows)
    + [Merge Master in the Current Branch](#merge-master-in-the-current-branch)
  * [Github Workflows](#github-workflows)
    + [Create a PR](#create-a-pr)
    + [Extract a PR From a Larger One](#extract-a-pr-from-a-larger-one)
    + [Systematic Code Transformation](#systematic-code-transformation)
  * [Docker Workflows](#docker-workflows)
    + [Generate a Local `amp` Docker Image](#generate-a-local-amp-docker-image)
    + [Update the dev `amp` Docker image](#update-the-dev-amp-docker-image)
    + [Experiment in a local image](#experiment-in-a-local-image)
  * [Github Actions (CI)](#github-actions-ci)
  * [Pytest Workflows](#pytest-workflows)
    + [Run with Coverage](#run-with-coverage)
    + [Capture Output of a Pytest](#capture-output-of-a-pytest)
    + [Run Only One Test Based on Its Name](#run-only-one-test-based-on-its-name)
    + [Iterate on Stacktrace of Failing Test](#iterate-on-stacktrace-of-failing-test)
    + [Iterating on a Failing Regression Test](#iterating-on-a-failing-regression-test)
    + [Detect Mismatches with Golden Test Outcomes](#detect-mismatches-with-golden-test-outcomes)
  * [Lint Workflows](#lint-workflows)
    + [Lint Everything](#lint-everything)

<!-- tocstop -->

# Invoke Workflows

## Introduction

- We use `invoke` to implement workflows (aka "tasks") similar to Makefile
  targets, but using Python
- The official documentation for `invoke` is
  [here](https://docs.pyinvoke.org/en/0.11.1/index.html)

- We use `invoke` to automate tasks and package workflows for:
  - Docker: `docker_*`
  - Git: `git_*`
  - GitHub (relying on `gh` integration): `gh_*`
  - Running tests: `run_*`
  - Branch integration: `integrate_*`
  - Releasing tools and Docker images: `docker_*`
  - Lint: `lint_*`

- Each set of commands starts with the name of the corresponding topic:
  - E.g., `docker_*` for all the tasks related to Docker
- The best approach to getting familiar with the tasks is to browse the list and
  then check the output of the help
- `i` is the shortcut for the `invoke` command

  ```bash
  > invoke --help command
  > i -h gh_issue_title
  Usage: inv[oke] [--core-opts] gh_issue_title [--options] [other tasks here ...]

  Docstring:
  Print the title that corresponds to the given issue and repo_short_name.
  E.g., AmpTask1251_Update_GH_actions_for_amp.

  :param pbcopy: save the result into the system clipboard (only on macOS)

  Options:
  -i STRING, --issue-id=STRING
  -p, --[no-]pbcopy
  -r STRING, --repo-short-name=STRING
  ```

- We can guarantee you a 2x improvement in performance if you master the
  workflows, but it takes some time and patience

- `TAB` completion available for all the tasks, e.g.,

  ```bash
  > i gh_<TAB>
  gh_create_pr      gh_issue_title    gh_login          gh_workflow_list  gh_workflow_run
  ```
  - Tabbing after typing a dash (-) or double dash (--) will display valid
    options/flags for the current context.

### Listing All the Tasks

- New commands are always being added, but a list of valid tasks is below

  ```bash
  > invoke --list
  INFO: > cmd='/Users/saggese/src/venv/amp.client_venv/bin/invoke --list'
  Available tasks:
  ```

### Getting Help for a Specific Workflow

- You can get a more detailed help with

  ```bash
  > invoke --help run_fast_tests
  Usage: inv[oke] [--core-opts] run_fast_tests [--options] [other tasks here ...]

  Docstring:
  Run fast tests.

  :param stage: select a specific stage for the Docker image
  :param pytest_opts: option for pytest
  :param pytest_mark: test list to select as `@pytest.mark.XYZ`
  :param dir_name: dir to start searching for tests
  :param skip_submodules: ignore all the dir inside a submodule
  :param coverage: enable coverage computation
  :param collect_only: do not run tests but show what will be executed

  Options:
  -c, --coverage
  -d STRING, --dir-name=STRING
  -k, --skip-submodules
  -o, --collect-only
  -p STRING, --pytest-opts=STRING
  -s STRING, --stage=STRING
  -y STRING, --pytest-mark=STRING
  ```

### Implementation Details

- By convention all invoke targets are in `*_lib_tasks.py`, e.g.,
  - `helpers/lib_tasks.py` - tasks to be run in `cmamp`
  - `optimizer/opt_lib_tasks.py` - tasks to be run in `cmamp/optimizer`
- All invoke tasks are functions with the `@task` decorator, e.g.,

  ```python
  from invoke import task

  @task
  def invoke_task(...):
    ...
  ```

- To run a task we use `context.run(...)`, see
  [the official docs](https://docs.pyinvoke.org/en/0.11.1/concepts/context.html)
- To be able to run a specified invoke task one should import it in `tasks.py`
  - E.g., see `cmamp/tasks.py`
- A task can be run only in a dir where it is imported in a corresponding
  `tasks.py`, e.g.,
  - `invoke_task1` is imported in `cmamp/tasks.py` so it can be run only from
    `cmamp`
  - `invoke_task2` is imported in `cmamp/optimizer/tasks.py` so it can be run
    only from `cmamp/optimizer`
    - In other words one should do `cd cmamp/optimizer` before doing
      `i invoke_task2 ...`

## Task Categories

The invoke tasks are organized into the following categories:

- AWS/ECS Task Definitions
  - Tasks for managing AWS ECS task definitions across different environments
    (test, preprod, prod).
    - Creating task definitions for different environments
    - Copying image URLs between task definitions

- Bash Utilities
  - Simple bash utility commands for printing paths and directory trees.

- Docker Tasks
  - Comprehensive Docker workflow automation including:
    - **Container Operations**: Starting bash shells, running commands, Jupyter notebooks
    - **Image Building**: Building local, dev, prod, and multi-arch images
    - **Image Management**: Listing, pulling, pushing, and removing images
    - **Release Workflows**: Complete release pipelines for dev and prod images
    - **Tagging**: Managing image tags across registries

- Find Utilities
  - Code search and discovery tools:
    - Finding symbols, imports, and dependencies
    - Locating test classes and decorators
    - Finding `check_string()` output in tests

- GitHub Integration
  - GitHub operations via `gh` CLI integration:
    - Creating and managing pull requests
    - Managing GitHub issues
    - Running and monitoring GitHub Actions workflows
    - Publishing dashboards to S3

- Git Operations
  - Git workflow automation:
    - Branch management (create, copy, rename, delete)
    - Branch analysis (files changed, diffs, merge status)
    - Merging and pulling changes
    - Creating patches and backups
    - Repository integration

- Integration Workflows
  - Tools for integrating code between different repository directories:
    - Creating integration branches
    - Finding and comparing modified files
    - Syncing directories with rsync
    - Managing cross-repo integrations

  - Linting and Code Quality
    - Code quality and linting tools:
      - Running linters on modified files
      - Checking Python file compilation
      - Detecting cyclic imports
      - Creating lint branches
      - Syncing linting code

  - Pytest
    - Test management utilities:
      - Managing golden outcome files
      - Running regression tests (buildmeister)
      - Cleaning pytest artifacts
      - Comparing test logs
      - Renaming tests and their outcomes
      - Reproducing failed tests

  - Running Tests
    - Test execution tasks for different test suites:
      - Fast tests (quick unit tests)
      - Slow tests (integration tests)
      - Superslow tests (end-to-end tests)
      - Test coverage reporting
      - QA tests

## Common Workflows

### Git Workflows

#### Merge Master in the Current Branch

```bash
> i git_merge_master
```

### Github Workflows

- Get the official branch name corresponding to an Issue

  ```bash
  > i gh_issue_title -i 256
  ## gh_issue_title: issue_id='256', repo_short_name='current'

  # Copied to system clipboard:
  AmpTask256_Part_task2236_jenkins_cleanup_split_scripts:
  https://github.com/alphamatic/amp/pull/256
  ```

#### Create a PR

TODO(gp): Describe

#### Extract a PR From a Larger One

- For splitting large PRs, use the dedicated workflow `git_branch_copy'
- See detailed guide in
  [all.invoke_git_branch_copy.how_to_guide.md](/docs/tools/all.invoke_git_branch_copy.how_to_guide.md)

#### Systematic Code Transformation

- Can be done with the help of
  `dev_scripts_helpers/system_tools/replace_text.py`

### Docker Workflows

#### Generate a Local `amp` Docker Image

- This is a manual flow used to test and debug images before releasing them to
  the team.
- The flow is similar to the dev image, but by default tests are not run and the
  image is not released.

  ```bash
  # Build the local image (and update Poetry dependencies, if needed).

  > i docker_build_local_image --update-poetry
  ...
  docker image ls 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local

  REPOSITORY TAG IMAGE ID CREATED SIZE
  665840871993.dkr.ecr.us-east-1.amazonaws.com/amp local 9b3f8f103a2c 1 second ago 1.72GB

  # Test the new "local" image
  > i docker_bash --stage "local" python -c "import async_solipsism" python -c
  > "import async_solipsism; print(async_solipsism.**version**)"

  # Run the tests with local image
  # Make sure the new image is used: e.g., add an import and trigger the tests.
  > i run_fast_tests --stage "local" --pytest-opts core/dataflow/test/test_real_time.py
  > i run_fast_slow_tests --stage "local"

  # Promote a local image to dev.
  > i docker_tag_local_image_as_dev
  > i docker_push_dev_image
  ```

#### Update the dev `amp` Docker image

- To implement the entire Docker QA process of a dev image

  ```bash
  # Clean all the Docker images locally, to make sure there is no hidden state.
  > docker system prune --all

  # Update the needed packages.
  > devops/docker_build/pyproject.toml

  # Visually inspect the updated packages.
  > git diff devops/docker_build/poetry.lock

  # Run entire release process.
  > i docker_release_dev_image
  ```

#### Experiment in a local image

- To install packages in an image, do `i docker_bash`

  ```bash
  # Switch to root and install package.
  > sudo su -
  > source /venv/bin/activate
  > pip install <package>

  # Switch back to user.
  > exit
  ```

- You should test that the package is installed for your user, e.g.,
  ```bash
  > source /venv/bin/activate python -c "import foobar; print(foobar);print(foobar.__version__)"
  ```
- You can now use the package in this container. Note that if you exit the
  container, the modified image is lost, so you need to install it again.
- You can save the modified image, tagging the new image as local, while the
  container is still running.
- Copy your Container ID. You can find it
  - In the docker bash session, e.g., if the command line in the container
    starts with `user_1011@da8f3bb8f53b:/app$`, your Container ID is
    `da8f3bb8f53b`
  - By listing running containers, e.g., run `docker ps` outside the container
- Commit image
  ```bash
  > docker commit <Container ID> <IMAGE>/cmamp:local-$USER
  ```
  - E.g.
    `docker commit da8f3bb8f53b 665840871993.dkr.ecr.us-east-1.amazonaws.com/cmamp:local-julias`
- If you are running inside a notebook using `i docker_jupyter` you can install
  packages using a one liner `! sudo su -; source ...; `

### Github Actions (CI)

- To run a single test in GH Action
  - Create a branch
  - Change .github/workflows/fast_tests.yml
    ```bash
    run: invoke run_fast_tests
    --pytest-opts="helpers/test/test_git.py::Test_git_modified_files1::test_get_modified_files_in_branch1
    -s --dbg"
    ```

### Pytest Workflows

- From
  [https://gist.github.com/kwmiebach/3fd49612ef7a52b5ce3a](https://gist.github.com/kwmiebach/3fd49612ef7a52b5ce3a)

- More details on running unit tests with `invoke` is
  [/docs/coding/all.run_unit_tests.how_to_guide.md](/docs/coding/all.run_unit_tests.how_to_guide.md)

#### Run with Coverage

```bash
> i run_fast_tests --pytest-opts="core/test/test_finance.py" --coverage
```

#### Capture Output of a Pytest

- Inside the `dev` container (i.e., docker bash)

  ```bash
  docker> pytest_log ...
  ```
  - This captures the output in a file `tmp.pytest_script.txt`

- Get the failed tests (inside or outside the container)
  ```bash
  [docker]> i pytest_failed
  dataflow/model/test/test_run_notebooks.py::Test_run_master_research_backtest_analyzer::test_run_notebook1
  dataflow/system/test/test_real_time_runner.py::TestRealTimeDagRunner1::test_simulated_replayed_time1
  dataflow/model/test/test_dataframe_modeler.py::TestDataFrameModeler::test_dump_json1
  ...
  ```

#### Run Only One Test Based on Its Name

- Outside the `dev` container

  ```bash
  > i find_test_class Test_obj_to_str1
  INFO: > cmd='/Users/saggese/src/venv/amp.client_venv/bin/invoke find_test_class Test_obj_to_str1'
  ## find_test_class: class_name abs_dir pbcopy
  10:18:42 - INFO  lib_tasks_find.py _find_test_files:44                  Searching from '.'

  # Copied to system clipboard:
  ./helpers/test/test_hobject.py::Test_obj_to_str1
  ```

#### Iterate on Stacktrace of Failing Test

- Inside docker bash
  ```bash
  docker> pytest ...
  ```
- The test fails: switch to using `pytest_log` to save the stacktrace to a file

  ```bash
  > pytest_log dataflow/model/test/test_tiled_flows.py::Test_evaluate_weighted_forecasts::test_combine_two_signals
  ...
  =================================== FAILURES ===================================
  __________ Test_evaluate_weighted_forecasts.test_combine_two_signals ___________
  Traceback (most recent call last):
    File "/app/dataflow/model/test/test_tiled_flows.py", line 78, in test_combine_two_signals
      bar_metrics = dtfmotiflo.evaluate_weighted_forecasts(
    File "/app/dataflow/model/tiled_flows.py", line 265, in evaluate_weighted_forecasts
      weighted_sum = hpandas.compute_weighted_sum(
  TypeError: compute_weighted_sum() got an unexpected keyword argument 'index_mode'
  ============================= slowest 3 durations ==============================
  2.18s call     dataflow/model/test/test_tiled_flows.py::Test_evaluate_weighted_forecasts::test_combine_two_signals
  0.01s setup    dataflow/model/test/test_tiled_flows.py::Test_evaluate_weighted_forecasts::test_combine_two_signals
  0.00s teardown dataflow/model/test/test_tiled_flows.py::Test_evaluate_weighted_forecasts::test_combine_two_signals
  ```

- Then from outside `dev` container launch `vim` in quickfix mode

  ```bash
  > invoke traceback
  ```

- The short form is `it`

#### Iterating on a Failing Regression Test

- The workflow is:

  ```bash
  # Run a lot of tests, e.g., the entire regression suite.
  > pytest ...
  # Some tests fail.

  # Run the `pytest_repro` to summarize test failures and to generate commands to reproduce them.
  > invoke pytest_repro
  ```

#### Detect Mismatches with Golden Test Outcomes

- The command is

  ```bash
  > i pytest_find_unused_goldens
  ```

- The specific dir to check can be specified with the `dir_name` parameter.
- The invoke detects and logs mismatches between the tests and the golden
  outcome files.
  - When goldens are required by the tests but the corresponding files do not
    exist
    - This usually happens if the tests are skipped or commented out.
    - Sometimes it's a FP hit (e.g. the method doesn't actually call
      `check_string` but instead has it in a string, or `check_string` is called
      on a missing file on purpose to verify that an exception is raised).
  - When the existing golden files are not actually required by the
    corresponding tests.
    - In most cases it means the files are outdated and can be deleted.
    - Alternatively, it can be a FN hit: the test method A, which the golden
      outcome corresponds to, doesn't call `check_string` directly, but the
      test's class inherits from a different class, which in turn has a method B
      that calls `check_string`, and this method B is called in the test method
      A.
- For more details see
  [CmTask528](https://github.com/cryptokaizen/cmamp/issues/528).

### Lint Workflows

#### Lint Everything

```bash
> i lint --phases="amp_isort amp_class_method_order amp_normalize_import
amp_format_separating_line amp_black" --files='$(find . -name "\*.py")'
```
