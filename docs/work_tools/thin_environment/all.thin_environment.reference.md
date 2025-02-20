<!-- toc -->

- [Basic concepts](#basic-concepts)
  * [Naming objects composed across repos](#naming-objects-composed-across-repos)
- [Files](#files)
  * [General utils](#general-utils)
  * [Building the thin environment](#building-the-thin-environment)
  * [Configuring a shell](#configuring-a-shell)
  * [Tmux session](#tmux-session)
  * [How to test](#how-to-test)
  * [Build container](#build-container)

<!-- tocstop -->

# Basic concepts

Each repo relies on several concept:

- "thin environment": a Python environment that contains the minimal number of
  packages to run commands and start the development system in Docker
- "set env" script: it is used to configured a shell inside the thin environment
- "tmux" script: it is used to create a `tmux` session with our standard setup
  for the repo (e.g., multiple windows on different repo and sub-repos)
- "Docker environment": it contains all the libraries, packages, and
  dependencies for the actual development (e.g., run the tools, run the unit
  tests)
- "devops": it contains all the code to build containers for the specific repo

## Naming objects composed across repos

- We add a suffix representing the name of the repo any time we need to
  distinguish different objects
  - E.g., `dev_scripts_helpers` vs `dev_scripts_cmamp`
- For runnable dirs that are not top level, the suffix includes the name of the
  repo followed by the name of the runnable dir
  - E.g., `dev_scripts_cmamp_infra`, `dev_scripts_tutorial_tensorflow`
- We can't always use the `.` to separate the fields since `.` creates problems
  when importing Python files, and so we resort to using `_`

- On the one hand, we agree that the directory structure should help distinguish
  different objects
  - E.g., `//helpers/.../dev_scripts_helpers` vs `//cmamp/.../dev_scripts_cmamp`
- We keep files named in the same way underneath different directories

- Pros
  - It's easy to diff files in corresponding dirs
- Cons
  - The name is not enough to disambiguate files, but one needs to account for
    the full path of each file across different repos / directories

# Files

- The files involved are:
  ```bash
  > ls -l -1 dev_scripts_helpers/thin_client/
  __init__.py
  build.py
  requirements.txt
  setenv.sh
  sync_repo_thin_client.sh
  test_thin_client.sh
  thin_client_utils.py
  thin_client_utils.sh
  tmux.py
  ```

## General utils

- `thin_client_utils.sh`: contain common Bash code for the scripts in this dir
- `thin_client_utils.py`: contain common Python code for the scripts in this dir

## Building the thin environment

- `build.py`: build the thin environment
- `requirements.txt`: list of Python packages needed in the thin environment

## Configuring a shell

- `setenv.sh`: configure a shell to run the thin environment

## Tmux session

- `tmux.py`: a script to create the standard `tmux` set up

## How to test

- The script
  [`/dev_scripts_helpers/thin_client/test_helpers.sh`](/dev_scripts_helpers/thin_client/test_helpers.sh)
  tests `helpers`

- Build thin environment
  ```bash
  > dev_scripts_helpers/thin_client/build.py
  ```
- Source setenv
  ```bash
  > source dev_scripts_helpers/thin_client/setenv.sh
  ```
- Create the tmux session
  ```bash
  > dev_scripts_helpers/thin_client/tmux.py --create_global_link
  > dev_scripts_helpers/thin_client/tmux.py --index 1
  ```

## Build container

- Build the container

  ```bash
  > i docker_build_local_image --version 1.0.0
  > i docker_tag_local_image_as_dev --version 1.0.0
  ```

- Run the container
  ```bash
  > i docker_bash --skip-pull
  > i docker_jupyter
  ```
