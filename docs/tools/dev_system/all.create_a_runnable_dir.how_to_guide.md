<!-- toc -->

- [How to create a runnable dir](#how-to-create-a-runnable-dir)
  * [Definition](#definition)
  * [A runnable dir as sub directory under a super-repo](#a-runnable-dir-as-sub-directory-under-a-super-repo)
    + [1) Turn the repo into a super-repo with helpers](#1-turn-the-repo-into-a-super-repo-with-helpers)
    + [2) Copy and customize files in the top dir](#2-copy-and-customize-files-in-the-top-dir)
    + [3) Copy and customize files in `devops`](#3-copy-and-customize-files-in-devops)
    + [4) Copy and customize files in thin_client](#4-copy-and-customize-files-in-thin_client)
    + [5) Replace files with symbolic links](#5-replace-files-with-symbolic-links)
    + [6) Commit changes](#6-commit-changes)
    + [7) Build a container for a runnable dir](#7-build-a-container-for-a-runnable-dir)
    + [8) Test the code](#8-test-the-code)
    + [9) Add the dependency lock files to the commit](#9-add-the-dependency-lock-files-to-the-commit)
    + [10) Release the Docker image](#10-release-the-docker-image)
    + [11) Update and release a new version of the image](#11-update-and-release-a-new-version-of-the-image)

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

```bash
> export CSFY_RUNNABLE_DIR="ck.infra"
> export CSFY_RUNNABLE_DIR_SUFFIX="cmamp_infra"
```

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
  > echo $CSFY_RUNNABLE_DIR
  > mkdir $CSFY_RUNNABLE_DIR
  > cp helpers_root/{changelog.txt,conftest.py,pytest.ini,invoke.yaml,repo_config.yaml,tasks.py} $CSFY_RUNNABLE_DIR
  ```
  - `changelog.txt`: this is copied from the repo that builds the used container
    or started from scratch for a new container
    ```bash
    > vim $CSFY_RUNNABLE_DIR/changelog.txt
    # cmamp-infra-1.0.0
    - 2024-10-16
    - First release
    ```
  - `conftest.py`: needed to configure `pytest`
  - `pytest.ini`: needed to configure `pytest` preferences
  - `invoke.yaml`: needed configure `invoke`
  - `runnable_dir`: needed to be created as it is used for automated discovery
    of runnable dirs for `pytest` runs
    ```bash
    > touch $CSFY_RUNNABLE_DIR/runnable_dir
    ```
  - `repo_config.yaml`: store information about this specific repo (e.g., name,
    used container)
    - This needs to be modified
    ```bash
    > vim $CSFY_RUNNABLE_DIR/repo_config.yaml
    repo_info:
      repo_name: cmamp
    ...
    docker_info:
      docker_image_name: cmamp-infra
    ...
    runnable_dir_info:
      use_helpers_as_nested_module: True
      ...
      dir_suffix: cmamp_infra
    ```
  - `tasks.py`: the `invoke` tasks available in this container
    - This can be modified if needed

### 3) Copy and customize files in `devops`

- Copy the `devops` from `//helpers` as a template dir
  ```bash
  > (cd helpers_root; git pull)
  > cp -r helpers_root/devops $CSFY_RUNNABLE_DIR
  ```
- Follow the instructions in
  [`/docs/work_tools/all.devops_docker.reference.md`](/docs/work_tools/all.devops_docker.reference.md)
  and
  [`/docs/work_tools/all.devops_docker.how_to_guide.md`](/docs/work_tools/all.devops_docker.how_to_guide.md)
  to customize the files in order to build the Docker container
  - Typically, we might want to customize the following
    - `$CSFY_RUNNABLE_DIR/devops/docker_build/dev.Dockerfile`: if we need to use
      a base image with different Linux distro or version
    - `$CSFY_RUNNABLE_DIR/devops/docker_build/install_os_packages.sh`: if we
      need to add or remove OS packages
    - `$CSFY_RUNNABLE_DIR/devops/docker_build/pyproject.toml`: if we need to add
      or remove Python dependencies
- Always trim
  [`/devops/docker_build/pyproject.toml`](/devops/docker_build/pyproject.toml)
  to only include the dependancies requred by the runnable dir

### 4) Copy and customize files in thin_client

- Create the `dev_scripts_{runnable_dir_suffix}` dir based off the template from
  `helpers`

  ```bash
  # Use a suffix based on the repo name and runnable dir name, e.g., `cmamp_infra`.
  > SRC_DIR="./helpers_root/dev_scripts_helpers/thin_client"; echo $SRC_DIR
  > DST_DIR="${CSFY_RUNNABLE_DIR}/dev_scripts_${CSFY_RUNNABLE_DIR_SUFFIX}/thin_client"; echo $DST_DIR
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
  > ./helpers_root/helpers/create_links.py --src_dir ./helpers_root --dst_dir $CSFY_RUNNABLE_DIR --replace_links --use_relative_paths
  ```

- Refer to
  [Managing common files](/docs/work_tools/dev_system/all.runnable_repo.reference.md#managing-common-files)
  for explanation
- Refer to
  [Managing symbolic links between directories](/docs/work_tools/dev_system/all.replace_common_files_with_script_links.md)
  for how to use the commands

### 6) Commit changes

- Commit changes
  ```bash
  > git add $CSFY_RUNNABLE_DIR
  > git commit -m "Add runnable dir"
  ```

### 7) Build a container for a runnable dir

- Run the single-arch flow to test the flow

  ```bash
  > cd $CSFY_RUNNABLE_DIR
  > source dev_scripts_${CSFY_RUNNABLE_DIR_SUFFIX}/thin_client/setenv.sh
  > i docker_build_local_image --version 1.0.0 --container-dir-name $CSFY_RUNNABLE_DIR
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  ```

- Run the multi-arch flow
  ```bash
  > cd $CSFY_RUNNABLE_DIR
  > source dev_scripts_${CSFY_RUNNABLE_DIR_SUFFIX}/thin_client/setenv.sh
  > i docker_build_local_image --version 1.0.0 --container-dir-name $CSFY_RUNNABLE_DIR --multi-arch "linux/amd64,linux/arm64"
  > i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull --version 1.0.0
  ```

### 8) Test the code

- Run tests from the runnable dir (e.g. `cmamp/ck.infra`)

  ```bash
  # If the version of the locally built image is 1.0.0.
  > cd $CSFY_RUNNABLE_DIR
  > i run_fast_tests --version 1.0.0
  > i run_slow_tests --version 1.0.0
  ```

  TODO(heanh): Add support for `skip_pull` so we can run tests without creating
  a registry first. For example,

  ```bash
  > i run_fast_tests --version 1.0.0 --skip-pull
  > i run_slow_tests --version 1.0.0 --skip-pull
  ```

- Run tests from the root dir (e.g. `cmamp`)
  ```bash
  > main_pytest.py run_fast_tests --dir ck.infra
  > main_pytest.py run_slow_tests --dir ck.infra
  ```

### 9) Add the dependency lock files to the commit

```bash
> cd $CSFY_RUNNABLE_DIR
> git add devops/docker_build/poetry.lock
> git add devops/docker_build/pip_list.txt
> git commit -m "Update dependencies"
```

### 10) Release the Docker image

- Refer to the following docs for more info on image releases
  - [docs/tools/dev_system/all.devops_docker.how_to_guide.md#release-a-docker-image](/docs/tools/dev_system/all.devops_docker.how_to_guide.md#release-a-docker-image)

- To create new registory to store the image, please contact Infra team.

- Release to ECR
  - This is required for running the container from the dev/prod servers

  ```bash
  > i docker_push_dev_image --version <version>
  ```
  - Or run the following command to build, test, and release the image

  ```bash
  > i docker_release_dev_image --version <version> --container-dir-name $CSFY_RUNNABLE_DIR
  ```

- Release to GHCR
  - This is required for running the container from GH Actions CI/CD pipelines
  - TODO(heanh): Can we create an invoke target for this?
  ```bash
  > docker login ghcr.io -u <username> -p <personal_access_token>
  > docker tag 623860924167.dkr.ecr.eu-north-1.amazonaws.com/<image_name>:dev ghcr.io/causify-ai/<image_name>:dev
  > docker push ghcr.io/causify-ai/<image_name>:dev
  ```

### 11) Update and release a new version of the image

We release a new version of the Docker image whenever we need to update its
dependencies

1. Modify changelog

- Specify what was changed
- Pick the release version according to semantic versioning convention
- For example for version 1.2.3:
  - 1 is major, 2 is minor, 3 is patch

```bash
> cd $CSFY_RUNNABLE_DIR
> source dev_scripts_${CSFY_RUNNABLE_DIR_SUFFIX}/thin_client/setenv.sh
> vim changelog.txt

# cmamp-infra-1.2.0
- 2025-05-18
- Add support for Kubernetes Kustomize
- Upgrade `kubectl` to v1.31.0
- Add `yq` command line tool
```

2. Modify dependencies list

- Modify `$CSFY_RUNNABLE_DIR/devops/docker_build/install_os_packages.sh` to add
  or remove OS packages
- Modify `$CSFY_RUNNABLE_DIR/devops/docker_build/pyproject.toml` to add or
  remove Python packages

3. Build the image locally

```bash
# Build the image.
> i docker_build_local_image --version 1.2.0 --container-dir-name $CSFY_RUNNABLE_DIR

# Tag the image as dev.
> i docker_tag_local_image_as_dev --version 1.2.0
```

4. Add the dependency lock files to the commit

```bash
> cd $CSFY_RUNNABLE_DIR
> git add devops/docker_build/poetry.lock
> git add devops/docker_build/pip_list.txt
> git commit -m "Update dependencies"
```

4. Make sure we can run the container

```bash
> i docker_bash --skip-pull --stage local --version 1.2.0
> i docker_jupyter --skip-pull --stage local --version 1.2.0
```

5. Make sure all tests pass

```bash
# Run tests.
> i run_fast_tests --stage local --version 1.2.0
> i run_slow_tests --stage local --version 1.2.0
```

6. Release the images to remote registries
