<!-- toc -->

- [Prepare for development in KaizenFlow](#prepare-for-development-in-kaizenflow)
  * [Introduction](#introduction)
  * [Technologies used](#technologies-used)
  * [Set up the dev environment](#set-up-the-dev-environment)
  * [Coding style](#coding-style)
  * [Linter](#linter)
    + [Run Linter and check results](#run-linter-and-check-results)
  * [Writing and contributing code](#writing-and-contributing-code)

<!-- tocstop -->

# Prepare for development in KaizenFlow

## Introduction

This document outlines the steps to take in order to start contributing to
KaizenFlow. Documenting this set up, we aim to streamline the information flow
and make the contribution process seamless by creating a collaborative and
efficient coding environment for all contributors.

Happy coding!

## Technologies used

- [UMD DATA605 Big Data Systems](https://github.com/gpsaggese/umd_data605)
  contains
  [lectures](https://github.com/gpsaggese/umd_data605/tree/main/lectures) and
  [tutorials](https://github.com/gpsaggese/umd_data605/tree/main/tutorials)
  about most of the technologies we use in KaizenFlow, e.g., Dask, Docker,
  Docker Compose, Git, github, Jupyter, MongoDB, Pandas, Postgres, Apache Spark
- You can go through the lectures and tutorials on a per-need basis, depending
  on what it's useful for you to develop
- As an additional resource to become proficient in using Linux and shell, you
  can refer to
  [The Missing Semester of Your CS Education](https://missing.csail.mit.edu/)

## Set up the dev environment

- Set up the development environment following the instructions in
  [`intern.set_up_development_on_laptop.how_to_guide.md`](/docs/onboarding/intern.set_up_development_on_laptop.how_to_guide.md)

## Coding style

- Adopt the coding style outlined
  [here](/docs/coding/all.coding_style.how_to_guide.md)
- Internalize the guidelines to maintain code consistency

## Linter

- Linter is in charge of reformatting the code according to our conventions and
  reporting potential problems

### Run Linter and check results

- Run Linter on the changed files in the PR branch

  ```bash
  > i lint --files="file1 file2..."
  ```

- More information about Linter can be found
  [here](/docs/coding/all.submit_code_for_review.how_to_guide.md#run-linter)

## Writing and contributing code

- If needed, always start with creating an issue first, providing a summary of
  what you want to implement and assign it to yourself and your team
- Create a branch of your assigned issues/bugs
  - E.g., for a GitHub issue with the name: "Expose Linter container to
    KaizenFlow contributors #63", The GitHub issue and the branch name should be
    called `SorrTask63_Expose_linter_container_to_Kaizenflow_contributors`
- Implement the code based on the requirements in the assigned issue
- Run Linter on your code before pushing
- Do `git commit` and `git push` together so the latest changes are readily
  visible
- Make sure your branch is up-to-date with the master branch
- Create a Pull Request (PR) from your branch
- Add your assigned reviewers for your PR so that they are informed of your PR
- After being reviewed, the PR will be merged to the master branch by your
  reviewers
- Do not respond to emails for replies to comments in issues or PRs. Use the
  GitHub GUI instead, as replying through email adds unwanted information
