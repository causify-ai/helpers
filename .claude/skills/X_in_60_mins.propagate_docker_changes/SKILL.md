---
description: Make the Docker build system for the tutorials and research projects as similar to project_template
---

# Step 1
- $SRC_DIR=class_project/project_template
- For each project / directory $DST_DIR in the following directories:
  - `class_project/project_template/`
  - `data605/tutorials/`
  - `msml610/tutorials/`
  - `tutorials/`
  - `research/`
- Make the Docker files in `$DST_DIR/docker_*.sh` as similar as possible to the
  corresponding ones in $SRC_DIR
  - The goal is to reuse functions and factored out code (e.g., from
    `class_project/project_template/utils.sh`)
- If you are not sure about what the changes are
  - Summarize the changes for the user in bullet points
  - Ask for the user to confirm

# Step 2
- Make sure not to change the behavior unless needed
- Make sure that the all the `docker_*.sh` scripts work running them directly or
  by running the relevant pytest unit tests
