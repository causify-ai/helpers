

<!-- toc -->

- [How to create a runnable dir](#how-to-create-a-runnable-dir)
  * [Definition](#definition)
  * [A runnable dir as sub directory under a super-repo](#a-runnable-dir-as-sub-directory-under-a-super-repo)
    + [1) Turn the repo into a super-repo with helpers](#1-turn-the-repo-into-a-super-repo-with-helpers)
    + [2) Copy and customize files in the top dir](#2-copy-and-customize-files-in-the-top-dir)
    + [3) Copy and customize files in `devops`](#3-copy-and-customize-files-in-devops)
    + [4) Copy and customize files in thin_client](#4-copy-and-customize-files-in-thin_client)
    + [5) Build a container for a runnable dir](#5-build-a-container-for-a-runnable-dir)
    + [6) Test the code](#6-test-the-code)
      - [Release the Docker image](#release-the-docker-image)

<!-- tocstop -->

# How to create a runnable dir

## Definition

- A runnable dir is a directory containing code and a `devops` dir so that it
  can build its own container storing all the dependencies to run and be tested
- A runnable dir can be
  - A super-repo (e.g. `//cmamp`, `//quant_dashboard`)
    - Follow
      [all.create_a_super_repo_with_helpers.how_to_guide.md](all.create_a_super_repo_with_helpers.how_to_guide.md)
      to create a runnable dir that is a super repo
  - A sub directory under a super-repo (e.g. `//cmamp/ck.infra`)

## A runnable dir as sub directory under a super-repo

### 1) Turn the repo into a super-repo with helpers

- Follow
  [all.create_a_super_repo_with_helpers.how_to_guide.md](all.create_a_super_repo_with_helpers.how_to_guide.md)
  to turn the repo into a super-repo with helpers
- For example, for `//cmamp`, the resulting root directory should have a
  structure like:
  ```bash
  > ls -1
  ...
  dev_scripts_cmamp
  ...
  helpers_root
  ...
  ```

### 2) Copy and customize files in the top dir

- Some files need to be copied from `helpers` to the runnable dir to configure
  various tools (e.g., dev container workflow, `pytest`, `invoke`)
  ```bash
  > (cd helpers_root; git pull)
  > DST_DIR="ck.infra"; echo $DST_DIR
  > cp helpers_root/{changelog.txt,conftest.py,pytest.ini,invoke.yaml,repo_config.py,tasks.py} $DST_DIR
  ```
  - `changelog.txt`: this is copied from the repo that builds the used container
    or started from scratch for a new container
    ```bash
    > cat $DST_DIR/changelog.txt
    # cmamp-infra-1.0.0
    - 2024-10-16
    - First release
    ```
  - `conftest.py`: needed to configure `pytest`
  - `pytest.ini`: needed to configure `pytest` preferences
  - `invoke.yaml`: needed configure `invoke`
  - `repo_config.py`: store information about this specific repo (e.g., name,
    used container)
    - This needs to be modified
    ```python
    _REPO_NAME = "cmamp"
    ...
    _DOCKER_IMAGE_NAME = "cmamp-infra"
    ```
  - `tasks.py`: the `invoke` tasks available in this container
    - This needs to be modified
  - TODO(gp): Some files (e.g., `conftest.py`, `invoke.yaml`) should be links to
    `helpers`

### 3) Copy and customize files in `devops`

- Copy the `devops` from `//helpers` as a template dir
  ```bash
  > (cd helpers_root; git pull)
  > DST_DIR="ck.infra"; echo $DST_DIR
  > cp -r helpers_root/devops $DST_DIR
  ```
- Follow the instructions in `docs/work_tools/all.devops_docker.reference.md`
  and `docs/work_tools/all.devops_docker.how_to_guide.md` to customize the files
  in order to build the Docker container
  - Typically, we might want to customize the following
    - `$DST_DIR/devops/docker_build/dev.Dockerfile`: if we need to use a base
      image with different Linux distro or version
    - `$DST_DIR/devops/docker_build/install_os_packages.sh`: if we need to add
      or remove OS packages
    - `$DST_DIR/devops/docker_build/pyproject.toml`: if we need to add or remove
      Python dependencies

### 4) Copy and customize files in thin_client

- Create the `dev_script` dir based off the template from `helpers`

  ```bash
  # Use a prefix based on the repo name and runnable dir name, e.g., `cmamp_infra`.
  > SRC_DIR="helpers_root/dev_scripts_helpers/thin_client"; echo $SRC_DIR
  > DST_PREFIX="cmamp_infra"
  > DST_DIR="dev_scripts_${DST_PREFIX}/thin_client"; echo $DST_DIR
  > mkdir -p $DST_DIR
  > cp "$SRC_DIR/setenv.sh" $DST_DIR
  ```

- The resulting `dev_script` should look like:

  ```bash
  > ls -1 $DST_DIR
  setenv.sh
  ```

- Customize `setenv.py`
  - `DIR_TAG`="cmamp_infra"
  - `IS_SUPER_REPO` = 1 (since this runnable directory sits under a super-repo)
    - TODO(heanh): Rename `IS_SUPER_REPO` var (See #135).
  - `VENV_TAG`="helpers" (reuse helpers if the new thin environment is not
    built)
  - Update PATH to the runnable dir
    ```bash
    # runnable dir is "ck.infra" in this case.
    SCRIPT_PATH="ck.infra/dev_scripts_${DIR_TAG}/thin_client/setenv.sh"
    DEV_SCRIPT_DIR="${GIT_ROOT_DIR}/ck.infra/dev_scripts_${DIR_TAG}"
    ```
    - TODO(heanh): Automatically infer them.

### 5) Build a container for a runnable dir

- Run the single-arch flow to test the flow

  ```bash
  > DST_DIR="ck.infra"
  > DST_PREFIX="cmamp_infra"
  > cd $DST_DIR
  > source dev_scripts_${DST_PREFIX}/thin_client/setenv.sh
  > i docker_build_local_image --version 1.0.0 --container-dir-name $DST_DIR
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  > i docker_push_dev_image --version 1.0.0
  ```

- Run the multi-arch flow
  ```bash
  > DST_DIR="ck.infra"
  > DST_PREFIX="cmamp_infra"
  > cd $DST_DIR
  > source dev_scripts_${DST_PREFIX}/thin_client/setenv.sh
  > i docker_build_local_image --version 1.0.0 --container-dir-name $DST_DIR --multi-arch "linux/amd64,linux/arm64"
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  > i docker_push_dev_image --version 1.0.0
  ```

### 6) Test the code

- Run tests from the runnable dir (e.g. `cmamp/ck.infra`)

  ```bash
  > cd $DST_DIR
  > i run_fast_tests
  > i run_slow_tests
  ```

- Run tests from the root dir (e.g. `cmamp`)
  - TODO(heanh): Add support for recusive pytest run
  ```bash
  > main_pytest.py run_fast_tests --dir ck.infra
  > main_pytest.py run_slow_tests --dir ck.infra
  ```

#### Release the Docker image

- TODO(gp): Add details




# Get fresh copy of the repo and its submodules.
heanhs@dev1:~/src$ git clone --recursive git@github.com:causify-ai/cmamp.git cmamp2

# Checkout the branch that contains the changes.
heanhs@dev1:~/src/cmamp2$ git checkout CmampTask10224_Make_infra_dir_releasable_2

# Go to the helpers_root directory.
heanhs@dev1:~/src/cmamp2$ cd helpers_root/

# Checkout the branch that contains fixes.
heanhs@dev1:~/src/cmamp2/helpers_root$ git checkout TutorialsTask1_Create_releasable_dir

# Go runnable directory.
heanhs@dev1:~/src/cmamp2/helpers_root$ cd ..
heanhs@dev1:~/src/cmamp2$ cd ck.infra/

# Activate the virtual environment.
heanhs@dev1:~/src/cmamp2/ck.infra$ source devops/setenv.sh

# Run tests from runnable dir.
(client_venv.helpers) heanhs@dev1:~/src/cmamp2/ck.infra$ i run_fast_tests
