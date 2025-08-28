<!-- toc -->

- [High level philosophy](#high-level-philosophy)
  * [Separate Docker containers](#separate-docker-containers)
  * [Pre-built vs build-on-the-fly containers](#pre-built-vs-build-on-the-fly-containers)
  * [Thin client](#thin-client)
  * [amp / cmamp container](#amp--cmamp-container)
  * [Stages](#stages)
    + [Local](#local)
    + [Dev](#dev)
    + [Prod](#prod)
  * [Registries](#registries)
- [invoke targets](#invoke-targets)
  * [Single-arch flow](#single-arch-flow)
  * [Multi-arch flow](#multi-arch-flow)
  * [Prod flow](#prod-flow)
- [How to test a package in a Docker container](#how-to-test-a-package-in-a-docker-container)
  * [Install a package in a container](#install-a-package-in-a-container)
  * [Hacky approach to patch up a container](#hacky-approach-to-patch-up-a-container)
- [Release a Docker image](#release-a-docker-image)
  * [Overview of how to release an image](#overview-of-how-to-release-an-image)
  * [How to add a Python package to dev image](#how-to-add-a-python-package-to-dev-image)
  * [How to find unused packages](#how-to-find-unused-packages)
  * [How to build a local image](#how-to-build-a-local-image)
  * [Testing the local image](#testing-the-local-image)
  * [Pass the local image to another user for testing](#pass-the-local-image-to-another-user-for-testing)
  * [Tag `local` image as `dev`](#tag-local-image-as-dev)
  * [Push image](#push-image)
  * [End-to-end flow for `dev` image](#end-to-end-flow-for-dev-image)
  * [Multi-architecture build](#multi-architecture-build)
  * [Release a multi-architecture dev image](#release-a-multi-architecture-dev-image)
    + [Overview](#overview)
    + [Pre-release check-list](#pre-release-check-list)
    + [Command to run the release flow](#command-to-run-the-release-flow)
    + [Post-release check-list](#post-release-check-list)
  * [Build prod image](#build-prod-image)
    + [QA for prod image](#qa-for-prod-image)
    + [End-to-end flow for `prod` image](#end-to-end-flow-for-prod-image)
  * [Release a multi-architecture prod image](#release-a-multi-architecture-prod-image)
    + [Overview](#overview-1)
  * [Flow for both dev and prod images](#flow-for-both-dev-and-prod-images)
- [Release flow](#release-flow)
  * [cmamp](#cmamp)
  * [QA flow](#qa-flow)

<!-- tocstop -->

# High level philosophy

- We use Docker extensively and assume you are familiar with Docker concepts and
  workflows
- A short tutorial about Docker is
  [/docs/tools/docker/all.docker.tutorial.md](/docs/tools/docker/all.docker.tutorial.md)

## Separate Docker containers

- We always want to separate things that don't need to run together in different
  containers along repos or "independently runnable / deployable directories"
  - E.g., `dev / prod cmamp`, `optimizer`, `im`, `oms`

- The rationale is that when we put too many dependencies in a single container,
  we start having huge containers that are difficult to deploy and are unstable
  in terms of building even when using tools like `poetry`.
- Each dir that can be "deployed" and run should have a `devops` dir to build /
  QA / release containers with all the needed dependencies

## Pre-built vs build-on-the-fly containers

1. Certain containers that need to be widely available to the team and deployed
   go through the release process and are stored in ECR (AWS and DockerHub)

2. Other containers that are lightweight and used only by one person can be
   built on the fly using `docker compose` / `docker build`.

- E.g., the `infra` container, containers to run a simple tools

3. Sometimes we install a dependency on the fly from inside the code, when it's
   needed only rarely and it doesn't justify being added to the Docker container
   - E.g., when we need to profile Python code, we install the package directly
     in the container

## Thin client

- To bootstrap the system we use a "thin client" which installs in a virtual env
  the minimum set of packages to run (e.g., installs `invoke`, `docker`, etc).

## amp / cmamp container

- The `dev` version is used to develop
- The `prod` version is used for deployment as shortcut to creating a smaller
  container with only the strictly needed dependencies

- In order to avoid shipping the monster `cmamp` dev / prod container, we want
  to start building smaller containers with only the dependencies that specific
  prod scripts need

## Stages

- A "stage" is a step (e.g., local, dev, prod) in our release workflow of Docker
  images, code, or infrastructure.
- To run a Docker container in a certain stage use the `stage` parameter
  - E.g. `i docker_bash --stage="local"` creates a bash session inside the local
    Docker `amp` container

### Local

- A `local` image is used to develop and test an update to the Docker container
  - E.g. after updating a package, installing a new package, etc.
- Local images can only be accessed locally by a developer, i.e. the team
  members can not / should not use local images
- In practice `local` images are like `dev` images but private to users and
  servers

### Dev

- A `dev` image is used by team members to develop our system
  - E.g., add new functionalities to the `cmamp` or `helpers` codebase
- The source code is mounted through a bind mount in Docker so that one can
  change the code and execute it in Docker, without rebuilding the container
- A local image is tested, blessed, and released as `dev` so that users and CI
  can pull it and use it knowing that it's sane

### Prod

- A `prod` image is used to run a system by final users
  - E.g., Linter inside `helpers`, some prod system inside Airflow
- It is self-contained (i.e., it has no dependencies) since it contains
  everything required to run a system
  - E.g., OS, Python packages code, code
- A `prod` image is typically created from the `dev` image by copying the
  released code inside the `prod` image

## Registries

- We use several Docker image registries
  - AWS ECR: images are used on the dev and prod servers
  - GHCR (GitHub Container Repo): images are used by the CI systems
  - DockerHub: images are used by developers on the public facing repo

- In practice we mirror the Docker images to make sure they are close to where
  they need to be used and they minimize downloading costs

# invoke targets

## Single-arch flow

- `docker_build_local_image`: build a "local" image, i.e., a release candidate
  for the "dev" image
- `docker_tag_local_image_as_dev`: promote "local" image to "dev" without
  pushing it to the remote
- `docker_push_dev_image`: push image to an image registry
- `docker_release_dev_image`: build, test the "dev" image and then release it to
  ECR

## Multi-arch flow

- `docker_tag_push_multi_build_local_image_as_dev`: build a "local" multi-arch
  image and tag it as "dev"
- `docker_release_multi_build_dev_image`: same as `docker_release_dev_image` but
  for multi-arch image

## Prod flow

- `docker_build_prod_image`: build a "prod" image from a dev image
- `docker_push_prod_image`: push the "prod" image to ECR
- `docker_push_prod_candidate_image`: push the "prod" candidate image to ECR
- `docker_build_multi_arch_prod_image`: build a multi arch. versioned "prod"
  image from a "dev" image
- `docker_tag_push_multi_arch_prod_image`: mark the multi-arch versioned "prod"
  image as "prod" and push them to the target registry
- `docker_release_prod_image`: build, test, and release the "prod" image to ECR
- `docker_release_multi_arch_prod_image`: build, test, and release to Docker
  registries the multi-arch prod image
- `docker_release_all`: release both the "dev" and "prod" image to ECR
- `docker_rollback_dev_image`: rollback the version of the "dev" image
- `docker_rollback_prod_image`: rollback the version of the "prod" image
- `docker_create_candidate_image`: create a new "prod" candidate image
- `docker_update_prod_task_definition`: update image in "prod" task definition
  to the desired version

# How to test a package in a Docker container

## Install a package in a container

- You can install a Python package with the following command in Docker
  ```bash
  docker> sudo /bin/bash -c "(source /venv/bin/activate; pip install yfinance)"
  docker> python -c "import finance"
  ```

## Hacky approach to patch up a container

- To patch up a container you can use the following instructions

  ```bash
  # After changing the container, create a new version of the container.
  > docker commit d2916dd5f122 \
      623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev_ccxtpr

  # Push the updated container to the repo.
  > docker push 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev_ccxtpro

  # Now you can pull the container on different machines.
  > docker pull 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev_ccxtpro

  # To use `docker_bash` you might need to retag it to match what the system expects
  > docker tag 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev_ccxtpro
  ```

# Release a Docker image

- All the `invoke` tasks to run the release flow are in
  [`/helpers/lib_tasks.py`](/helpers/lib_tasks.py)
- Depending on the type of changes sometimes one needs to rebuild only the
  `prod` image, other times one needs to rebuild also the `dev` image
- E.g.,
  - If you change Docker build-related things (e.g., add a Python package), you
    need to rebuild the `dev` image and then the `prod` image from the `dev`
    image
  - If you change the code for a production system, you need to create a new
    `prod` image

- We try to use the same build/release flow, conventions, and code for all the
  containers (e.g., `amp`, `cmamp`, `helpers`, `opt`)

## Overview of how to release an image

- The release flow consists of the following phases
  - Make changes to the image
    - E.g., add Python package through `poetry`, add an OS package, ...
  - Update the changelog
  - Build a local image
    - Run specific tests (e.g., make sure that the new packages are installed)
    - Run unit tests
    - Run QA tests
  - Tag local image as dev image
  - Push dev image to ECR, DockerHub, GHCR

- If there is also an associated prod image
  - Build prod image from dev image
    - Run unit tests
    - Run QA tests
  - Push prod image to ECR, DockerHub, GHCR

- The release flow is implemented in the `invoke` tasks:
  - E.g., `docker_release_dev_image`, `docker_release_prod_image`, etc.
  - These tasks are quite complex and perform many operations
  - Currently, we don't run them directly — instead, we execute the individual
    steps from the `invoke` tasks
  - Once the release process is more stable, we plan to run them directly

## How to add a Python package to dev image

- To add a new Python package to a Docker image you need to update `poetry`
  files and release a new image:
  - Add a new package to
    [`/devops/docker_build/pyproject.toml`](/devops/docker_build/pyproject.toml)
    file to the `[tool.poetry.dependencies]` section
  - E.g., to add `pytest-timeout` do:
    ```text
    [tool.poetry.dependencies]
    ...
    pytest-timeout = "*"
    ...
    ```
  - In general we use the latest version of a package `*` whenever possible
    - If the latest package has some problems with our codebase, we freeze the
      version of the problematic packages to a known-good version to get the
      tests back to green until the problem is solved. We switch back to the
      latest version once the problem is fixed
    - If you need to put a constraint on the package version, follow the
      [official docs](https://python-poetry.org/docs/dependency-specification/),
      and explain in a comment why this is needed making reference to GitHub
      issues

- To verify that package is installed correctly:
  - Build a local image
    - There are two options:
      - Update `poetry` and upgrade all packages to the latest versions
        ```bash
        > i docker_build_local_image --version {version} --poetry-mode="update"
        ```
      - Install packages from the current `poetry.lock` file without upgrading
        the packages
        ```bash
        > i docker_build_local_image --version <VERSION> --poetry-mode="no_update"
        ```
  - Run a docker container based on the local image
    ```bash
    > i docker_bash --stage local --version <VERSION>
    ```
  - Verify what package was installed with `pip show {package name}`, e.g.,
    ```bash
    > pip show pytest-rerunfailures
    Name: pytest-rerunfailures
    Version: 10.2
    Summary: pytest plugin to re-run tests to eliminate flaky failures
    ...
    Location: /venv/lib/python3.8/site-packages
    Requires: pytest, setuptools
    Required-by:
    ```
  - Run regressions for the local image, i.e.
    ```bash
    > i run_fast_tests --stage local --version <VERSION>
    > i run_slow_tests --stage local --version <VERSION>
    ```

- Update the changelog describing the new version
- Send a PR with the updated `poetry` files and any other change needed to make
  the tests pass
- Release the new image following the
  [Release a Docker image](#how-to-test-a-package-in-a-docker-container)
  section, use `--update-poetry` flag to resolve the dependencies

## How to find unused packages

- While installing Python packages we need to make sure that we do not install
  packages that are not used

- You can use the import-based approach using
  [`pipreqs`](https://github.com/bndr/pipreqs)
  - Under the hood it uses the regex below and `os.walk` for selected dir:
    ```python
    REGEXP = [
        re.compile(r'^import (.+)$'),
        re.compile(r'^from ((?!\.+).*?) import (?:.*)$')
    ]
    ```

- `pipreqs` has some limitations
  - Not all packages that we use are necessarily imported, e.g. `awscli`,
    `jupyter`, `pytest-cov`, etc. so `pipreqs` won't find these packages
  - The import name is not always equal to the package actual name, see the
    mapping [here](https://github.com/bndr/pipreqs/blob/master/pipreqs/mapping)

- Run a bash session inside a Docker container
- Install `pipreqs` with `sudo pip install pipreqs`
  - We install it temporary within a Docker bash session in order to introduce
    another dependency
  - You need to re-install `pipreqs` every time you create a new Docker bash
    session
- To run for a root dir do:
  ```bash
  docker> pipreqs . --savepath ./tmp.requirements.txt
  ```
- The command above will generate `./tmp.requirements.txt` with the list of the
  imported packages, e.g.,
  ```text
  amp==1.1.4
  async_solipsism==0.3
  beautifulsoup4==4.11.1
  botocore==1.24.37
  cvxopt==1.3.0
  cvxpy==1.2.0
  dill==0.3.4
  environs==9.5.0
  ...
  ```
- You can grep for a package name to see where it is used, e.g.,
  ```bash
  > jackpy "dill"
  helpers/hpickle.py:108:       import dill
  ...
  ```
- See the [official docs](https://github.com/bndr/pipreqs) for the advanced
  usage

## How to build a local image

- The `local` image is built using
  [`/devops/docker_build/dev.Dockerfile`](/devops/docker_build/dev.Dockerfile)
- This Dockerfile runs various scripts to install:
  - OS
  - Python
  - `venv` + Python packages
  - Jupyter extensions
  - Application-specific packages (e.g., for Linter)

- To build a local image run:

  ```bash
  > i docker_build_local_image --version 1.0.0

  # Build from scratch and not incrementally.
  > i docker_build_local_image --version 1.0.0 --no-cache

  # Update poetry package list.
  > i docker_build_local_image --version 1.0.0 --poetry-mode="update"

  # See more options:
  > i docker_build_local_image -h
  ```

- Once an image is built, it is tagged as `local-${user}-${version}`, e.g.,
  `local-saggese-1.0.0`
  ```
  Successfully tagged 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-gsaggese-1.0.9

  > docker image ls 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-gsaggese-1.0.9
  REPOSITORY                                         TAG                    IMAGE ID            CREATED                  SIZE
  665840871993.dkr.ecr.us-east-1.amazonaws.com/amp   local-gsaggese-1.0.9   cf16e3e3d1c7        Less than a second ago   2.75GB
  ```

- A local image is a candidate for becoming a `dev` image.
  ```
  > i run_fast_tests --stage local --version 1.0.0
  ```

## Testing the local image

- Compare the version of the packages in the different images

  ```bash
  > i docker_bash
  docker> pip list | tee pip_packages.dev.txt

  > i docker_bash --stage local --version 1.0.9
  docker> pip list | tee pip_packages.local.txt
  ```

- Or in one command:
  ```
  > i docker_cmd --cmd "pip list | tee pip_packages.dev.txt"; i docker_cmd --stage=local --version=1.0.9 --cmd "pip list | tee pip_packages.local.txt"
  > vimdiff pip_packages.dev.txt pip_packages.local.txt
  ```

- You can move the local image on different servers for testing by pushing it on
  ECR:
  ```
  > i docker_login
  > i docker push 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-gsaggese-1.1.0
  ```

## Pass the local image to another user for testing

- Push the local image built by a user to ECR registry
- For e.g., if the image is built by user `gsaggese`
  ```
  > i docker_login
  > i docker push 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-gsaggese-1.1.0
  ```

- From user session who wants to test: pull the local image from ECR
  ```
  > i docker pull 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-gsaggese-1.1.0
  ```

- Tag the local image from user `gsaggese`, who built the image, as
  `local-currentuser-1.1.0` for user `currentuser` who wants to test it
  ```
  > i docker tag 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-gsaggese-1.1.0 665840871993.dkr.ecr.us-east-1.amazonaws.com/amp:local-currentuser-1.1.0
  ```

- Run any kind of test using the local image. For e.g., to run fast tests
  ```
  > i run_fast_tests --stage local --version 1.1.0
  ```

- Check something inside the container
  ```
  > i docker_bash --stage local --version 1.1.0
  docker > pip freeze | grep pandas
  ```
- After testing and making sure the regressions are green, make sure to tag the
  image built by the initial user as `dev` and not the one tagged for the
  `current-user`
- This will make sure image is tagged for both `arm` and `x86` architecture on
  the remote registries

## Tag `local` image as `dev`

- A docker tag is just a way of referring to an image, in the same way Git tags
  refer to a particular commit in your history
- Basically, tagging is creating a reference from one image (e.g.,
  `local-saggese-1.0.0`) to another (`dev`)
- Once the `local` (e.g., `local-saggese-1.0.0`) image is tagged as `dev`, your
  `dev` image becomes equal to `local-saggese-1.0.0`
- `dev` image is also tagged with `dev-${version}`, e.g., `dev-1.0.0` to
  preserve history and allow for quick rollback
- Locally in Git repository a git tag `${repo_name}-${version}`, e.g.
  `cmamp-1.0.0` is created in order to properly control sync between code and
  container

## Push image

- Pushing `dev` or `prod` image means sending them to our docker registries
- Once an image is pushed, it can be used by the team members by running
  `i docker_pull`
- Local git tag `${repo_name}-${version}`, e.g. `cmamp-1.0.0`, is pushed at this
  stage to the remote repository to allow others to properly control sync
  between code and container.
- To be able to push an image to the ECR one should have permissions to do so

## End-to-end flow for `dev` image

<!-- TODO(gp): Merge with the rest, this is repeated -->

- Conceptually the flow consists of the following phases:

  1. Build a local image of docker
     - `i docker_build_local_image --version 1.0.0`
  2. Run fast tests to verify that nothing is broken
     - `i run_fast_tests --stage local --version 1.0.0`
  3. Run specific end-to-end tests by
  4. Tag `local` image as `dev`
     - `i docker_tag_local_image_as_dev --version 1.0.0`
  5. Push `dev` image to the docker registry
     - `i docker_push_dev_image --version 1.0.0`
  - The mentioned flow is executed by `Build dev image` GH action and that is a
    preferred way to do an image release

- For specific cases that can not be done via GH action see commands below:

  ```bash
  # To run the official flow end-to-end:
  > i docker_release_dev_image --version 1.0.0

  # To see the options:
  > i docker_release_dev_image -h

  # Run from scratch and not incrementally:
  > i docker_release_dev_image --version 1.0.0 --no-cache

  # Force an update to poetry to pick up new packages
  > i docker_release_dev_image --version 1.0.0 --update-poetry

  # Skip running the QA tests
  > i docker_release_dev_image --version 1.0.0 --no-qa-tests

  # Skip running the tests
  > i docker_release_dev_image --version 1.0.0 --skip-tests

  # Skip end-to-end tests
  > i docker_release_dev_image --version 1.0.0 --no-run-end-to-end-tests
  ```

## Multi-architecture build

- We allow to build multi-architecture Docker image using
  `docker_build_local_image`

  ```bash
  > i docker_build_local_image --version <VERSION> --multi-arch <PLATFORM NAME>
  ```
  - To build for specific platforms specify the platform name:
    - For `x86`: `linux/amd64`
    - For `arm`: `linux/arm64`
  - To build for both `arm` and `x86` architectures:
    ```
    > i docker_build_local_image --version <VERSION> --multi-arch linux/amd64,linux/arm64
    ```

- Multi-arch images are built using `docker buildx` which does not generate any
  local image by default
- Images are pushed to the remote registry and pulled for testing and usage
- To tag the local image as dev and push it to the target registry: e.g.,
  `aws_ecr.ck` or `dockerhub.causify` , use
  ```bash
  > i docker_tag_push_multi_build_local_image_as_dev --version <VERSION> --target-registry <TARGET>
  ```
- Once the image has been successfully pushed to both ECR and DockerHub
  registries, the subsequent step involves pushing the `dev` image to GHCR
  registry. However, this action currently requires manual execution due to
  restricted access
  - Access to the `causify-ai` packages is limited. To gain access, kindly reach
    out to GP, Samarth or Vlad
  - To proceed, perform a Docker login using your GitHub username and PAT
    (Personal Access Token):
    ```bash
    > docker login ghcr.io -u <username>
    ```
  - Tag the `dev` image to the GHCR namespace:
    ```bash
    > docker tag 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev ghcr.io/causify-ai/cmamp:dev
    ```
  - Push the tagged image to the GHCR registry:
    ```bash
    > docker push ghcr.io/causify-ai/cmamp:dev
    ```

## Release a multi-architecture dev image

### Overview

- Update the `changelog.txt` file with a description of the new version
- Build "local" image remotely in the CK AWS ECR registry and pull once it is
  built
- Run the `cmamp` regressions using a local image
- Run QA tests using a local image
- Tag the image as dev image and push it to the target Docker registries
- Tag the new `dev` image to GHCR namespace and push it to GHCR registry

### Pre-release check-list

Prerequisites:

- The new image is built locally

Check-list:

- Make sure that the regressions are passing when being run using the local
  image because we run the regressions as part of the official release flow,
  i.e. via `docker_release_multi_build_dev_image()`.
  - `cmamp`
    - [ ] Update the `changelog.txt` file
    - [ ] Fast tests
    - [ ] Slow tests
    - [ ] Super-slow test
    - [ ] QA tests

- Running regressions in the `orange` repository is not a part of the official
  image release flow so run them separately.
  - `orange`
    - [ ] Update the `changelog.txt` file
    - [ ] Fast tests
    - [ ] Slow tests
    - [ ] Super-slow test

- Example:
  ```bash
  > i run_fast_tests --version 1.10.0 --stage local
  ```
  where `1.10.0` is the new version of the image with stage as local.

### Command to run the release flow

- To run the release flow

  ```bash
  > i docker_release_multi_build_dev_image \
      --version <VERSION> \
      --target-registries <TARGET_REGISTRIES>
  ```

  where
  - TARGET_REGISTRIES: list of target registries to push the image to. E.g.,
    - `aws_ecr.ck`: private CK AWS Docker registry
    - `dockerhub.causify`: public Dockerhub registry
  - All the other options are the same as for the `docker_release_dev_image`
    end-to-end flow.

- E.g.,
  ```
  > i docker_release_multi_build_dev_image \
      --version 1.6.1 \
      --target-registries aws_ecr.ck,dockerhub.causify
  ```

### Post-release check-list

- [ ] Make an integration with the `kaizenflow` repository in order to copy all
      the changes from the `cmamp` repository
- [ ] Tag the new `dev` image to GHCR namespace and push it to GHCR registry

## Build prod image

- The main differences between `dev` image and `prod` image are:
  - The source code is accessed through a bind mount for `dev` image (so that it
    can be easily modified) and copied inside the image for a `prod` image
    (since we want to package the code in the container)
  - Requirements to be installed are different:
    - `dev` image requires packages to develop and run the code
    - `prod` image requires packages only to run the code

- The recipe to build a `prod` image is in
  [`/devops/docker_build/prod.Dockerfile`](/devops/docker_build/prod.Dockerfile).

- To build the `prod` image run:

  ```bash
  > i docker_build_prod_image --version 1.0.0

  # Check the options.
  > i docker_build_prod_image -h

  # To build from scratch.
  > i docker_build_prod_image --version 1.0.0 --no-cache
  ```

- To run a command inside the prod image
  ```
  > docker run --rm -t --user $(id -u):$(id -g) --workdir=/app
  665840871993.dkr.ecr.us-east-1.amazonaws.com/cmamp:prod-1.0.3 "ls -l /app"
  ```
- Example of a complex command:
  ```
  > docker run --rm -t --workdir=/app 665840871993.dkr.ecr.us-east-1.amazonaws.com/cmamp:prod-1.0.3 "python /app/datapull/ccxt/data/extract/download_realtime.py --to_datetime '20211204-194432' --from_datetime '20211204-193932' --dst_dir 'test/ccxt_test' --data_type 'ohlcv' --api_keys 'API_keys.json' --universe 'v03'"
  ```

### QA for prod image

- In dev_scripts repo test:
  ```
  > i lint --files "linters/amp_black.py"
  ```
- In amp repo make sure:
  ```
  > i lint -f "helpers/dbg.py"
  ```

### End-to-end flow for `prod` image

1. Build docker `prod` image
   ```bash
   > i docker_build_prod_image --version 1.0.0
   ```
2. Run all the tests to verify that nothing is broken
   ```bash
   > i run_fast_tests --version 1.0.0 --stage prod
   > i run_slow_tests --version 1.0.0 --stage prod
   > i run_superslow_tests --version 1.0.0 --stage prod
   > i run_qa_tests --version 1.0.0 --stage prod
   ```
3. Push `prod` image to the docker registry
   ```bash
   > i docker_push_prod_image --version 1.0.0
   ```

- To run the flow end-to-end do:

  ```bash
  > i docker_release_prod_image --version 1.0.0
  ```

- The same options are available as for `i docker_release_dev_image` and you can
  check them with `i docker_release_prod_image -h`

## Release a multi-architecture prod image

### Overview

- Build `prod` versioned image remotely in the CK AWS ECR registry and pull once
  it is built
- Run the `cmamp` regressions using a versioned `prod` image
- Tag the versioned `prod` image as `prod` image and push it to the Docker
  registries
- Tag the new `prod` image to GHCR namespace and push it to GHCR registry

## Flow for both dev and prod images

- To run both flows end-to-end do:
  - `i docker_release_all`
- Alternatively, one can run the release stages step-by-step

# Release flow

## cmamp

- File a GitHub Issue for the release
  - E.g., "Add package foobar to cmamp image"
- Create the corresponding branch
  ```
  > i git_create_branch -i ${issue_number}
  ```
- Change the code as needed
- Update the changelog, e.g., `//cmamp/changelog.txt`
  - Specify what was changed
  - Pick the release version according to
    [semantic versioning](https://semver.org/) convention
    - For example for version `1.2.3`:
      - 1 is major, 2 is minor, 3 is patch
    - We keep major and minor versions for `dev` and `prod` image in sync, while
      `prod` gets patches
      - E.g., go from `prod-1.1.0` to `prod-1.1.1` for a small bug fix
    - In this manner, it cannot happen we have `dev-1.1.0` and `prod-1.2.0` at
      any point in time, but `dev-1.1.0` and `prod-1.1.2` are perfectly fine
- Test the change using the local release flow

  ```bash
  > i docker_build_local_image -v ${version}
  ...

  > i run_fast_slow_tests -s local -v ${version}
  ```

- Make sure that the goal of the Issue is achieved
  - E.g., a new package is visible, the package version has been updated
- Do a PR with the change including the updated `changelog.txt`, the poetry
  files (e.g.,
  [`/devops/docker_build/poetry.toml`](/devops/docker_build/poetry.toml),
  [`/devops/docker_build/poetry.lock`](/devops/docker_build/poetry.lock)
- Run the release flow manually (or rely on GH Action build workflow to create
  the new image)

  ```bash
  # Release dev image
  > i docker_release_dev_image --version $version

  # Pick up the new image from image repo
  > i docker_pull
  ```

- Tag and push the latest `dev` to GHCR registry manually
  - Perform a Docker login using your GitHub username and PAT (Personal Access
    Token):
    ```bash
    > docker login ghcr.io -u <username>
    ```
  - Tag the `dev` image to the GHCR namespace:
    ```bash
    > docker tag 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev ghcr.io/causify-ai/cmamp:dev
    ```
  - Push the tagged image to the GHCR registry:
    ```bash
    > docker push ghcr.io/causify-ai/cmamp:dev
    ```

- Send a message on the `all@` chat telling people that a new version of the
  `XYZ` container has been released
- Users need to do a `i docker_pull` to get the new container
- Users that don't update should see a message telling them that the code and
  container are not in sync any more, e.g.,:
  ```
  -----------------------------------------------------------------------------
  This code is not in sync with the container:
  code_version='1.0.3' != container_version='amp-1.0.3'
  -----------------------------------------------------------------------------
  You need to:
  - merge origin/master into your branch with `invoke git_merge_master`
  - pull the latest container with `invoke docker_pull`
  ```

## QA flow

- The goal is to test that the container as a whole works
- We want to run the container as a user would do

- Usually we run tests inside a container to verify that the code is correct
- To test the container itself right now we test outside (in the thin client)
  ```
  > pytest -m qa test --image_stage dev
  ```
