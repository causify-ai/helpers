---
description: Criticize and suggest improvements for class slides
---

- Given a Markdown file storing slides for a class (where each slide title is
  prepended with `*`)

# Propose improvements
- Read the content and make suggestions on how to improve the class, numbering
  each suggestion so that it's easy to refer to
  - Do not make changes but only make proposals

## Change order of slides
- Propose how to organize the slides in a different flow, separating cohesive
  chunks with level 1 and 2 headers
  - E.g.,
    ```
    # Topic 1

    ## Topic 1.1

    * Slide 1

    * Slide 2
    ```

## Slides to remove
- Remove slides whose content is redundant or unclear

## Slides to merge
- Merge slides to remove redundant content

## Fix content of slides
- If a slide content is incorrect, propose how to fix it

## Ignore TODOs and comments
- Leave the TODOs or comments in the format
  ```
  // ...
  ```
  untouched

# Ask the user which improvement needs to be done
- After the user approves a subset of changes, perform the changes in place
