# Basic concepts

Each repo relies on several concept:

- "thin environment": a Python environment that contains enough packages to run
  commands and start the development system in Docker
- "set env" script: it is used to configured a shell inside the thin environment
- "tmux" script: it is used to create a `tmux` session with our standard setup
  for the repo (e.g., multiple windows on different repo and sub-repos)
- Docker environment: it contains all the libraries, packages, and dependencies
  for the actual development (e.g., run the tools, run the unit tests)

## Naming objects composed across repos
- We add a suffix representing the name of the repo any time we need to
  distinguish different objects
  - E.g., `dev_scripts_helpers` vs `dev_scripts_cmamp`
- We can't always use the `.` to separate the fields since `.` creates problems
  when importing Python files, and so we resort to using `_`

- On the one hand, we agree that the directory structure should help distinguish
  different objects
  - E.g., `//helpers/.../dev_scripts` vs `//cmamp/.../dev_scripts`
- On the other hand, with the previous approach is that the same name easily create
  confusion and can be a source of bugs, since one needs to always keep track
  of the including dir

# Files

- The files involved in the various functions
  ```bash
  > ls -l -1 dev_scripts/thin_client/
  build.py
  requirements.txt
  setenv.helpers.sh
  setenv.template.sh
  thin_client_utils.py
  thin_client_utils.sh
  tmux.helpers.py
  tmux.template.py
  ```

## General utils

- `thin_client_utils.sh`: contain common Bash code for the scripts in this dir

## Building the thin environment

- `build.py`: build the thin environment
- `thin_client_utils.py`: contain common Python code for the scripts in this dir
- `requirements.txt`: list of Python packages needed in the thin environment

## Configuring a shell

- `setenv.helpers.sh`: configure a shell to run the thin environment
- `setenv.template.sh`: template for the set env script for a super-repo
  including `helpers`

## Tmux session

- `tmux.helpers.sh`: a script to create the standard `tmux` set up
- `tmux.template.sh`: template for the tmux script for a super-repo including
  `helpers`

## How to test

- Build thin environment
  ```bash
  > dev_scripts/thin_client/build.py
  ```
- Source setenv
  ```bash
  > source dev_scripts/thin_client/setenv.helpers.sh
  ```
- Create the tmux session
  ```bash
  > dev_scripts/thin_client/tmux.helpers.py --index 1
  ```

# How to create a super-repo including `helpers`

- Create the super-repo

- Add `helpers` as sub-repo
  ```bash
  > git submodule add <repository-url> <path>
  > git submodule add git@github.com:kaizen-ai/helpers.git helpers_root
  > git submodule init
  > git submodule update
  > git add .gitmodules helpers_root
  ```

- Create the `dev_script` dir
  ``` bash
  > PREFIX="sports_analytics"
  > DST_DIR="dev_scripts_${PREFIX}/thin_client"
  > mkdir $SDT_DIR
  > cp -r helpers_root/dev_scripts/thin_client/setenv.template.sh $DST_DIR/setenv.${PREFIX}.sh
  > cp -r helpers_root/dev_scripts/thin_client/tmux.template.sh $DST_DIR/tmux.${PREFIX}.sh
  ```

- It should look like:
  ```bash
  > ls -1 dev_scripts_sports_analytics/thin_client/*
  dev_scripts_sports_analytics/thin_client/setenv.sports_analytics.sh
  dev_scripts_sports_analytics/thin_client/tmux.sports_analytics.py
  ```
- Customize the `dev_scripts` dir
  - You need to decide if a new thin environment is needed or one can be reused
    (e.g., `helpers` one)

## How to test

- Make sure the setenv works
  ```bash
  > source dev_scripts_sports_analytics/thin_client/setenv.sports_analytics.sh
  ```

## Maintain the files in sync with the template

- Keep files in sync
  ```bash
  > vimdiff dev_scripts_sports_analytics/thin_client/setenv.sports_analytics.sh helpers_root/dev_scripts/thin_client/setenv.helpers.sh
  > vimdiff dev_scripts_sports_analytics/thin_client/setenv.sports_analytics.sh helpers_root/dev_scripts/thin_client/templates/setenv.template.sh
  ```

## Tmux links

- Create the global link
  ```bash
  > dev_scripts_sports_analytics/thin_client/tmux.sports_analytics.py --create_global_link
  ```

- Create the tmux session
  ```bash
  > dev_scripts_sports_analytics/thin_client/tmux.sports_analytics.py --index 1 --force_restart
  ```

## Create files

- Some files need to be copied from `helpers` to the root of the super-repo
  - `changelog.txt`: this is copied from the repo that builds the used container or
    started from scratch for a new container
  - `conftest.py`: configure `pytest`
  - `invoke.yaml`: configure `invoke`
  - `pytest.ini`: configure `pytest` preferences
  - `repo_config.py`: stores information about this specific repo (e.g., name, used
    container)
    - This needs to be modified
  - `tasks.py`: the `invoke` tasks available in this container
    - This needs to be modified
  - TODO(gp): Some should be links to `helpers`

## Build a container for a super-repo

- Copy the `devops` template dir
  ```bash
  > (cd helpers_root; git pull)
  > cp -r helpers_root/devops/templates/devops_with_build_stage devops
  ```
- If we don't need to build a container, but just reuse one we can delete
  the corresponding directory
  ```bash
  > rm -rf devops/docker_build
  ```
