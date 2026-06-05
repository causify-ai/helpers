# The Bash Print Tree Workflow

<!-- toc -->

- [Introduction](#introduction)
- [Workflow Explanation](#workflow-explanation)
- [Usage Instructions](#usage-instructions)
- [Use Cases](#use-cases)
- [Example](#example)
  * [Step 1: Create a new file with tree output](#step-1-create-a-new-file-with-tree-output)
  * [Step 2: Add comments to explain important files](#step-2-add-comments-to-explain-important-files)
  * [Step 3: Add more files and subdirectories to `devops`](#step-3-add-more-files-and-subdirectories-to-devops)
  * [Step 4: Re-run the workflow to update the tree](#step-4-re-run-the-workflow-to-update-the-tree)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)

<!-- tocstop -->

## Introduction

- The `bash_print_tree` `invoke` workflow prints a directory tree and optionally
  updates an existing Markdown file
- It is used for maintaining documentation of structured files preserving inline
  comments
- The tree can be printed to standard output or embedded into a file between
  markers like `<!-- tree:start:{name} -->` and `<!-- tree:end -->`

## Workflow Explanation

- The task walks the specified directory up to a maximum depth
- By default, the tree includes all subdirectories and files (excluding Python
  and test files), and outputs to the terminal only
- You can configure whether to:
  - Include or exclude Python files
  - Include or exclude test files
  - Show only directories
  - Output to a file, while preserving existing inline comments
  - Clean untracked files
- If an output file is given and contains tree markers, the script:
  - Extracts inline comments from the existing tree
  - Preserves these comments while updating the tree section

## Usage Instructions

- Some examples of workflows are:

  ```bash
  # Print the current directory tree.
  > i bash_print_tree

  # Limit depth to 2 and include test files.
  > i bash_print_tree --path="devops" --depth=2 --include-tests

  # Include only Python files.
  > i bash_print_tree --include-python

  # Print only directory names.
  > i bash_print_tree --only-dirs

  # Overwrite tree block in a Markdown file while preserving comments.
  > i bash_print_tree --path="devops" --output="README.md"

  # Clean untracked files before generating the tree.
  > i bash_print_tree --clean
  ```

## Use Cases

- Documenting file structures in `README.md` or similar documentation
- Auditing the layout of codebases and shared folders
- Tracking structural changes over time via version control

## Example

- Consider the case where we want to document the DevOps code organization
  located in the directory `devops`

### Step 1: Create a new file with tree output

- Create the initial file with the structure of the tree

  ```bash
  > i bash_print_tree --path="devops" --output="all.devops_docker.reference.md"
  ```

- The output file `all.devops_docker.reference.md` should look like this:

  ```markdown
  <!-- tree:start:devops -->

  devops
  - compose
    - tmp.docker-compose.yml
  - docker_build
    - create_users.sh
    - dev.Dockerfile
    - dockerignore.dev
    - dockerignore.prod
    - etc_sudoers
    - fstab
    - install_cprofile.sh
    - install_dind.sh
    - install_os_packages.sh
    - install_publishing_tools.sh
    - install_python_packages.sh
    - pip_list.txt
    - poetry.lock
    - poetry.toml
    - prod.Dockerfile
    - pyproject.python_data_stack.toml
    - pyproject.toml
    - update_os.sh
    - utils.sh
  - docker_run
    - bashrc
    - docker_setenv.sh
    - entrypoint.sh
    - run_jupyter_server.sh
  - env
    - default.env
    <!-- tree:end -->
  ```

### Step 2: Add comments to explain important files

- You edit the output file `all.devops_docker.reference.md` and more information
  and comments to the files in the tree

  ```markdown
  ## Introduction

  This file documents the code organization and Docker-based DevOps structure.

  ## Directory Structure

  <!-- tree:start:devops -->

  devops
  - compose # Contains Docker compose files.
    - tmp.docker-compose.yml
  - docker_build # Building Docker image.
    - create_users.sh # Create container users.
    - dev.Dockerfile
    - dockerignore.dev
    - dockerignore.prod
    - etc_sudoers # Gives sudo permissions.
    - fstab
    - install_cprofile.sh
    - install_dind.sh # Installs docker-in-docker.
    - install_os_packages.sh
    - install_publishing_tools.sh
    - install_python_packages.sh
    - pip_list.txt
    - poetry.lock
    - poetry.toml
    - prod.Dockerfile
    - pyproject.python_data_stack.toml
    - pyproject.toml
    - update_os.sh
    - utils.sh
  - docker_run # Running Docker image.
    - bashrc
    - docker_setenv.sh
    - entrypoint.sh
    - run_jupyter_server.sh
  - env
    - default.env
    <!-- tree:end -->

  ## Docker invoke flow

  There exists `docker_bash` and `docker_jupyter`.
  ```

### Step 3: Add more files and subdirectories to `devops`

- Over time, additional files and subdirectories will be added to `devops`

  ```bash
  # Create a new directory.
  > mkdir -p devops/debug

  # Add a new file.
  > touch devops/docker_build/install_tools.sh
  ```

### Step 4: Re-run the workflow to update the tree

- Update the documentation file with the updated structure of `devops`

  ```bash
  > i bash_print_tree --path="devops" --output="all.devops_docker.reference.md"
  ```

- The updated tree will reflect the new files while preserving comments:

  ```markdown
  ## Introduction

  This file documents the code organization and Docker-based DevOps structure.

  ## Directory Structure

  <!-- tree:start:devops -->

  devops
  - compose # Contains Docker compose files.
    - tmp.docker-compose.yml
  - debug
  - docker_build # Building Docker image.
    - create_users.sh # Create container users.
    - dev.Dockerfile
    - dockerignore.dev
    - dockerignore.prod
    - etc_sudoers # Gives sudo permissions.
    - fstab
    - install_cprofile.sh
    - install_dind.sh # Installs docker-in-docker.
    - install_os_packages.sh
    - install_publishing_tools.sh
    - install_python_packages.sh
    - install_tools.sh
    - pip_list.txt
    - poetry.lock
    - poetry.toml
    - prod.Dockerfile
    - pyproject.python_data_stack.toml
    - pyproject.toml
    - update_os.sh
    - utils.sh
  - docker_run # Running Docker image.
    - bashrc
    - docker_setenv.sh
    - entrypoint.sh
    - run_jupyter_server.sh
  - env
    - default.env
    <!-- tree:end -->

  ## Docker invoke flow

  There exists `docker_bash` and `docker_jupyter`.
  ```

## Known Limitations

- Inline comment preservation only works if the tree is wrapped with markers
  like `<!-- tree:start:{name} -->` and `<!-- tree:end -->`
- The function does not support excluding arbitrary file patterns beyond test or
  Python filters

## Future Improvements

- Add support for custom exclude or include glob patterns
- Support multiple tree blocks per file (e.g., for different directories)
- Improve standardization of how tree blocks are rendered in Markdown files by
  wrapping the content between markers in a code block (e.g., using ` ```bash `)
  so that only the tree, not the markers, is displayed in the final output
