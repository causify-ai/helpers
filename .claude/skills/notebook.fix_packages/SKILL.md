---
description: Keep the Docker container aligned with the template and install Python packages directly in the notebook
model: haiku
---

# Goal
- When creating Docker images for projects and tutorials, we want to
  - Try to use always the same Docker template image from the `class_project` to
    avoid replication of Docker containers
  - Install the needed packages in the notebooks to customize the container

## Inputs
- The user passes:
  - A pointer to a target directory `<TARGET_DIR>` (e.g.,
    `msml610/tutorials/L03_knowledge_representation`) that was cloned from
    `class_project/project_template`
  - (Optional) pointers to Jupyter notebooks

# Workflow

## Use the Docker Container from the Project Teamplate
- In the directory with the project (e.g.,
  `msml610/tutorials/L03_knowledge_representation`) we want to use the same
  `Dockerfile` and `requirements.txt` as the corresponding files in
  `class_project/project_template` (so that the Docker container for the project is
  the same as the template used for class project)

- If something needs to be added to the Docker image (e.g., a package that can't
  be installed with `pip`) then it's ok to add it to `Dockerfile` but it should
  be clearly commented why that package is needed

## Discover All Packages Needed by the Notebook
- A notebook's own `import` lines are not the full picture: each notebook is
  paired with a `*_utils.py` file (e.g., `L03_06_logic_solvers.ipynb` ->
  `L03_06_logic_solvers_utils.py`), and that file is imported with a line
  like:
  ```
  import L03_06_logic_solvers_utils as utils
  ```
- Read the `*_utils.py` file (and any other local module it imports,
  transitively) and collect every third-party `import` / `from ... import`
  statement in it, not just the ones in the notebook itself
- Map import names to their pip package name where they differ (e.g., `cv2`
  -> `opencv-python`, `sklearn` -> `scikit-learn`, `PIL` -> `Pillow`,
  `yaml` -> `PyYAML`)
- Diff this full package list against `requirements.txt` and `Dockerfile`:
  any package used by the notebook or its utils file that is missing from
  both is a bug, even if it happens to already be installed in whatever
  container was used to author the notebook
- Add every missing package to `requirements.txt` (and to `Dockerfile` only
  if it can't be installed with `pip`, per `## Use the Docker Container from
  the Project Teamplate` above)

## Add Packages to Notebooks
- Then we want to add `pip install` the packages needed in each notebook,
  including every package found in `## Discover All Packages Needed by the
  Notebook` above, by installing and pinning down the packages

- For each notebook we want to add after the first call with
  ```
  %load_ext autoreload
  %autoreload 2

  import logging
  ```
  a cell with content like:
  ```
  !pip install -q python-sat==1.9.dev15 sympy==1.14.0 z3-solver==5.1.0.0

  import pysat
  print("pysat version: ", pysat.__version__)
  import sympy
  print("sympy version: ", sympy.__version__)
  import z3
  print("z3 version: ", z3.get_version_string())
  ```

## Sync Notebook
- At the end, sync the paired `.py` file with Jupytext following the conventions
  in `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Verification
- [ ] Every third-party import in the notebook and its paired `*_utils.py`
  file has a matching entry in `requirements.txt` and in the notebook's
  `pip install` cell
- [ ] Build the docker container with `docker_build.sh` inside the target dir
  `<TARGET_DIR>`
- [ ] Make sure the container builds correctly and it's the same as the Docker
  container for the project, if possible
- [ ] Run each notebook inside the docker container with `docker_cmd.sh` and
  `nbconvert` to make sure they run correctly end-to-end

# Conventions
- Always follow the conventions and guidelines in
  `.claude/skills/notebook.rules.md`
