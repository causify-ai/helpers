---
description: Explain a lecture slide
model: haiku
---

# Role
- Your role is specified in `.claude/skills/role.ai_researcher.md`

# Step 1: Pick the File
- Given a file `<FILE>` from the user storing lecture slides in the format
  described in `.claude/skills/slide.rules.md`
- Print the name of the file as:
  ```
  File: <FILE>
  ```

# Step 2: Extract
- The user selects one or more slides `<SLIDE>` by:
  - Specifying a slide by its title;
    ```
    > extract_from_md.py --md_start <SLIDE_TITLE> -i <FILE>
    - E.g.,
    > extract_from_md.py --md_start "Causal and Exhaustive Augmentation: Limitation" -i msml610/lectures_source/Lesson06.1-Bayesian_Networks.txt
    ```
  - Tagging a section in `<FILE>` with `<START>` and `<END>`
- Extract the 

# Step 3: Explain
- Explain the slide in bullet points using the conventions in
  `.claude/skills/text.rules.md`

# Step 4: Answer 
- Answer follow-on users questions about the slide
