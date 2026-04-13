# Summary
This directory contains a Docker-based development environment template with:

- Utility scripts for Docker operations (build, run, clean, push)
- Configuration files for Dockerfile and environment setup
- Jupyter notebook templates for standardized project development
- Shell utilities and Python helpers for container-based workflows

A guide to set up Docker-based projects using the template, customize it for
your needs, and maintain it over time.

## Description of Files
- `bashrc`
  - Bash configuration file enabling `vi` mode for command-line editing

- `copy_docker_files.py`
  - Python script for copying Docker configuration files to destination
    directories

- `docker_build.version.log`
  - Log file containing Python, `pip`, Jupyter, and package version information
    from Docker build

- `docker_cmd.sh`
  - Shell script for executing arbitrary commands inside Docker containers with
    volume mounting

- `docker_jupyter.sh`
  - Shell script for launching Jupyter Lab server inside Docker containers

- `docker_name.sh`
  - Configuration file defining Docker repository and image naming variables

- `Dockerfile`
  - Docker image build configuration with Ubuntu, Python, Jupyter, and project
    dependencies

- `etc_sudoers`
  - Sudoers configuration file granting passwordless sudo access for postgres
    user

- `README.md`
  - Documentation file describing directory contents, files, and executable
    scripts

- `template_utils.py`
  - Python utility functions supporting tutorial notebooks with data processing
    and modeling helpers

- `template.API.ipynb`
  - Jupyter notebook template for API exploration and library usage examples

- `template.example.ipynb`
  - Jupyter notebook template for project examples and demonstrations

- `utils.sh`
  - Bash utility library with reusable functions for Docker operations

## Workflows
- All commands should be run from inside the project directory
  ```bash
  > cd tutorials/FilterPy
  ```

- To build the container for a project
  ```bash
  > cd $PROJECT
  # Build the container.
  > docker_build.sh
  # Test the container.
  > docker_bash.sh ls
  ```

- Start Jupyter
  ```bash
  > docker_jupyter.sh
  # Go to localhost:8888
  ```

- Start Jupyter on a specific port with vim support
  ```bash
  > docker_jupyter.sh -p 8890 -u
  # Go to localhost:8890
  ```

## How to Customize a Project Template
- Copy the template
  ```bash
  > cp -r class_project/project_template $TARGET
  ```

## Description of Executables

### `copy_docker_files.py`
- **What It Does**
  - Copies Docker configuration and utility files from project_template to a
    destination directory
  - Preserves all file permissions and attributes during copying
  - Creates destination directory if it doesn't exist

- Copy all Docker files to a target directory:
  ```bash
  > ./copy_docker_files.py --dst_dir /path/to/destination
  ```

- Copy with verbose logging:
  ```bash
  > ./copy_docker_files.py --dst_dir /path/to/destination -v DEBUG
  ```

### `docker_bash.sh`
- **What It Does**
  - Launches an interactive bash shell inside a Docker container
  - Mounts the current working directory as `/data` inside the container
  - Exposes port 8889 for potential services running in the container

- Launch bash shell in the container:
  ```bash
  > ./docker_bash.sh
  ```

### `docker_build.sh`
- **What It Does**
  - Builds Docker container images using Docker BuildKit
  - Supports single-architecture builds (default) or multi-architecture builds
    (`linux/arm64`, `linux/amd64`)
  - Copies project files to temporary build directory and generates build logs

- Build container image for current architecture:
  ```bash
  > ./docker_build.sh
  ```

- Build multi-architecture image (requires setting `DOCKER_BUILD_MULTI_ARCH=1`
  in the script):
  ```bash
  > # Edit docker_build.sh to set DOCKER_BUILD_MULTI_ARCH=1
  > ./docker_build.sh
  ```

### `docker_clean.sh`
- **What It Does**

- Removes all Docker images matching the project's full image name
- Lists images before and after removal for verification
- Uses force removal to ensure cleanup completes

- Remove project's Docker images:
  ```bash
  > ./docker_clean.sh
  ```

### `docker_cmd.sh`
- **What It Does**
  - Executes arbitrary commands inside a Docker container
  - Mounts current directory as `/data` for accessing project files
  - Automatically removes container after command execution completes

- Run Python script inside container:
  ```bash
  > ./docker_cmd.sh python script.py --arg value
  ```

- List files in the container:
  ```bash
  > ./docker_cmd.sh ls -la /data
  ```

- Run tests inside container:
  ```bash
  > ./docker_cmd.sh pytest tests/
  ```

### `docker_exec.sh`
- **What It Does**
  - Attaches to an already running Docker container with an interactive bash
    shell
  - Finds the container ID automatically based on the image name
  - Useful for debugging or inspecting running containers

- Attach to running container:
  ```bash
  > ./docker_exec.sh
  ```

### `docker_jupyter.sh`
- **What It Does**
  - Launches Jupyter Lab server inside a Docker container
  - Supports custom port configuration (default 8888), vim keybindings, and
    custom directory mounting
  - Runs `run_jupyter.sh` script inside the container with specified options

- Start Jupyter on default port 8888:
  ```bash
  > ./docker_jupyter.sh
  ```

- Start Jupyter on custom port with vim bindings:
  ```bash
  > ./docker_jupyter.sh -p 8889 -u
  ```

- Start Jupyter with external directory mounted:
  ```bash
  > ./docker_jupyter.sh -d /path/to/notebooks -p 8889
  ```

- Start Jupyter in verbose mode:
  ```bash
  > ./docker_jupyter.sh -v -p 8890
  ```

### `docker_push.sh`
- **What It Does**
  - Authenticates to Docker registry using credentials from
    `~/.docker/passwd.$REPO_NAME.txt`
  - Pushes the project's Docker image to the remote repository
  - Lists images before pushing for verification

- Push container image to registry:
  ```bash
  > ./docker_push.sh
  ```

### `run_jupyter.sh`
- **What It Does**
  - Launches Jupyter Lab server with no authentication (token and password
    disabled)
  - Binds to all network interfaces (0.0.0.0) on port 8888
  - Allows root access for container environments

- Start Jupyter Lab server (typically called from docker_jupyter.sh):
  ```bash
  > ./run_jupyter.sh
  ```

### `version.sh`
- **What It Does**
  - Reports version information for Python3, pip3, and Jupyter
  - Lists all installed Python packages with versions
  - Used during Docker image builds to log environment configuration

- Display version information:
  ```bash
  > ./version.sh
  ```

- Save version information to a log file:
  ```bash
  > ./version.sh 2>&1 | tee version.log
  ```

# Template Customization and Maintenance

## Quick Start for New Projects

### Step 1: Copy the Template
```bash
> cd class_project/project_template
> cp -r . /path/to/your/new/project
> cd /path/to/your/new/project
```

### Step 2: Choose a Base Image
The template includes three Dockerfile options. Choose the one that best fits
your project:

| Option                     | File                     | Best For                                                         |
| -------------------------- | ------------------------ | ---------------------------------------------------------------- |
| **Standard**               | `Dockerfile.ubuntu`      | Full Ubuntu environment with system tools                        |
| **Lightweight**            | `Dockerfile.python_slim` | Minimal Python environment; reduced image size                   |
| **Modern Package Manager** | `Dockerfile.uv`          | Fast dependency resolution with [uv](https://docs.astral.sh/uv/) |

**How to choose:**

- **Use Standard** if you need system-level tools (git, curl, graphviz, etc.)
- **Use Python Slim** to minimize image size and build time
- **Use uv** if you want faster, more reliable dependency management

### Step 3: Set Up Your Dockerfile
- Delete unused reference files
  ```bash
  > rm Dockerfile.ubuntu Dockerfile.python_slim Dockerfile.uv
  ```

- Create your working Dockerfile
  ```bash
  > cp Dockerfile.ubuntu Dockerfile
  ```

- Add your dependencies
  ```bash
  > echo "numpy\npandas\nscikit-learn" > requirements.in
  > pip-compile requirements.in > requirements.txt
  ```

### Step 4: Keep Customization Minimal
- Only modify what's necessary for your project
- Use `requirements.txt` for all Python packages (don't edit Dockerfile for
  this)
- Keep `bashrc` and `etc_sudoers` as-is unless you need custom shell setup
- Keep base image and Python version unless you have specific requirements

## Understanding the Dockerfile Flow
Each Dockerfile follows the same structure. Here are the key stages:

### Stage 1: Base Image and System Setup
```dockerfile
FROM ubuntu:24.04  # or python:3.12-slim, depending on your requirement
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get -y update && apt-get -y upgrade
```

- **Purpose**: Start with a clean base image and disable interactive
  installation prompts

- **When to customize**: Only change the base image or version if your project
  has specific requirements (different Ubuntu version, specific Python version,
  etc.)

### Stage 2: System Utilities (Ubuntu-based Dockerfiles Only)
```dockerfile
RUN apt install -y --no-install-recommends \
    sudo \
    curl \
    systemctl \
    gnupg \
    git \
    vim
```

- **Purpose**: Install essential system tools for development and container
  management

- **When to customize**: Add only if needed for your project
  - `postgresql-client`: for database connections
  - `graphviz`: for graph visualizations
  - `ffmpeg`: for media processing

- **Best practice**: Use `--no-install-recommends` to keep the image small

### Stage 3: Python and Build Tools (Ubuntu-based Dockerfiles Only)
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*
```

- **Purpose**: Install Python 3, pip, and build tools needed for compiled
  packages

- **Why venv**: Creates an isolated Python environment separate from system
  Python

- **When to customize**: Rarely. Only change if you need a specific Python
  version (e.g., `python3.11` instead of `python3`)

### Stage 4: Virtual Environment Setup
```dockerfile
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN python -m pip install --upgrade pip
```

- **Purpose**: Create and activate an isolated virtual environment for your
  project

- **Why this matters**: Ensures reproducibility and prevents dependency
  conflicts across projects

- **When to customize**: Never. This is a standard best practice

### Stage 5: Jupyter Installation
```dockerfile
RUN pip install jupyterlab
```

- **Purpose**: Install Jupyter Lab for interactive development and data
  exploration

- **When to customize**:
  - **Remove** this line if your project doesn't use Jupyter
  - **Add extensions** if needed (e.g., `jupyterlab-git`,
    `jupyterlab-variableinspector`)

### Stage 6: Project Dependencies
```dockerfile
COPY requirements.txt /install/requirements.txt
RUN pip install --no-cache-dir -r /install/requirements.txt
```

- **Purpose**: Install your project-specific Python packages

- **When to customize**: This is the primary place to customize. Define all your
  dependencies in `requirements.txt`

- **Best practice**:
  - **Pin all versions**: `numpy==1.24.0` (not `numpy>=1.20.0`)
  - **Use `--no-cache-dir`**: Reduces image size by skipping pip cache
  - **For complex dependencies**: Use `requirements.in` with `pip-tools` or
    `pip-compile`

- **Example requirements.txt**:
  ```text
  numpy==1.24.0
  pandas==2.0.0
  scikit-learn==1.2.2
  tensorflow==2.13.0
  ```

### Stage 7: Configuration
```dockerfile
COPY etc_sudoers /etc/sudoers
COPY bashrc /root/.bashrc
```

- **Purpose**: Apply custom bash configuration and sudo permissions

- **When to customize**:
  - **Edit `bashrc`**: to add aliases, environment variables, or custom prompt
  - **Edit `etc_sudoers`**: if additional users need passwordless sudo access

### Stage 8: Version Logging
```dockerfile
ADD version.sh /install/
RUN /install/version.sh 2>&1 | tee version.log
```

- **Purpose**: Document the exact versions of Python, pip, Jupyter, and all
  installed packages

- **What it logs**:
  - Python 3 version
  - Pip version
  - Jupyter version
  - Complete list of all installed Python packages

- **Why it matters**: Creates a detailed record of your container's environment
  for troubleshooting and reproducibility

- **How to use**: After building, review `version.log` to verify all
  dependencies installed correctly
  ```bash
  > docker build -t my-project .
  > cat version.log
  ```

- **Extending it**: If you need to log additional tools (MongoDB, Node.js,
  etc.), add them to `version.sh`:
  ```bash
  > echo "# mongo"
  > mongod --version
  ```

### Stage 9: Port Declaration
```dockerfile
EXPOSE 8888
```

- **Purpose**: Declare that the container uses port 8888 (informational for
  Docker)

- **When to customize**: Add additional ports if your application needs them
  (e.g., `EXPOSE 8888 5432 3000`)

## Best Practices: Keep It Simple

### The Core Principle
Only change what's necessary for your project. Everything else should inherit
from the template.

This approach:

- Makes Dockerfiles easier to understand and maintain
- Keeps images smaller and faster to build
- Simplifies future updates from the template
- Ensures consistency across similar projects

### How to Do It Right
| What             | Where                        | Example                         |
| :--------------- | :--------------------------- | :------------------------------ |
| Python packages  | `requirements.txt`           | `numpy==1.24.0`                 |
| System tools     | Dockerfile `apt-get` section | `postgresql-client`             |
| Shell aliases    | `bashrc`                     | `alias jlab="jupyter lab"`      |
| Custom scripts   | `scripts/` directory         | Setup or initialization scripts |
| User permissions | `etc_sudoers`                | Grant passwordless sudo         |

### Wrong Vs. Right Approach
- **Wrong**: Embed everything in the Dockerfile
  ```dockerfile
  RUN pip install my-package && python my_setup.py && npm install
  ```

- **Right**: Use separate files and keep Dockerfile clean
  ```dockerfile
  COPY requirements.txt /install/
  RUN pip install -r /install/requirements.txt
  COPY scripts/setup.sh /install/
  RUN /install/setup.sh
  ```

## .Dockerignore Policy

### Why It Matters
The `.dockerignore` file prevents unnecessary files from being added to the
Docker build context:

- **Reduces build time**: Fewer files to transfer to Docker daemon
- **Reduces image size**: Only necessary files are included
- **Improves security**: Prevents leaking sensitive data

### What to Exclude: Category Breakdown
- Python Artifacts (Always Exclude)
  ```verbatim
  __pycache__/
  *.pyc
  *.pyo
  *.pyd
  ```
  - Why: Compiled bytecode generated at runtime. Regenerated in container, adds
    bloat

- Virtual Environments (Always Exclude)
  ```verbatim
  venv/
  .venv/
  env/
  .env/
  ```
  - Why: Local venvs aren't portable to containers. The Dockerfile creates its
    own

- Jupyter Checkpoints (Always Exclude)
  ```verbatim
  .ipynb_checkpoints/
  ```
  - Why: Auto-generated by Jupyter, not needed in the image

- Git and Version Control (Always Exclude)
  ```verbatim
  .git/
  .gitignore
  .gitattributes
  ```
  - Why: Repository history not needed at runtime

- Docker Build Scripts (Always Exclude)
  ```verbatim
  docker_build.sh
  docker_push.sh
  docker_clean.sh
  docker_exec.sh
  docker_cmd.sh
  docker_bash.sh
  docker_jupyter.sh
  docker_name.sh
  Dockerfile.*
  ```
  - Why: Local development scripts don't run inside the container

- Large Data Files (Recommended)
  ```verbatim
  data/
  *.csv
  *.pkl
  *.h5
  *.parquet
  ```
  - Why: Don't ship large training and test data in the image. Mount via volume
    instead
  - Best practice: `bash     > docker run -v /path/to/data:/data my-image     `

- Test Files (Project-Dependent)
  ```verbatim
  tests/
  tutorials/
  ```
  - Why: Exclude if tests don't run in the container
  - When to include: If CI and CD runs tests inside the container

- Documentation (Recommended)
  ```verbatim
  README.md
  docs/
  *.md
  ```
  - Why: Not needed at runtime
  - Exception: Only keep if your app reads these files at runtime

- Generated Files (Always Exclude)
  ```verbatim
  *.log
  *.tmp
  *.cache
  build/
  dist/
  ```
  - Why: Generated at runtime, not needed in the image

## Workflow: From Template to Your Project

### Complete Setup Checklist
- Copy the template
  ```bash
  > cp -r project_template my-new-project
  > cd my-new-project
  ```

- Keep all reference Dockerfiles
  ```verbatim
  Dockerfile.ubuntu_24_04
  Dockerfile.python_slim
  Dockerfile.uv
  ```

- Create your working Dockerfile
  ```bash
  > cp Dockerfile.ubuntu_24_04 Dockerfile
  ```

- Add your dependencies
  ```bash
  > pip freeze > requirements.txt
  ```

- Configure `.dockerignore`: Review the template `.dockerignore` and add your
  project-specific exclusions (e.g., data directories)

- Test the build
  ```bash
  > docker build -t my-project:latest .
  > docker run -it my-project:latest bash
  ```

- Test Jupyter (if using)
  ```bash
  > ./docker_jupyter.sh -p 8888
  ```

- Document customizations in your project README:
  - Base image chosen and why
  - Key dependencies
  - Any Dockerfile modifications
  - How to build and run

## Maintaining Your Setup

### Document Any Changes
- If you modify the Dockerfile, add explanatory comments:
  ```dockerfile
  # Custom: PostgreSQL client for database access
  postgresql-client \

  # Custom: Node.js for frontend builds
  nodejs \
  ```

### Monitor Package Versions
- After each build, review `version.log`:
  ```bash
  > docker build -t my-project .
  > cat version.log
  ```

### Keep `.dockerignore` Updated
- If you add new directories or files, update `.dockerignore`. Add to
  `.dockerignore` if the directory shouldn't be in the image:
  ```verbatim
  data/
  cache/
  .temp/
  ```

### Contribute Improvements Back
When you improve your project's Docker setup:

- Test thoroughly in your project
- Document the improvement clearly
- Submit back to `project_template`
- Other projects can adopt it when they update

Example improvements:

- Better way to install TensorFlow with GPU support
- Optimized `.dockerignore` for data science projects
- Security hardening (non-root user setup)

## Troubleshooting

### Build Is Slow
- Check `.dockerignore`: Ensure large directories (data/, .git/) are excluded
- Check Docker daemon: Verify Docker is running properly
- Check layer caching: Docker reuses cached layers; avoid changing early layers

### Image Is Too Large
- Check layer sizes:
  ```bash
  > docker history my-project:latest
  ```

- Remove unnecessary packages or use `python_slim` base image

### Package Not Found Error
- Verify package name in PyPI (packages are case-sensitive)
- Check Python version compatibility
- Pin specific version if needed

### Permission Issues in Container
- Check `etc_sudoers`: Ensure user has appropriate permissions
- Check file ownership: Ensure COPY doesn't create root-only files

### Jupyter Won't Connect
- Run Jupyter
  ```bash
  > ./docker_jupyter.sh -p 8888
  ```

- Verify http://localhost:8888 (not https). Check firewall if remote access
  needed
