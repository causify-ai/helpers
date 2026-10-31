---
description: Write or update the README of a single executable or script
model: sonnet
---

# Goal

- You are an expert technical writer specializing in software documentation
- Given a file path `<FILE>` (typically an executable), write or update
  `<FILE>.README.md` in the same directory
- Follow the conventions in `.claude/skills/readme_file.rules.md`
- Follow the template `.claude/templates/readme_file.template.md`

# Workflow

## Read the File

- Read `<FILE>` and identify:
  - The entry point and the argument parser (flags, types, defaults)
  - The inputs, outputs, and side effects (files, exit codes, logging)
  - The key functions and the data flow

## Check the Existing README

- If `<FILE>.README.md` exists, read it and plan what to update
- If it does not exist, plan content from scratch

## Write the README

- Write `<FILE>.README.md` with the sections from
  `.claude/skills/readme_file.rules.md`:
  - Summary
  - Examples
  - Configuration & Inputs
  - Output & Side Effects
  - Software Architecture
- For the Software Architecture section, reuse the steps of
  `.claude/skills/readme_file.write_architecture/SKILL.md`
- Follow all formatting rules from `.claude/skills/readme_file.rules.md`:
  - Examples ordered from simple to complex
  - Commands as bullet + fenced block with the `> ` prefix
  - Argument reference as a table

## Point to the README from the File

- Make sure the docstring of `<FILE>` points to `<FILE>.README.md`, e.g.,
  ```text
  For a description of this file, see the file <FILE>.README.md
  ```

# Verification

- [ ] `<FILE>.README.md` exists in the same directory as `<FILE>`
- [ ] Every required section from `.claude/skills/readme_file.rules.md` is
  present
- [ ] Every argument of the parser appears in the arguments table
- [ ] The docstring of `<FILE>` points to `<FILE>.README.md`
