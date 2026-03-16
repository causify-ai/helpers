---
description: Format a directory to follow the "Learn X in 60 Minutes" tutorial conventions
---

- You are an expert at structuring self-contained, reproducible data-science
  tutorials
- I will pass you a directory `$TARGET` that contains, or will contain, a "Learn
  XYZ in 60 Minutes" tutorial for the topic / package XYZ

# Step 1: Read the Spec and Reference

- Read the spec in `class_project/X_in_60_mins.format_rules.md` 
- Read `tutorials/Autogen/` to understand what a finished tutorial looks like
- Note the package name (abbreviated below as `XYZ`, e.g., `autogen`)

# Step 2: Docker Build System

- The Docker build system should follow the style in
  `.claude/skills/docker.use_standard_style/SKILL.md`

# Step 3: Improve Content

- Organize the content of the directory as in
- `class_project/X_in_60_mins.format_rules.md` 

# Step 4: 

- Create a file in `website/docs/blog/posts/XYZ_in_60_minutes.md` using
  `website/docs/blog/posts/Autogen_in_60_minutes.md` as a reference
