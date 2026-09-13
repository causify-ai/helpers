---
description: Align Docker files in a project to the standard project template style
model: haiku
---

# Goal
- Act as an expert in Docker and Docker Compose
- Given a directory `<TARGET>` with a project that requires Docker, align its
  Docker files to the standard project template style

# Workflow

## Read the Reference Template
- Read `class_project/project_template/docker_scripts.README.md`, which
  explains how the project uses Docker to build and execute containers

## Align the Target
- Make the Docker files in `<TARGET>` align to the reference
  `class_project/project_template`, so containers build and run the same way

## Summarize
- Write a short summary in bullet points of what needs to be done

# Constraints
- Only change files in `<TARGET>`

# Verification
- [ ] Confirm the Docker files in `<TARGET>` match the structure and behavior
      of `class_project/project_template`
- [ ] Confirm no file outside `<TARGET>` was changed
