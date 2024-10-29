

<!-- toc -->

- [How to create a runnable dir](#how-to-create-a-runnable-dir)
  * [Definition](#definition)
  * [A runnable dir as sub directory under a super-repo](#a-runnable-dir-as-sub-directory-under-a-super-repo)
    + [1) Turn the repo into a super-repo with helpers](#1-turn-the-repo-into-a-super-repo-with-helpers)
    + [2) Copy and customize files in the top dir](#2-copy-and-customize-files-in-the-top-dir)
    + [3) Copy and customize files in `devops`](#3-copy-and-customize-files-in-devops)
      - [Build a container for a runnable dir](#build-a-container-for-a-runnable-dir)

<!-- tocstop -->

# How to create a runnable dir

## Definition

A runnable dir is a directory with its own devops dir so that it can have its
own container and dependencies (to run and to test)

- A runnable dir can be a super-repo (e.g. `//cmamp`, `//quant_dashboard`)
  - Follow
    [all.create_a_super_repo_with_helpers.how_to_guide.md](all.create_a_super_repo_with_helpers.how_to_guide.md)
    to create a runnable dir that is a super repo
- A runnable dir can be a sub directory under a super-repo (e.g.
  `//cmamp/ck.infra`)

## A runnable dir as sub directory under a super-repo

### 1) Turn the repo into a super-repo with helpers

- Follow
  [all.create_a_super_repo_with_helpers.how_to_guide.md](all.create_a_super_repo_with_helpers.how_to_guide.md)
  to turn the repo into a super-repo with helpers
- For example, for `//cmamp`, the resulting root directory shoud have:
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
  - `conftest.py`: configure `pytest`
  - `pytest.ini`: configure `pytest` preferences
  - `invoke.yaml`: configure `invoke`
  - `repo_config.py`: stores information about this specific repo (e.g., name,
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

#### Build a container for a runnable dir

- Copy the `devops` template dir
  ```bash
  > (cd helpers_root; git pull)
  > DST_DIR="ck.infra"; echo $DST_DIR
  > cp -r helpers_root/devops $DST_DIR
  ```
- Follow the instructions in `docs/work_tools/all.devops_docker.reference.md`
  and `docs/work_tools/all.devops_docker.how_to_guide.md`
- For example, we might want to customize the following
  - `$DST_DIR/devops/docker_build/dev.Dockerfile`: if we need to use a base
    image with different Linux distro or version
  - `$DST_DIR/devops/docker_build/install_os_packages.sh`: if we need to add or
    remove OS packages
  - `$DST_DIR/devops/docker_build/pyproject.toml`: if we need to add or remove
    Python dependencies

- Set switch variables in `$DST_DIR/devops/docker_run/docker_setenv.sh` and
  `$DST_DIR/devops/docker_run/entrypoint.sh`
  - `IS_SUPER_REPO` = 1 (since this runnable directory that sits under a
    super-repo)
  - `IS_SUB_DIR` = 1 (since this runnable directory is a sub directory)
    - Refer to switch variables definitions in
      `docs/work_tools/all.devops_docker.reference.md` for detailed explanation

- Run the single-arch flow
  ```bash
  > REPO_NAME="cmamp"
  > source dev_scripts_${REPO_NAME}/thin_client/setenv.sh
  > cd $DST_DIR
  > i docker_build_local_image --version 1.0.0 --container-dir-name $DST_DIR
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  > i docker_push_dev_image --version 1.0.0
  ```
- Run the multi-arch flow

  ```bash
  > REPO_NAME="cmamp"
  > source dev_scripts_${REPO_NAME}/thin_client/setenv.sh
  > cd $DST_DIR
  > i docker_build_local_image --version 1.0.0 --container-dir-name $DST_DIR --multi-arch "linux/amd64,linux/arm64"
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  > i docker_push_dev_image --version 1.0.0
  ```

- Run tests from the runnable dir (e.g. `cmamp/ck.infra`)

  ```bash
  > cd $DST_DIR
  > i run_fast_tests
  > i run_slow_tests
  ```

- Run tests from the root dir (e.g. `cmamp`)
  ```bash
  > main_pytest.py run_fast_tests --dir ck.infra
  > main_pytest.py run_slow_tests --dir ck.infra
  ```
