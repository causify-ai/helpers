---
description: Create a tutorial directory to follow the "Learn X in 60 Minutes" tutorial conventions
---

- You are an expert at structuring self-contained, reproducible data-science
  tutorials
- The user will pass you a `<topic>` and a target dir such as `tutorials/<topic>`
  
- Write a "Learn XYZ in 60 Minutes" tutorial for the topic / package `<topic>`
  in the dir `tutorials/<topic>`

# Follow the Following Steps

## Read the Specs and Examples

- Read the spec in `.claude/skills/tool_X_in_60_mins.rules.md`
- Use as a reference of how a tutorial looks like
  - `tutorials/AutoGen` 
  - `tutorials/BambooAI` 
  - `tutorials/TensorFlow` 

## Copy the Project Template
  ```
  > cp -a tutorials/project_template tutorials/<topic>
  ```
- Ask the user to commit this change before modifying it

## Improve Docker Build System

- Modify `tutorials/<topic>/docker_name.sh`
  ```
  # The file should be all lower case.
  IMAGE_NAME=umd_project_<topic>
  ```

- Modify `tutorials/<topic>/requirements.txt` to include the needed packages

- Customize the Docker build system in `tutorials/<topic>` following the
  instructions from `.claude/skills/docker.use_standard_style/SKILL.md`

## Improve Content of the Tutorial

- Create the content of the directory `tutorials/<topic>` following the
  directions of `.claude/skills/tool_X_in_60_mins.rules.md`

- In `tutorials/<topic>` the files that typically need customization are
  - `XYZ_utils.py`          # Reusable helper functions (no notebook logic)
  - `XYZ.API.ipynb`         # Native API walkthrough (paired with XYZ.API.py)
  - `XYZ.API.py`            # Jupytext percent-format mirror
  - `XYZ.example.ipynb`     # End-to-end application demo (paired with XYZ.example.py)
  - `XYZ.example.py`        # Jupytext percent-format mirror
  - `requirements.txt`      # Python dependencies (pinned versions)
  - `README.md`             # Quick start guide

- Use as a reference the files in:
  - `tutorials/AutoGen` 
  - `tutorials/BambooAI` 
  - `tutorials/TensorFlow` 

## Create Content of the README.md

- Create or improve a file `tutorials/<topic>/README.md`
- Use as reference:
  - `tutorials/AutoGen/README.md` 
  - `tutorials/BambooAI/README.md` 
  - `tutorials/TensorFlow/README.md` 
- Run `lint_txt.py -i` to format the README file

## Run Docker

- Make sure the system builds by running
  ```
  > cd tutorials/<topic>
  > docker_build.sh
  ```

## Customize the Tests

- Customize the tests if needed in `tutorials/<topic>/test`

- Make sure the test run
  ```
  > cd tutorials/<topic>
  > docker_cmd.sh `pytest test`
  ```

## Create Blog Entry

- Create or improve a file `website/docs/blog/posts/<topic>_in_60_mins.md`
- For
  ```
  categories:
    - AI Research
    - Software Engineering
  ```
  the categories are chosen from `categories_allowed` in `website/mkdocs.yml`
  based on what makes sense
- Use as a reference
  - `website/docs/blog/posts/Autogen_in_60_mins.md`,
  - `website/docs/blog/posts/BambooAI_in_60_mins.md`,
  - `website/docs/blog/posts/TensorFlow_in_60_mins.md`,
- Run `lint_txt.py -i` to format the file
