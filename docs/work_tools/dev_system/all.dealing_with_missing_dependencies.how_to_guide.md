<!-- toc -->

- [Dealing with missing dependencies in Docker images](#dealing-with-missing-dependencies-in-docker-images)
  * [Quick hacks](#quick-hacks)
    + [Install dependency on the fly](#install-dependency-on-the-fly)
    + [Skip the module](#skip-the-module)
    + [Delay the evaluation](#delay-the-evaluation)
    + [Type annotations](#type-annotations)
  * [Long term solution](#long-term-solution)
    + [Add the dependency to the Docker image](#add-the-dependency-to-the-docker-image)
    + [Create "dockerized" executable](#create-dockerized-executable)
    + [Create "runnable" directory](#create-runnable-directory)

<!-- tocstop -->

# Dealing with missing dependencies in Docker images

- Sometimes our scripts need to use dependencies that are not available in our
  primary Docker image
- If the package is necessary for the entire project and not just for a specific
  script, we can request to have it installed in the Docker image and release a
  new version of the image
- However, sometimes the packages are only needed for a specific script or part
  of a project. Thus, we don't want to install them in the Docker image as it
  would bloat the image

- Due to missing dependencies, the build process will fail when tests are
  discovered or when the module is imported and used in another module
- The following are some common workarounds to deal with the missing
  dependencies without breaking the build

## Quick hacks

### Install dependency on the fly

- While installing the package on the fly is possible, it is NOT a good practice
- This approach is NOT great since every time somebody imports that module (even
  pytest during test discovery), the package gets installed
  - _Bad_
    ```python
    try:
      import somepackage
    except ModuleNotFoundError:
      subprocess.call(["sudo", "/venv/bin/pip", "install", "somepackage"])
    finally:
      import somepackage
    ```
  - A preferred way is to issue a warning if the package is not installed, so
    the user of the script can install it in their environment
    - TODO(heanh): Replace with the wrapper function. See CmampTask11877.
    ```python
    try:
      import somepackage
    except ModuleNotFoundError:
      _module = "somepackage"
      print(_WARNING + f": Can't find {_module}: continuing")
    ```

- A exception is in Jupyter Notebooks, where it's acceptable to install packages
  on the fly for prototyping, experimenting, or running analyses
- However, we should "comment out" those lines afterwards, since Jupyter
  Notebooks are often converted to Python scripts (through jupytext), and we
  don't want these installation commands running automatically
- Example (in a Jupyter Notebook cell)
  ```bash
  !sudo /bin/bash -c "(source /venv/bin/activate; pip install --quiet somepackage)"
  ```

### Skip the module

- If a module is only needed for specific tests or features, we can skip those
  parts gracefully when the module is not available

- Use `pytest.importorskip` to skip the test during the test discovery phase

  ```python
  pytest.importorskip("somepackage")
  ```

- Use try/catch statement to check if package exists and run the code only if
  they are there when the module is imported
  - TODO(heanh): Replace with the wrapper function. See CmampTask11877.

  ```python
  _HAS_MOTO = True
  try:
      import moto
  except ImportError:
      ...
      _HAS_MOTO = False

  if _HAS_MOTO:
    ....
  ```

### Delay the evaluation

- Sometimes it's sufficient to delay when a module is imported to prevent errors
  during script loading or testing

- Move the `import` statement inside the function or class definition so that
  the module is only required when that part of the code is executed

  ```python
  def my_function():
    import somepackage
  ```

  ```python
  class MyClass:
    import somepackage
    ...
  ```

### Type annotations

- If the missing dependency is only needed for type annotations, we can postpone
  the evaluation of the annotations to avoid errors during module loading or
  pytest discovery

- One option is to use string literals for type hints

  ```python
  def my_function(param: "SomeClass") -> "SomeClass":
      ...
  ```

- Another option is to use the `__future__` module to enable postponed
  evaluation of type annotations
  ```python
  from __future__ import annotations
  ```

## Long term solution

- While quick hacks are useful temporary workarounds, they are not a long term
  solution

### Add the dependency to the Docker image

- Obviously, if the package is needed for the entire project, we should add it
  to the Docker image and release a new version of the image

### Create "dockerized" executable

- We can create a "dockerized" executable that can be run in a Docker container
  with all the dependencies pre-installed
- A "dockerized" executable is easier to set up compared to a runnable directory
- It is suitable for utility scripts that have a single and well defined purpose
  and do not have a large number of dependencies
- The image is built on the fly
- Some examples of dockerized executables:
  - `dockerized_prettier`
  - `dockerized_mermaid`
  - `dockerized_extract_notebook_images`

### Create "runnable" directory

- We can create a "runnable" directory that contains all the code and a `devops`
  directory so it can build its own container with all the dependencies needed
  to run and be tested
- A "runnable" dir is more complex to set up than the previous approach
- It is good for larger projects or parts of a project with many interacting
  components that have many dependencies
- The image can be built and stored in the container registry
- Some examples of runnable directories:
  - `infra`
  - `optimizer`
  - `sports_analytics`
  - `tutorial_langchain`
