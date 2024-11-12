# The concept of "dockerized" executables

The goal of "dockerized" executables is to allow to run an executable (e.g.,
prettier, latex, pandoc) inside a container, instead of having to install it
on the host or in a dev container

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

- Testing a dockerized executable can be complex since we run `pytest` inside a
  container
  - The dockerized executable will be started inside a container instead of
    running outside of Docker as in its normal behavior

- The layers are
  - `host`
    - `dev container`
      - `dockerized executable`

- Running inside the dev container requires to use the docker-in-docker or
  the sibling-container approach
  - docker-in-docker approach typically solves most of the problems but it
    requires escalated privileges
  - sibling-container is more efficient, more secure but it has more
    use limitations

- Bind mounting a dir from inside the dev container (which is needed to exchange
  files with the dockerized executable) needs to be handled carefully
  - For docker-in-docker, bind mounting a dir is not a problem
  - For sibling-container, the mounted dir needs to be visible by the host
    - E.g., if we mount the local dir in the container `/src` (which is shared
      with host) the name of it is not the one inside the container `/src` but
      the name of the dir outside host, which creates dependencies between 
    - E.g., the local `/tmp` dir to the dev container is not visible to the
      host

- A solution can be to run the tests for dockerized executables outside the dev
  container
  - This is a generalization of running pytest across "runnable dirs", but it
    requires more complexity on the pytest infrastructure

- A less intrusive solution is to inject files inside the image/container,
  although this is not simple to do
  - Approach 1)
    - We could overwrite the entrypoint with something like:
      ```
      #!/bin/bash

      # Wait until a specific file is copied into the container
      while [ ! -f "/path/in/container/ready_file" ]; do
        echo "Waiting for files..."
        sleep 1
      done

      # Run the container’s main command
      exec "$@"
      ```
    - then write files in the running container

  - Approach 2)
    - The approach we decided to use is to
      - inject files in the Docker image writing another layer through a
        Dockerfile
      - run the test to process the input file copied in the image
      - pause the container
      - copy the output file to outside the container
      - kill the container
    - This is a general approach that can be reused in many similar circumstances
      and that works for both docker-in-docker and sibling-container approaches
