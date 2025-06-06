<!-- toc -->

- [How to create a runnable dir](#how-to-create-a-runnable-dir)
  * [Definition](#definition)
  * [A runnable dir as sub directory under a super-repo](#a-runnable-dir-as-sub-directory-under-a-super-repo)
    + [1) Turn the repo into a super-repo with helpers](#1-turn-the-repo-into-a-super-repo-with-helpers)
    + [2) Copy and customize files in the top dir](#2-copy-and-customize-files-in-the-top-dir)
    + [3) Copy and customize files in `devops`](#3-copy-and-customize-files-in-devops)
    + [4) Copy and customize files in thin_client](#4-copy-and-customize-files-in-thin_client)
    + [5) Replace files with symbolic links](#5-replace-files-with-symbolic-links)
    + [6) Build a container for a runnable dir](#6-build-a-container-for-a-runnable-dir)
    + [7) Test the code](#7-test-the-code)
    + [8) Create a New Release of the Image](#8-create-a-new-release-of-the-image)
      - [Release the Docker image](#release-the-docker-image)

<!-- tocstop -->

# How to create a runnable dir

## Definition

- A runnable dir is a directory containing code and a `devops` dir so that it
  can build its own container storing all the dependencies to run and be tested
- A runnable dir can be
  - A super-repo (e.g. `//cmamp`, `//quant_dashboard`)
    - Follow
      [all.create_a_super_repo_with_helpers.how_to_guide.md](/docs/work_tools/dev_system/all.create_a_super_repo_with_helpers.how_to_guide.md)
      to create a runnable dir that is a super repo
  - A sub directory under a super-repo (e.g. `//cmamp/ck.infra`)

## A runnable dir as sub directory under a super-repo

### 1) Turn the repo into a super-repo with helpers

- Follow
  [all.create_a_super_repo_with_helpers.how_to_guide.md](/docs/work_tools/dev_system/all.create_a_super_repo_with_helpers.how_to_guide.md)
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
  > cp helpers_root/{changelog.txt,conftest.py,pytest.ini,invoke.yaml,repo_config.yaml,tasks.py} $DST_DIR
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
  - `repo_config.yaml`: store information about this specific repo (e.g., name,
    used container)
    - This needs to be modified
    ```yaml
    repo_info:
      repo_name: cmamp
    ...
    docker_info:
      docker_image_name: cmamp-infra
    ...
    runnable_dir_info:
      use_helpers_as_nested_module: 1
      ...
      dir_suffix: cmamp_infra
    ```
  - `tasks.py`: the `invoke` tasks available in this container
    - This can be modified if needed

### 3) Copy and customize files in `devops`

- Copy the `devops` from `//helpers` as a template dir
  ```bash
  > (cd helpers_root; git pull)
  > DST_DIR="ck.infra"; echo $DST_DIR
  > cp -r helpers_root/devops $DST_DIR
  ```
- Follow the instructions in
  [`/docs/work_tools/all.devops_docker.reference.md`](/docs/work_tools/all.devops_docker.reference.md)
  and
  [`/docs/work_tools/all.devops_docker.how_to_guide.md`](/docs/work_tools/all.devops_docker.how_to_guide.md)
  to customize the files in order to build the Docker container
  - Typically, we might want to customize the following
    - `$DST_DIR/devops/docker_build/dev.Dockerfile`: if we need to use a base
      image with different Linux distro or version
    - `$DST_DIR/devops/docker_build/install_os_packages.sh`: if we need to add
      or remove OS packages
    - `$DST_DIR/devops/docker_build/pyproject.toml`: if we need to add or remove
      Python dependencies
- Always trim
  [`/devops/docker_build/pyproject.toml`](/devops/docker_build/pyproject.toml)
  to only include the dependancies requred by the runnable dir

### 4) Copy and customize files in thin_client

- Create the `dev_scripts_{dir_name}` dir based off the template from `helpers`

  ```bash
  # Use a suffix based on the repo name and runnable dir name, e.g., `cmamp_infra`.
  > SRC_DIR="./helpers_root/dev_scripts_helpers/thin_client"; echo $SRC_DIR
  > DST_SUFFIX="cmamp_infra"
  > DST_DIR="./ck.infra/dev_scripts_${DST_SUFFIX}/thin_client"; echo $DST_DIR
  > mkdir -p $DST_DIR
  > cp "$SRC_DIR/setenv.sh" $DST_DIR
  ```

- The resulting `dev_script` should look like:

  ```bash
  > ls -1 $DST_DIR
  setenv.sh
  ```

- Replace file with symbolic links

  ```bash
  > echo $SRC_DIR
  ./helpers_root/dev_scripts_helpers/thin_client
  > echo $DST_DIR
  ./ck.infra/dev_scripts_cmamp_infra/thin_client
  > ./helpers_root/helpers/create_links.py --src_dir $SRC_DIR --dst_dir $DST_DIR --replace_links --use_relative_paths
  ```

### 5) Replace files with symbolic links

- Some common files can be replaced with symbolic links

  ```bash
  # Runnable dir is "ck.infra" in this case.
  ./helpers_root/helpers/create_links.py --src_dir ./helpers_root --dst_dir ./ck.infra --replace_links --use_relative_paths
  ```

- Refer to
  [Managing common files](/docs/work_tools/dev_system/all.runnable_repo.reference.md#managing-common-files)
  for explanation
- Refer to
  [Managing symbolic links between directories](/docs/work_tools/dev_system/all.replace_common_files_with_script_links.md)
  for how to use the commands

### 6) Build a container for a runnable dir

- Run the single-arch flow to test the flow

  ```bash
  > DST_DIR="ck.infra"
  > DST_SUFFIX="cmamp_infra"
  > cd $DST_DIR
  > source dev_scripts_${DST_SUFFIX}/thin_client/setenv.sh
  > i docker_build_local_image --version 1.0.0 --container-dir-name $DST_DIR
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  > i docker_push_dev_image --version 1.0.0
  ```

- Run the multi-arch flow
  ```bash
  > DST_DIR="ck.infra"
  > DST_SUFFIX="cmamp_infra"
  > cd $DST_DIR
  > source dev_scripts_${DST_SUFFIX}/thin_client/setenv.sh
  > i docker_build_local_image --version 1.0.0 --container-dir-name $DST_DIR --multi-arch "linux/amd64,linux/arm64"
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  > i docker_push_dev_image --version 1.0.0
  ```

### 7) Test the code

- Run tests from the runnable dir (e.g. `cmamp/ck.infra`)

  ```bash
  # If the version of the locally built image is 1.0.0.
  > i run_fast_tests --version 1.0.0
  > i run_slow_tests --version 1.0.0
  ```

- Run tests from the root dir (e.g. `cmamp`)
  - TODO(heanh): Add support for recusive pytest run
  ```bash
  > main_pytest.py run_fast_tests --dir ck.infra
  > main_pytest.py run_slow_tests --dir ck.infra
  ```

### 8) Create a New Release of the Image

We release a new version of the Docker image whenever we need to update its
dependencies.

1. Modify changelog to specify what was changed and pick a semantic version
   Example:

   ```bash
   > cd {research_dir}
   > source dev_scripts_{runnable_dir_suffix}/thin_client/setenv.sh
   > cat changelog.txt

   # cmamp-causal-kg-1.0.0
   - 2025-05-18
   - Initial release
   ```

2. Modify dependencies Update as needed:
   - OS packages:/devops/docker_build/install_os_packages.sh
   - Python packages: /devops/docker_build/pyproject.toml

3. Build the image locally

   ```bash
   # Build the image.
   > i docker_build_local_image --version 1.0.0 --container-dir-name {dir_name}

   # Tag the image as dev.
   > i docker_tag_local_image_as_dev --version 1.0.0
   ```

4. Bash into the container

   ```bash
   > i docker_bash --skip-pull --stage local --version 1.0.0

   # Run tests.
   > i run_fast_tests --stage local --version 1.0.0
   > i run_slow_tests --stage local --version 1.0.0
   > i run_superslow_tests --stage local --version 1.0.0
   ```

#### Release the Docker image

- TODO(gp): Add details
