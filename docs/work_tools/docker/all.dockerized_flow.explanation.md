

<!-- toc -->

- [The concept of "dockerized" executables](#the-concept-of-dockerized-executables)
- [Testing a dockerized executable](#testing-a-dockerized-executable)

<!-- tocstop -->

# The concept of "dockerized" executables

The objective of utilizing "dockerized" executables is to execute software
applications (e.g., Prettier, LaTeX, and Pandoc) within a Docker container with
all the needed dependencies.

This approach eliminates the need for installing these applications directly on
the host system or within a development container.

In other terms, instead of install and execute `prettier` on the host

```bash
> install prettier
> prettier ...cmd opts...
```

we want to run it in a container with minimal changes to the call:

```bash
> dockerized_prettier ...cmd opts...
```

- There are two template for dockerized scripts:
  - `dev_scripts_helpers/dockerize/dockerized_template.py`
    - TODO(gp): This is not the most updated
  - `dev_scripts_helpers/dockerize/dockerized_template.sh`
    - We prefer to use Python, instead of shell scripts

- Examples of dockerized Python scripts are:
  - `dev_scripts_helpers/llms/llm_transform.py`
    - Run a Python script using `helpers` in a container with `openai` packages
  - `dev_scripts_helpers/documentation/dockerized_prettier.py`
    - Run `prettier` in a container
  - `dev_scripts_helpers/documentation/convert_docx_to_markdown.py`
    - Run `pandoc` in a container

- Examples of dockerized shell scripts are:
  - `dev_scripts_helpers/documentation/lint_latex.sh`
  - `dev_scripts_helpers/documentation/latexdockercmd.sh`
  - `dev_scripts_helpers/documentation/run_latex.sh`
  - TODO(gp): Convert the scripts in Python

# Testing a dockerized executable

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

- Running applications within the development container necessitates one of the
  following approaches:
  - **Docker-in-Docker**:
    - Typically addresses most operational issues, since it runs a Docker
      container in another container, as the outermost container was a host
    - Requires elevated privileges.
  - **Sibling-Container**:
    - More efficient and secure compared to Docker-in-Docker.
    - Comes with greater usage restrictions.

- **Bind Mounting a Directory from Inside the Development Container**
  - Caution must be exercised when bind mounting a directory to facilitate file
    exchange with the dockerized executable.
  - **Docker-in-Docker Scenario**
    - In this case, bind mounting a directory does not pose any issues.
  - **Sibling Container Scenario**
    - The mounted directory must be accessible from the host system.
    - For instance, when a local directory is mounted within the container at
      `/src` (which is shared with the host):
      - The reference name within the container is `/src`, but the corresponding
        name outside on the host system is different.
      - This introduces dependencies that can complicate the development
        environment.
      - For example, the local directory `/tmp` on the host is not visible from
        the development container.

- One potential solution is to execute tests for dockerized executables outside
  of the development container.
  - This approach generalizes the process of running pytest across "runnable
    directories."
  - However, it necessitates increased complexity within the pytest
    infrastructure.

- An alternative, less intrusive solution involves injecting files into the
  image or container.
  - However, this process can be complex and may not be straightforward to
    implement.
  - Approach 1)
    - We could overwrite the entrypoint with something like:

      ```bash
      #!/bin/bash

      # Wait until a specific file is copied into the container
      while [ ! -f "/path/in/container/ready_file" ]; do
        echo "Waiting for files..."
        sleep 1
      done

      # Run the container’s main command
      exec "$@"
      ```
    - Then write files in the running container

- Approach 2:
  - The selected method involves the following steps:
    - Inject files into the Docker image by creating an additional layer using a
      Dockerfile.
    - Execute the test to process the input file that has been copied into the
      image.
    - Pause the container.
    - Transfer the output file from the container to the host system.
    - Terminate the container.
  - This approach demonstrates versatility and is applicable to a range of
    similar scenarios.
    - It operates effectively using both the docker-in-docker method.
    - It also functions efficiently with the sibling-container method.
