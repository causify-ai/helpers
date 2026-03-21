---
description: Propagate the last change in the Docker system for project_template to all the projects
---

$SRC_DIR=class_project/project_template

# Step 1
- Look at the changes from the last git commit in $SRC_DIR
- Summarize the changes for the user in bullet points
- If you are not sure about what the changes are, stop and ask for the user to
  confirm

# Step 2
- Propagate the changes in the Docker system in directory from the dir $SRC_DIR
  to all the projects in the directories below:
  - `class_project/project_template/`
  - `data605/tutorials/`
  - `tutorials/`
  - `research/`

- Make sure not to change the behavior unless needed

# Step 3
- Make sure that the all the `docker_*.sh` scripts work running them directly or
  by running the relevant pytest unit tests

# Step 4
- Update `class_project/project_template/README.md` explaining how this project
  uses Docker to build and execute containers given the new changes
