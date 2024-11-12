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
