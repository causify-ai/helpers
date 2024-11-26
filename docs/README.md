

<!-- toc -->

- [Readme](#readme)
  * [File description](#file-description)

<!-- tocstop -->

# Readme

- This file is the entrypoint of all the documentation and describes all the
  documentation files in the `docs` directory

- The current file structure is:
  ```bash
  > tree.sh -p docs
  docs/
  |-- work_tools/
  |   |-- all.create_a_super_repo_with_helpers.how_to_guide.md
  |   |-- all.devops_docker.how_to_guide.md
  |   |-- all.devops_docker.reference.md
  |   `-- all.thin_environment.reference.md
  |-- code_organization.md
  `-- README.md
  ```

## File description

- Invariants:
  - Files are organized by directory (e.g., `docs`, `docs/work_tools`)
  - Each file name uses the Diataxis naming convention
  - Each file name should be linked to the corresponding file as always
  - Files are organized in alphabetical order to make it easy to add more files
    and see which file is missing
  - Each file has a bullet lists summarizing its content using imperative mode

- In `docs`
  - `docs/README.md`
    - This file
    - Describe all the available documentation files
  - `docs/code_organization.md`
    - Describe the high-level code structure and organization in this repo

- In `docs/work_tools`
  - `all.create_a_super_repo_with_helpers.how_to_guide.md`
    - Describe how to create a super-repo including helpers
  - `all.create_a_runnable_dir.how_to_guide.md`
    - Describe how to create a runnable dir, i.e., a directory that has code and
      a Docker container to run its code inside
  - `all.devops_docker.how_to_guide.md`
    - Describe how to run the devops Docker environment
  - `all.devops_docker.reference.md`
    - Describe how the devops Docker environment works
  - `all.thin_environment.reference.md`
    - Describe how the "thin environment" works
    - The thin environment is used to bootstrap the development system
