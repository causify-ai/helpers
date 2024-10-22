# Summary

- This document describes the design principles around our approach to create Git
  repos that contains code that can be:
  - individually released
  - tested (through `pytest`)
  - built, run, and released (through Docker containers)

# Design goals

- We want to have a development chain to:
  - bootstrapping the development system using a "thin environment", which has
    the minimum number of dependencies to allow development on a server and
    personal laptop
  - support composing code based using GitHub sub-repo approach
  - manage dependencies in a way that is uniform across platforms and OSes, using
    Docker containers
  - separate the need to build container (by devops) vs the need to use a
    container (for developers)
  - ensure alignment between development environment and CI systems (e.g.,
    GitHub)
  - carefully manage and control dependencies using Python managers (such as
    `poetry`) and virtual environments
  - run end-to-end tests using `pytest` by automatically discover tests
    based on dependencies and test lists, supporting the dependencies needed by
    different directories
  - standardize ways of building, testing, retrieving, and deploying containers
  - support different stages for container development (e.g., `test` / `local`,
    `dev`, `prod`)
  - support a way to deploy code in production with minimal difference from
    development
  - make it easy to add our development chain to a given a "new project" (e.g.,
    new repo such as `dev_scripts`, `sports_analytics`) we want to make it easier to 
invoke docker (generalize the invoke flow)
pytest

# Alternative solution

- Our previous approach was to create a single repo with different directories
  containing different "applications" all running in a single Docker container
  (aka `cmamp` or `dev` container)

- The main issues with this approach is that
  - the repo is enormous and monolithic
  - there is no easy way to have permission control over which parts of a repo
    developers have access to

- This problem got progressively worse since 
  we want to have all the dev chain we are used to (thin environment, `invoke`,
  pytest, Docker), but since the dev chain was bolted on `cmamp`, we kept adding to
  `cmamp` instead of creating another repo

- 
I have already done a bunch of experiments / prototype so I know what needs to be done and I don’t think there are unknown unknowns

New repos:
Demo
Tutorials
Propagate changes back to cmamp

Amp = helpers + …
Annamite = helpers + manager app
Dev_tools = helpers + linter …
Lemonade = helpers + amp + ...
Orange = 
Defi = helpers + …
Demo = helpers + …
Sports_analytics = helpers + LLMs + demo 
Tutorials = helpers + …
Support releasable dirs
Each dir can have its own devops dir so that they can have its own container and dependencies (to run and to test)

E.g., optimizer, infra

The thin container for infra should become a releasable dir

We also need to support recursive pytest 
Use decorator to decide what container is needed
Then there is a recursive_pytest that runs all the pytest with the correct container
Separate prod deps from dev deps
The deps that we need to run the system (“prod”) are different from the one that we need to develop and unit-test (“dev”)
pytest
With a single container
i docker_bash
pytest

main_pytest.py --dir infra

If you have a multiple containers

for container in containers:
   (cd container; i docker_bash; pytest)

cd infra; i docker_cmd --cmd “pytest”
cd optimizer; i docker_cmd ---cmd “pytest”
CI “problem”
Every test needs to run through pytest locally

CI getting a container, pytest inside

