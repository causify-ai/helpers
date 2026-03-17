---
description: Format a directory to follow the "Learn X in 60 Minutes" tutorial conventions
---

- You are an expert at structuring self-contained, reproducible data-science
  tutorials
- I will pass you a directory `$TARGET` that contains, or will contain, a "Learn
  XYZ in 60 Minutes" tutorial for the topic / package XYZ

- In the following the specific topic / package is referred to as `XYZ`
  - E.g., `Autogen`, `TensorFlow`

# Step 1: Read the Spec and Reference

- Read the spec in `class_project/X_in_60_mins.format_rules.md` 
- Use as a reference of how a tutorial looks like
  - `tutorials/AutoGen` 
  - `tutorials/BambooAI` 
  - `tutorials/TensorFlow` 

# Step 2: Improve Docker Build System

- Improve the Docker build system in `tutorials/{XYZ}` to follow the instructions
  from `.claude/skills/docker.use_standard_style/SKILL.md`

# Step 3: Improve Content of the Tutorial

- Organize the content of the directory `tutorials/{XYZ}` following the
  directions of `class_project/X_in_60_mins.format_rules.md` 
- Use as a reference of how a tutorial looks like
  - `tutorials/AutoGen` 
  - `tutorials/BambooAI` 
  - `tutorials/TensorFlow` 

# Step 4: Improve Content of the README.md

- Create or improve a file `tutorials/{XYZ}/README.md`
- Use as reference
  - `tutorials/AutoGen/README.md` 
  - `tutorials/BambooAI/README.md` 
  - `tutorials/TensorFlow/README.md` 
- Run `lint_txt.py -i` to format the file

# Step 5: Improve Blog Entry

- Create or improve a file `website/docs/blog/posts/{XYZ}_in_60_mins.md`
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
