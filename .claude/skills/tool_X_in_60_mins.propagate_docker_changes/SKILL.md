---
description: Make the Docker build system for the tutorials and research projects as similar to project_template
model: haiku
---

# Overview
- $SRC_DIR=class_project/project_template

This skill supports two modes:
- **Full sync**: Make all Docker files across projects match project_template
- **Last-commit sync**: Propagate only the changes from the most recent commit
  in project_template

# Mode A: Full sync
- For each project / directory $DST_DIR in the directories from
  `class_project/project_dirs.md`
- Make the Docker files `$DST_DIR/docker_*.sh`, `$DST_DIR/Dockerfile`,
  `$DST_DIR/run_jupyter.sh` as similar as possible to the corresponding ones in
  $SRC_DIR
  - The goal is to reuse functions and factored out code (e.g., from
    `class_project/project_template/utils.sh`)
- If you are not sure about what the changes are
  - Summarize the changes for the user in bullet points
  - Ask for the user to confirm

# Mode B: Last-commit sync
- Use this mode when you only need to propagate the most recent changes

## Step 1
- Look at the changes from the last git commit in $SRC_DIR
- Summarize the changes for the user in bullet points
- If you are not sure about what the changes are, stop and ask for the user to
  confirm

## Step 2
- Propagate the changes in the Docker system from $SRC_DIR to all the projects
  in the directories from `class_project/project_dirs.md`

## Step 3
- Make sure not to change the behavior unless needed

## Step 4
- Update `class_project/project_template/README.md` explaining how this project
  uses Docker to build and execute containers given the new changes

# Verification (both modes)
- Make sure that all the `docker_*.sh` scripts work running them directly or
  by running the relevant pytest unit tests
