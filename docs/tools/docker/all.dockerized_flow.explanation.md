<!-- toc -->

<!-- tocstop -->

# Dockerized Executable Flow

## The concept of "dockerized" executables

- The objective of "dockerized" executables is to execute software applications
  (e.g., `prettier`, LaTeX, `pandoc`) within a Docker container with all the
  needed dependencies

- This approach eliminates the need for installing these applications directly on
  the host system, in a virtual environment, or within a development container

- In other words, instead of install and execute `prettier` on the host
  ```bash
  > install prettier
  > prettier ...cmd opts...
  ```
  you want to run it in a container with minimal changes to the system call:
  ```bash
  > dockerized_prettier ...cmd opts...
  ```

## Templates

- There are two template for dockerized scripts:
  - [`/dev_scripts_helpers/dockerize/dockerized_template.py`](/dev_scripts_helpers/dockerize/dockerized_template.py)
  - [`/dev_scripts_helpers/dockerize/dockerized_template.sh`](/dev_scripts_helpers/dockerize/dockerized_template.sh)

- As always, prefer to use the Python approach, instead of shell scripts

## Examples of Dockerized Executables

- We support several dockerized executables
  - `prettier`
  - `pandoc`
  - `markdown-toc`
  - `plantuml`
  - `mermaid`
  - Latex
  - `llm_transform` (which relies on `helpers/hllm.py`)

- Examples of dockerized Python scripts are:
  - [`/dev_scripts_helpers/llms/llm_transform.py`](/dev_scripts_helpers/llms/llm_transform.py)
    - Run a Python script using `helpers` in a container with `openai` packages
  - [`/dev_scripts_helpers/documentation/dockerized_prettier.py`](/dev_scripts_helpers/documentation/dockerized_prettier.py)
    - Run `prettier` in a container
  - [`/dev_scripts_helpers/documentation/convert_docx_to_markdown.py`](/dev_scripts_helpers/documentation/convert_docx_to_markdown.py)
    - Run `pandoc` in a container

- You can find all the Python dockerized executable with:
  ```bash
  > ffind.py dockerized | grep py
  ./dev_scripts_helpers/dockerize/dockerized_template.py
  ./dev_scripts_helpers/documentation/dockerized_graphviz.py
  ./dev_scripts_helpers/documentation/dockerized_latex.py
  ./dev_scripts_helpers/documentation/dockerized_mermaid.py
  ./dev_scripts_helpers/documentation/dockerized_pandoc.py
  ./dev_scripts_helpers/documentation/dockerized_prettier.py
  ./dev_scripts_helpers/documentation/dockerized_tikz_to_bitmap.py
  ./dev_scripts_helpers/documentation/test/test_dockerized_pandoc.py
  ./dev_scripts_helpers/documentation/test/test_dockerized_prettier.py
  ./dev_scripts_helpers/github/dockerized_invite_gh_contributors.py
  ./dev_scripts_helpers/github/dockerized_sync_gh_issue_labels.py
  ...
  ./linters/dockerized_ty.py
  ```

- Examples of dockerized shell scripts are:
  - [`/dev_scripts_helpers/documentation/lint_latex.sh`](/dev_scripts_helpers/documentation/lint_latex.sh)
  - [`/dev_scripts_helpers/documentation/latexdockercmd.sh`](/dev_scripts_helpers/documentation/latexdockercmd.sh)
  - [`/dev_scripts_helpers/documentation/run_latex.sh`](/dev_scripts_helpers/documentation/run_latex.sh)
  - TODO(gp): Convert the scripts in Python and remove these

## Directory and Module Structure

### Core Infrastructure Modules

- `helpers/hdocker.py`
  - Core Docker infrastructure module providing low-level Docker operations:
    - Container lifecycle management (build, run, remove)
    - Image building and caching with content-based hashing
    - Path conversion between host and container filesystems
    - Mount point configuration for different container types (children vs
      sibling)
    - Architecture compatibility checking
  - Contains generic utilities that work with any Docker container
  - Examples: `build_container_image()`,
    `convert_caller_to_callee_docker_path()`, `get_docker_mount_info()`

- `helpers/hdockerized_executables.py`
  - High-level wrappers for specific external tools (prettier, pandoc, latex,
    mermaid, etc.)
  - Uses `hdocker.py` functions to run tools inside Docker containers
  - Handles tool-specific requirements:
    - Custom Dockerfiles for each tool
    - Command-line argument parsing and conversion
    - Input/output file path mapping
    - Tool-specific configuration options
  - Contains functions like `run_dockerized_prettier()`,
    `run_dockerized_pandoc()`, `run_dockerized_latex()`

### Script Architecture Pattern

The dockerized executable pattern follows a three-layer architecture:

1. **Entry Point Scripts (`XYZ.py`)**
   - User-facing command-line interface
   - Handles argument parsing and validation
   - Calls the appropriate dockerized function from `hdockerized_executables.py`
   - Examples: 
     - `dev_scripts_helpers/llms/llm_transform.py`
     - `dev_scripts_helpers/documentation/dockerized_prettier.py`

2. **Dockerized Wrapper Functions**
   - Located in `helpers/hdockerized_executables.py`
   - Manages Docker container execution
   - Converts file paths between host and container contexts
   - Examples: `run_dockerized_prettier()`, `run_dockerized_pandoc()`

3. **Core Business Logic (Optional)**
   - Complex functionality can be separated into dedicated helper modules
   - Examples: 
     - Image extraction logic in `helpers/hjupyter.py`
     - LLM operations in `helpers/hllm.py`

### File Naming Conventions

- **`dockerized_XYZ.py`**: Scripts that run inside containers (deprecated pattern)
- **`XYZ.py`**: User entry points that invoke dockerized functions
- **`run_dockerized_XYZ()`**: Functions in `hdockerized_executables.py` that manage container execution

## Running a Dockerized executable

### Children- vs Sibling-container

- There are several scenarios when one needs to run a dockerized executable
  inside another docker container
  - E.g., run an executable which has system and package dependencies:
    - in the thin environment, outside of a dev container
    - inside the dev container while developing
    - as part of unit testing (both CI and not CI)

- In this case we need to use one of the following approaches:
  - **Children-container** (aka **Docker-in-Docker**)
    - Run a Docker container inside another container
    - It requires elevated privileges
  - **Sibling-container**:
    - More efficient and secure compared to children container approach
    - It comes with greater usage restrictions

### Bind Mounting a Directory for Dockerized Executables

- Files that needs to be processed by dockerized executables needs to be visible
  and referred to in the file system of the dockerized executable
- So we need to convert them to paths that are valid inside the filesystem of the
  new Docker container

- **Problem**: There are multiple scenarios to consider

  - Files can be specified as absolute or relative path in the caller file system

  - We can run a Dockerized executable:
    - On the host; or
    - Inside a Docker container

  - The dockerized executables can be run:
    - As children-container (aka docker-in-docker, dind); or
    - As sibling-container

- Let's consider the problems and how to solve them

- **Children-container**
  - In this case bind mounting a directory does not pose any issues, since the
    dockerized executable uses the same filesystem as the hosting container

- **Sibling-container**
  - The mounted directory must be accessible from the host system
  - For instance, when a local directory is mounted within the container at
    `/src` (which is shared with the host):
    - The reference name within the container is `/src`, but the corresponding
      name outside on the host system is different
    - This introduces dependencies that can complicate the development
      environment
    - For example, the local directory `/tmp` on the host is not visible from
      the development container

- Assumption:
  - `src_root` and `dst_root` are the dirs used to bind mount the dockerized
    executable
  - For both children-container and sibling-containers we assume that the bind
    mount point is from the Git root of the outermost repo to `dst_root=/src` of
    the container
  - In the case of nested containers, the "style" of container (i.e., children-
    or sibling-) is the same. E.g., we assume that if the external container is
    children-container (or sibling), also the internal one is children-container
    (or sibling)
  - In the case of sibling-container, we need to use the dir from the host
    filesystem to mount a directory
  - In the case of children-container, to mount a directory we can use the dir
    from the caller filesystem

- Let's consider the 4 scenarios and how filesystems of the caller and called
  dockerized executable are mapped onto each other

  1. Caller=host, callee=children-container
     ```
     caller=host

     callee=docker
     - src_root=//host/users/.../git_root1
     - dst_root=//docker/src

     > exec.py -i foo/bar
     > exec.py -i /users/.../git_root1/foo/bar
     > (cd foo; exec.py -i bar)

     //host/users/.../git_root1/foo/bar -> /foo/bar -> //docker/src/foo/bar
     ```

  2. Caller=host, callee=sibling-container
     ```
     caller=host

     callee=docker
     - src_root=//host/users/.../git_root1
     - dst_root=//docker/src

     > exec.py -i foo/bar
     > exec.py -i /users/.../src/foo/bar
     > (cd foo; exec.py -i bar)

     //host/users/.../git_root1/foo/bar -> /foo/bar -> //docker/src/foo/bar
     ```

  3. Caller=children-container, callee=children-container
     ```
     caller=docker1
     - src_root=//host/users/.../git_root1
     - dst_root=//docker1/src

     callee=docker2
     - src_root=//docker1/src (which corresponds to the Git root)
     - dst_root=//docker2/src

     > exec.py -i foo/bar
     > exec.py -i /src/foo/bar

     //docker1//src/foo/bar -> /foo/bar -> //docker2/src/foo/bar
     ```

  4. Caller=sibling-container, callee=sibling-container
     ```
     caller=docker1
     - src_root=//host/users/.../git_root1
     - dst_root=//docker1/src

     callee=docker2
     - src_root=//host/users/.../git_root1
     - dst_root=//docker2/src

     > exec.py -i foo/bar
     > exec.py -i /src/foo/bar

     //docker1//src/foo/bar -> /foo/bar -> //docker2/src/foo/bar
     ```

- The algorithm is:
  - Normalize the input path to the caller filesystem (i.e., host or docker1)
  - Compute the path as relative to the mount point of the caller
  - Use the mount point of the caller container

## Testing a dockerized executable

- Testing a dockerized executable can be complex, since in our development
  system `pytest` is executed within a container environment.
- Thus the dockerized executable needs to be run inside the container running
  `pytest`, rather than executing outside of Docker as it typically would when
  called by a user.
- The layers in this setup are
  - `host`
    - `dev container`
      - `pytest`
        - `dockerized executable`

- Existing Approaches:
  - Approach 1:
    - Overwrite the entrypoint to wait for an injected file, then run the
      container's main command:

      ```bash
      #!/bin/bash

      # Wait until a specific file is copied into the container
      while [ ! -f "/path/in/container/ready_file" ]; do
        echo "Waiting for files..."
        sleep 1
      done

      # Run the container's main command
      exec "$@"
      ```
    - Then write files in the running container
  - Approach 2:
    - Inject files into the Docker image by creating an additional layer using a
      Dockerfile:
      - Build an image with the test files injected.
      - Execute the test inside the container processing the input file.
      - Pause the container.
      - Transfer the output file from the container to the host system.
      - Terminate the container.

- Preferred Approach: Simulated Usage Testing

  Instead of modifying the build context or patching the Dockerfile, we prefer
  to simulate real-world usage by testing the dockerized executable exactly as
  it will be used in production. This approach involves:
  - Using the `hdocker` Module Directly:

    Run the container using the helper function (e.g.,
    run_dockerized_notebook_image_extractor()) as-is, without any additional
    file injection or Dockerfile modifications.
  - Realistic Environment Simulation:

    The container is executed with its standard entrypoint and configuration,
    mimicking the actual user invocation.
  - Output Verification:

    After execution, assert the presence and correctness of output files or log
    messages. If needed, you can verify the file system or container logs to
    confirm that the expected actions were performed.

  Benefits
  - Simplifies the testing setup by reducing pytest configuration complexity
  - Ensures that tests mirror the actual behavior of the dockerized executable
    in production
  - Avoids the overhead of additional layers or entrypoint modifications

  Example:
  [`/dev_scripts_helpers/notebooks/test/test_extract_notebook_images.py`](/dev_scripts_helpers/notebooks/test/test_extract_notebook_images.py)

## Examples

### Example 1: Notebook Image Extraction

- Executable Script:
  - Location:[`/dev_scripts_helpers/notebooks/extract_notebook_images.py`](/dev_scripts_helpers/notebooks/extract_notebook_images.py)
  - Role: Acts as the entry point for users. It parses command-line arguments
    and orchestrates the workflow by invoking Docker operations from the
    helpers/`hdocker` module

- Core Functionalities:
  - Location: `helpers/hjupyter`
  - Role: Contains the logic for extracting images from Jupyter notebooks. This
    module implements the actual image extraction process used by the executable
    script

- Docker Management:
  - Location: `helpers/hdocker`
  - Role: Encapsulates all Docker-related operations such as building the
    container, defining Docker commands, and running the container. This module
    provides the function (e.g., `run_dockerized_notebook_image_extractor()`)
    that the executable script calls to execute the image extraction inside a
    Docker container

- Testing:
  - Location:
    [`/dev_scripts_helpers/notebooks/test/test_extract_notebook_images.py`](/dev_scripts_helpers/notebooks/test/test_extract_notebook_images.py)
  - Role: Contains tests for the dockerized executable. The tests simulate
    real-world usage by invoking the Docker container using the standard process
    defined in `helpers/hdocker`, and then asserting that the expected output
    (such as extracted images) is produced

### Example 2: llm_transform

The example illustrates how the dockerized executable for llm_transform manages
file path conversions and container invocation in two different scenarios.
Here's a breakdown:

- Overview

  The tool (`llm_transform.py`) transforms a markdown file based on a given type
  (here, md_rewrite) and supports two configurations controlled by:
  - `is_caller_host`: Determines if the command is initiated from the host.
  - `use_sibling_container_for_callee`: Indicates if a sibling container is used
    to execute the transformation.

- How File Paths Are Managed

  When you run the command, the tool converts file paths from the caller's
  context (either the host or within a container) to the paths that will be
  valid inside the target container. For instance:
  - Input File Conversion: The caller's `tmp.llm_transform.in.txt` is mapped to
    `/app/tmp.llm_transform.in.txt` in the container
  - Output File Conversion: Similarly, `tmp.llm_transform.out.txt` is mapped to
    `/app/tmp.llm_transform.out.txt`

- Script and Directory Conversion: The script located at
  [`/dev_scripts_helpers/llms/dockerized_llm_transform.py`](/dev_scripts_helpers/llms/dockerized_llm_transform.py)
  is converted to `/app/dev_scripts_helpers/llms/dockerized_llm_transform.py` so that it
  can be accessed inside the container.

- Docker Run Command Construction

  After converting the file paths, the system constructs a docker run command.
  - For the first scenario (when `is_caller_host = True`):
    - Mounting: The host directory (eg: `/Users/saggese/src/helpers1`) is
      mounted into the container at `/app`
    - Environment and Working Directory: Environment variables (like
      `OPENAI_API_KEY`) are passed, and the working directory is set to `/app`
    - Command Execution:

    The container then executes the transformed script
    (`/app/dev_scripts_helpers/llms/dockerized_llm_transform.py`) with the converted input
    and output paths and additional flags (e.g.,
    `transformation type -t md_rewrite and verbosity -v DEBUG`).
  - For the second scenario (when `is_caller_host = False`):
    - The conversion adjusts for the fact that the command is executed inside
      the container.
    - The mount paths and target paths differ (e.g., the container might mount
      `/app` to `/src`), but the concept remains the same: ensure that the file
      paths used in the command correspond correctly to those inside the
      container.
