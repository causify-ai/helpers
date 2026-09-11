---
description: Create a tutorial directory for the Learn X in 60 Minutes conventions
model: sonnet
---

# Goal

- You are an expert at structuring self-contained, reproducible data-science
  tutorials
- The user will pass you a `<TOPIC>` and a target dir such as
  `tutorials/<TOPIC>`
- Write a "Learn XYZ in 60 Minutes" tutorial for the topic / package `<TOPIC>`
  in the dir `tutorials/<TOPIC>`

# Workflow

## Read the Specs and Examples
- Read the spec in `.claude/skills/tool_X_in_60_mins.rules.md`

## Improve Content of the Tutorial
- Assume that the user has already created the tutorial directory
  `tutorials/<TOPIC>` following the directions of
  `.claude/skills/tool_X_in_60_mins.rules.md`

- In `tutorials/<TOPIC>` the files that typically need customization are
  - `XYZ_utils.py`: Reusable helper functions (no notebook logic)
  - `XYZ.API.ipynb`: Native API walkthrough (paired with XYZ.API.py)
  - `XYZ.API.py`: Jupytext percent-format mirror
  - `XYZ.example.ipynb`: End-to-end application demo (paired with
    XYZ.example.py)
  - `XYZ.example.py`: Jupytext percent-format mirror
  - `requirements.txt`: Python dependencies (pinned versions)
  - `README.md`: Quick start guide

## Improve Docker Build System

- Modify `tutorials/<TOPIC>/docker_name.sh`
  ```bash
  # The file should be all lower case.
  IMAGE_NAME=umd_project_<TOPIC>
  ```

- Modify `tutorials/<TOPIC>/requirements.txt` to include the needed packages

- Customize the Docker build system in `tutorials/<TOPIC>` following the
  instructions from `.claude/skills/docker.use_standard_style/SKILL.md`

## Create Content of the README.md
- Create or improve a file `tutorials/<TOPIC>/README.md`
- Use as reference:
  - `tutorials/AutoGen/README.md`
  - `tutorials/BambooAI/README.md`
  - `tutorials/TensorFlow/README.md`
- Run `lint_text.py -i` to format the README file

## Run Docker
- Make sure the system builds by running
  ```bash
  > cd tutorials/<TOPIC>
  > docker_build.sh
  ```

## Customize the Tests
- Customize the tests if needed in `tutorials/<TOPIC>/test`

- Make sure the test run
  ```bash
  > cd tutorials/<TOPIC>
  > docker_cmd.sh `pytest test`
  ```

## Create Blog Entry
- Create or improve a file `website/docs/blog/posts/<TOPIC>_in_60_mins.md`
- For
  ```yaml
  categories:
    - AI Research
    - Software Engineering
  ```
  the categories are chosen from `categories_allowed` in `website/mkdocs.yml`
  based on what makes sense
- Use as a reference
  - `website/docs/blog/posts/in_60_mins.AutoGen.md`,
  - `website/docs/blog/posts/in_60_mins.BambooAI.md`,
  - `website/docs/blog/posts/in_60_mins.Tensorflow.md`,
- Run `lint_text.py -i` to format the markdown file

# Examples
- Use as a reference of how a tutorial looks like
  - `tutorials/AutoGen`
  - `tutorials/BambooAI`
  - `tutorials/TensorFlow`

# Verification
- [ ] `tutorials/<TOPIC>` builds: `docker_build.sh` completes without error
- [ ] Tests pass: `docker_cmd.sh` `pytest test` completes without error
- [ ] `tutorials/<TOPIC>/README.md` exists and was linted with `lint_text.py -i`
- [ ] `website/docs/blog/posts/<TOPIC>_in_60_mins.md` exists, has categories from
  `website/mkdocs.yml`, and was linted with `lint_text.py -i`
