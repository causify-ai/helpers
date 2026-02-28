---
name: docker.use_standard_style
description: Align Docker files in a project directory to the standard project template style
---

- You are an expert of Docker and Docker compose

- I will pass you a directory $TARGET with a project that requires Docker

- Read `class_project/project_template/README.md` explaining how this project
  uses Docker to build and execute containers
- Make the Docker files in the $TARGET directory align to the reference
  `class_project/project_template` and the containers are built and executed in
  the same way

- Write a short summary in bullet points of what needs to be done

- Only change files in $TARGET
