<!-- toc -->

- [Using the `helpers` Docker image](#using-the-helpers-docker-image)
  * [Set up and activate the thin environment](#set-up-and-activate-the-thin-environment)
- [Releasing Docker image](#releasing-docker-image)
  * [Pull docker images from ECR](#pull-docker-images-from-ecr)
  * [Build and release a new image (only for maintainers)](#build-and-release-a-new-image-only-for-maintainers)
  * [Let people know](#let-people-know)
- [Poetry](#poetry)
  * [Poetry usage examples](#poetry-usage-examples)

<!-- tocstop -->

# Using the `helpers` Docker image

- We use Docker to encapsulate dependencies and maintain a reproducible
  environment

## Set up and activate the thin environment

- Build the thin environment to bootstrap the development system (e.g., for
  using invoke). Run once for all clients; re-running is only needed when the
  dependencies are changed.

  ```bash
  > ./dev_scripts_helpers/thin_client/build.py
  ```

- To activate the thin environment, run

  ```bash
  > source dev_scripts_helpers/thin_client/setenv.sh
  ```

  or start a tmux session, which will activate it automatically:

  ```bash
  > dev_scripts_helpers/thin_client/tmux.py --index 1
  ```

# Releasing Docker image

- This flow is used only by the maintainers of the Docker container

## Pull docker images from ECR

- Pull images from ECR for development purposes:

  ```bash
  > i docker_pull -s dev
  ```

- For production purposes:

  ```bash
  > i docker_pull -s prod
  ```

## Build and release a new image (only for maintainers)

- To build a local image (e.g. for testing the changes locally), run

  ```bash
  > i docker_build_local_image --version ${version}
  ```

- To bash into the local image, run

  ```bash
  > i docker_bash --stage local --version ${version}
  ```

- To run different kinds of tests on a local image, run

  ```bash
  > i run_fast_tests --stage local --version ${version}
  > i run_slow_tests --stage local --version ${version}
  > i run_superslow_tests --stage local --version ${version}
  ```

- To tag the local image as dev, run

  ```bash
  > i docker_tag_local_image_as_dev --version ${version}
  ```

- To push the dev image to ECR, run

  ```bash
  > i docker_push_dev_image --version ${version}
  ```

- To promote the image to prod, run
  ```bash
  > i docker_build_prod_image --version ${version}
  > i docker_push_prod_image --version ${version}
  ```

## Let people know

- Update the changelog: `changelog.txt`
  - The changelog should be updated only after the image is released; otherwise
    the sanity checks will assert that the release's version is not higher than
    the latest version recorded in the changelog.
  - Specify what has changed
  - Pick the release version accordingly - NB! The release version should
    consist of 3 digits, e.g. "1.1.0" instead of "1.1" - We use
    [semantic versioning](https://semver.org/) convention - For example, adding
    a package to the image would mean bumping up version 1.0.0 to 1.0.1

- Do a PR with the change including the updated `changelog.txt`
- Send a message on Slack letting people (especially developers) know that a new
  version of the container has been released

# Poetry

- This repo uses [poetry](https://python-poetry.org/) for package management
- Use `poetry` to
  - Help resolve dependencies
  - Hard-code all package versions (in `poetry.lock`) to get reproducible builds
  - Avoid the need for manually updating requirements files
  - Allow an easy distinction between prod & dev dependencies

## Poetry usage examples

- To create a new virtual env (or reactivate it after it's created):

  ```shell
  > poetry shell
  ```

- To install the requirements locally:

  ```shell
  > poetry install
  ```

- To add a new production dependency or upgrade the dependency:
  - Edit the `devops/docker_build/pyproject.toml` with the updated version of
    the package or the addition of a new dependency
  - Build a new local image

    ```bash
    > i docker_build_local_image --version ${version}
    ```
    - By default, it runs with `--poetry-mode="update"`, which updates `poetry`
      and upgrades all packages to the latest versions
    - Alternatively, run with the flag `--poetry-mode="no_update"` in order to
      install packages from the current `poetry.lock` file without upgrading.
      This is useful when the goal is to remove / add / update only a single
      package without updating everything
  - Bash into the container to check the version of the package

    ```bash
    > i docker_bash --stage local --version ${version}
    docker > pip freeze | grep <package name>
    ```
  - Run the regressions on the new image and do the release only after the
    regressions are green

    ```bash
    > i run_fast_tests --stage local --version ${version}
    > i run_slow_tests --stage local --version ${version}
    > i run_superslow_tests --stage local --version ${version}
    ```

- To update the Python version inside the container:
  - Update the Python version inside `devops/docker_build/pyproject.toml`
  - If the version mismatch occurs, follow this hacky approach:
    - Login into the current image
    - Install the specific Python version in it
    - Update poetry inside the container, so that the `pyproject.toml` and
      `poetry.lock` files are in sync with the latest Python version
    - Build a local image with `i docker_build_local_image --version ${version}`
