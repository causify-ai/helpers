---
description: Explain a lecture slide
---

# Role
- Your role is specified in `@.claude/skills/role.md`

# Goal
- Given a file `<file>` storing lecture slides in the format described in
  `@.claude/skills/slide.rules.md`
- Print the name of the file as:
  ```
  File: <file>
  ```

- The user select a slide `<slide>` by:
  - Specifying a slide by its title; or
  - Tagging a slide is tagged with `TODO(ai):`
- Print the title of the slide:
  ```
  Slide title: <title>
  ```

- Explain the slide in bullet points using the conventions in
  `@.claude/skills/text.rules.bullet_points.md`

- Answer users questions about the slide
