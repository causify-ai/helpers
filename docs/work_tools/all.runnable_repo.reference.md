# Summary

- This document describes the design principles around our approach to create Git
  repos that contains code that can be:
  - composed through different Git sub-repo
  - tested, built, run, and released (on a per-directory basis or not)

# Design goals

- The development toolchain should support the following functionalities

- Bootstrap the development system using a "thin environment", which has the
  minimum number of dependencies to allow development on a server or on a
  personal laptop
- Support composing code based using GitHub sub-repo approach
- Manage dependencies in a way that is uniform across platforms and OSes, using
  Docker containers
- Separate the need to build container (by devops) vs the need to use a container
  (for developers)
- Ensure alignment between development environment and CI systems (e.g., GitHub)
- Carefully manage and control dependencies using Python managers (such as
  `poetry`) and virtual environments
- Run end-to-end tests using `pytest` by automatically discover tests based on
  dependencies and test lists, supporting the dependencies needed by different
  directories
- Standardize ways of building, testing, retrieving, and deploying containers
- Support different stages for container development (e.g., `test` / `local`,
  `dev`, `prod`)
- Support a way to deploy code in production with minimal difference from
  development
- A system of makefile-like tools based on Python `invoke` package to create
  workflows
- Make it easy to add our development chain to a given a "new project" (e.g., new
  repo such as `dev_scripts`, `sports_analytics`) by simply adding a Git sub-repo
- Have a simple way to maintain common files across different repos in sync
- Code and containers can be versioned and kept in sync automatically
  - Code is versioned through Git
  - Each container has a `changelog.txt` that contains the current version and
    the history
  - A certain version of the code can require a certain version of the container
    to run properly

# Alternative solution

- Our previous approach was to create a single repo with different directories
  containing different "applications" all running in a single Docker container
  (aka `cmamp` or `dev` container)

- The main issues with this approach is that:
  - The repo is enormous and monolithic
  - There is not an easy way to have permission control over which parts of a
    repo developers have access to

- These problems got progressively worse since we want to have all the dev chain
  we are used to (thin environment, `invoke`, pytest, Docker), but since the dev
  chain was bolted on `cmamp`, we kept adding to `cmamp` instead of creating
  another repo

# Current solution

- The current solution follows the approach described below

## Helper sub-repo
- `//helpers` is the sub-repo that contains utilities shared by all the repos
  and the development toolchain (e.g., thin environment, Docker, setenv,
  `invoke` workflows)
- Git repos can include `//helpers` and other ones as sub-repos

## Runnable dir
- A dir is runnable when its own devops dir so that they can have its own
  container and dependencies (to run and to test)
  - E.g., `//cmamp/optimizer`, `//cmamp/infra`
- The code in a runnable directory or in the main repo requires a container
  that is built using the code in the corresponding `devops` dir

## Thin environment
- Each top-level repo requires a `dev_scripts` that contains code to build the
  corresponding thin environment
- A thin environment can be shared across multiple repos and runnable directories
  since typically the dependencies needed to start the development containers are
  common
- A setenv script is used to configure a shell outside and inside a Docker
  container

## Building a Docker container
- Code and tests need to be run inside a corresponding Docker container
- There is a shared toolchain to build, test, release, and deploy each Docker
  container:
  - The containers have all the dependencies to run the code
  - Each container is multi-architecture in order to be run on different processor
    architectures (e.g., x86-64, arm64)
- The same container is used to run the code in all set-ups (e.g., on a personal
  laptop, on a server, in the CI)
- The container mounts the source code as a bind-mount directory so that
  developers can use external tools to edit the code (e.g., vim, PyCharm, VSCode)
- A production container copies the code inside so that it contains OS
  dependencies, Python packages, and code, without any external dependency
- It is possible to have different dependencies for the dev and prod container
  - E.g., dependencies to run the unit tests are not needed in a prod container
- The toolchain to build containers is managed through `invoke` targets
  - It supports versioning
- The Python dependencies are managed to 

## Running a Docker container
- Handy wrappers through the `invoke` toolchain are available to perform common
  operations, e.g.,
  - `invoke docker_bash` to start a shell inside a container

## pytest
- To run all the tests in a repo, `pytest` needs to run inside a dev container
- For top-level repo, the needed container is the top-level container
- For a runnable dir, the needed container is the one built in that specific
  directory

## Recursive pytest
- When we want to run all the tests it is needed for `pytest` to run through
  a single script that iterates over the containers and runs the corresponding
  tests in the corresponding container

  ```
  > main_pytest.py --dir infra
  ```

- In case of multiple containers:
  ```
  for container in containers:
     (cd container; i docker_cmd --cmd pytest)
  ```

## Support for docker-in-docker and sibling-containers

# Examples

- Examples of composable repos
  - `cmamp` is composed of `helpers`
- TODO

# Maintaining code across different sub-repos

- TODO(gp): Explain
