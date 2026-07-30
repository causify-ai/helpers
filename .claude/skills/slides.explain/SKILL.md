---
description: Explain a lecture slide
model: haiku
---

# Goal
- You need to explain the concepts in slides provided by user in a simple and
  clear way

# Workflow

## Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`

## Step 1: Read the File
- Given the file `<FILE>` from the user storing lecture slides or the provided
  `<TEXT>` in the format described in `.claude/skills/slide.rules.md`

## Step 2: Extract Lecture Slides
- The user selects one or more slides `<SLIDE>` by:
  1) Specifying a slide by its title
  - You can use a tool like the one below to extract the content
    ```
    > extract_from_md.py --md_start <SLIDE_TITLE> -i <FILE>
    ```
  - E.g.,
    ```
    > extract_from_md.py --md_start "Causal and Exhaustive Augmentation: Limitation" -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt
    ```
  2) Tagging a section in `<FILE>` with `<START>` and `<END>`

- Extract the slides from the file

## Step 3: Explain
- Explain the slide in bullet points using the conventions in
  `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
- Focus on brevity, intuition, and simplicity

## Step 4: Answer
- Answer follow-on users questions about the slide
