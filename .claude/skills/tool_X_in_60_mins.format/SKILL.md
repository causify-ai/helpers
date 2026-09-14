---
description: Format a directory to follow the "Learn X in 60 Minutes" tutorial conventions
model: haiku
---

# Goal
- You are an expert at structuring self-contained, reproducible data-science
  tutorials
- I will pass you a directory `<TARGET>` that contains, or will contain, a
  "Learn XYZ in 60 Minutes" tutorial for the topic / package `<TOPIC>`

- In the following the specific topic / package is referred to as `<TOPIC>`
  - E.g., `Autogen`, `TensorFlow`

# Workflow

## Read the Spec and Reference
- Read the spec in `.claude/skills/tool_X_in_60_mins.rules.md`
- Use as a reference of how a tutorial looks like
  - `tutorials/AutoGen`
  - `tutorials/BambooAI`
  - `tutorials/TensorFlow`

## Improve Docker Build System
- Improve the Docker build system in `tutorials/<TOPIC>` to follow the
  instructions from `.claude/skills/docker.use_standard_style/SKILL.md`

## Improve Content of the Tutorial
- Organize the content of the directory `tutorials/<TOPIC>` following the
  directions of `.claude/skills/tool_X_in_60_mins.rules.md`
- Use as a reference of how a tutorial looks like
  - `tutorials/AutoGen`
  - `tutorials/BambooAI`
  - `tutorials/TensorFlow`

## Improve Content of the README.md
- Create or improve a file `tutorials/<TOPIC>/README.md`
- Use as reference
  - `tutorials/AutoGen/README.md`
  - `tutorials/BambooAI/README.md`
  - `tutorials/TensorFlow/README.md`
- Run `lint_text.py -i` to format the file

## Improve Blog Entry
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
- Run `lint_text.py -i` to format the file

# Verification
- [ ] `tutorials/<TARGET>` matches the structure in
  `.claude/skills/tool_X_in_60_mins.rules.md`
- [ ] Docker build system in `tutorials/<TOPIC>` follows
  `.claude/skills/docker.use_standard_style/SKILL.md`
- [ ] `tutorials/<TOPIC>/README.md` was linted with `lint_text.py -i`
- [ ] `website/docs/blog/posts/<TOPIC>_in_60_mins.md` was linted with
  `lint_text.py -i`
