

<!-- toc -->

- [The concept of "dockerized" executables](#the-concept-of-dockerized-executables)
  * [Children- vs Sibling-container](#children--vs-sibling-container)
- [Running a Dockerized executable](#running-a-dockerized-executable)
- [Testing a dockerized executable](#testing-a-dockerized-executable)
- [Example](#example)

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

## Children- vs Sibling-container

- There are several scenarios when one needs to run a dockerized executable
  inside another docker container, e.g., when running a dockerized executable
  inside the container for development or unit testing

- In this case we need to use one of the following approaches:
  - **Children-container**:
    - It typically addresses most operational issues, since it runs a Docker
      container in another container, as the outermost container was a host
    - It requires elevated privileges.
  - **Sibling-container**:
    - More efficient and secure compared to Docker-in-Docker.
    - It comes with greater usage restrictions.

- **Bind mounting a directory from inside the development container**
  - Caution must be exercised when bind mounting a directory to facilitate file
    exchange with the dockerized executable.
  - **Children-container**
    - In this case, bind mounting a directory does not pose any issues.
  - **Sibling-container**
    - The mounted directory must be accessible from the host system.
    - For instance, when a local directory is mounted within the container at
      `/src` (which is shared with the host):
      - The reference name within the container is `/src`, but the corresponding
        name outside on the host system is different.
      - This introduces dependencies that can complicate the development
        environment.
      - For example, the local directory `/tmp` on the host is not visible from
        the development container.

# Running a Dockerized executable

- The problem is that files that needs to be processed by dockerized executables
  can be specified as absolute or relative path in the caller file system, and
  we need to convert them to paths that are valid inside the new Docker
  container

- We can run a Dockerized executable:
  - On the host; or
  - Inside a Docker container

- The Docker container can be run:
  - As children-container (aka docker-in-docker, dind); or
  - As sibling-container

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

# Example

##

    is_caller_host = True
    use_sibling_container_for_callee = True

> llm_transform.py -i input.md -o - -t md_rewrite
 
caller_file_path='tmp.llm_transform.in.txt', caller_mount_path='/Users/saggese/src/helpers1', callee_mount_path='/app', check_if_exists=True, is_input=True, is_caller_host=True, use_sibling_container_for_callee=True
  Converted tmp.llm_transform.in.txt -> tmp.llm_transform.in.txt -> /app/tmp.llm_transform.in.txt

caller_file_path='tmp.llm_transform.out.txt', caller_mount_path='/Users/saggese/src/helpers1', callee_mount_path='/app', check_if_exists=False, is_input=False, is_caller_host=True, use_sibling_container_for_callee=True
  Converted tmp.llm_transform.out.txt -> tmp.llm_transform.out.txt -> /app/tmp.llm_transform.out.txt

caller_file_path='/Users/saggese/src/helpers1', caller_mount_path='/Users/saggese/src/helpers1', callee_mount_path='/app', check_if_exists=True, is_input=False, is_caller_host=True, use_sibling_container_for_callee=True
  Converted /Users/saggese/src/helpers1 -> . -> /app

caller_file_path='/Users/saggese/src/helpers1/dev_scripts_helpers/llms/_llm_transform.py', caller_mount_path='/Users/saggese/src/helpers1', callee_mount_path='/app', check_if_exists=True, is_input=True, is_caller_host=True, use_sibling_container_for_callee=True
  Converted /Users/saggese/src/helpers1/dev_scripts_helpers/llms/_llm_transform.py -> dev_scripts_helpers/llms/_llm_transform.py -> /app/dev_scripts_helpers/llms/_llm_transform.py

> (docker run --rm --user $(id -u):$(id -g) -e OPENAI_API_KEY -e PYTHONPATH=/app --workdir //app --mount type=bind,source=/Users/saggese/src/helpers1,target=/app tmp.llm_transform.b24cf6a4 /app/dev_scripts_helpers/llms/_llm_transform.py -i /app/tmp.llm_transform.in.txt -o /app/tmp.llm_transform.out.txt -t md_rewrite -v DEBUG) 2>&1

##
    is_caller_host = False
    use_sibling_container_for_callee = True

user_501@90607cb8df65:/app$ ./dev_scripts_helpers/llms/llm_transform.py -i
input.md -o - -t md_rewrite -v DEBUG

source_file_path='tmp.llm_transform.in.txt', source_host_path='/app', target_docker_path='/src', check_if_exists=True, is_input=True
Converted tmp.llm_transform.in.txt -> tmp.llm_transform.in.txt -> /src/tmp.llm_transform.in.txt

source_file_path='tmp.llm_transform.out.txt', source_host_path='/app', target_docker_path='/src', check_if_exists=False, is_input=False
Converted tmp.llm_transform.out.txt -> tmp.llm_transform.out.txt -> /src/tmp.llm_transform.out.txt

source_file_path='/app', source_host_path='/app', target_docker_path='/src', check_if_exists=True, is_input=False
Converted /app -> . -> /src/.

source_file_path='/app/dev_scripts_helpers/llms/_llm_transform.py', source_host_path='/app', target_docker_path='/src', check_if_exists=True, is_input=True
Converted /app/dev_scripts_helpers/llms/_llm_transform.py -> dev_scripts_helpers/llms/_llm_transform.py -> /src/dev_scripts_helpers/llms/_llm_transform.py

> (docker run --rm --user $(id -u):$(id -g) -e OPENAI_API_KEY -e
PYTHONPATH=/src/. --workdir /src --mount type=bind,source=/app,target=/src
tmp.llm_transform.b24cf6a4 /src/dev_scripts_helpers/llms/_llm_transform.py -i
/src/tmp.llm_transform.in.txt -o /src/tmp.llm_transform.out.txt -t md_rewrite -v
DEBUG) 2>&1
