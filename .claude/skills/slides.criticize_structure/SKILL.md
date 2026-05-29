---
description: Criticize and suggest improvements for class slides
---

- Given a Markdown file storing slides for a lecture
  - Each slide title is prepended with `*`, e.g., `* Title`

# Propose Improvements
- Read the content and make suggestions on how to improve the slides, numbering
  each suggestion so that it's easy to refer to
  - Do not make changes but only make proposals

## Change Order of Slides
- Propose how to organize the slides in a different flow, separating cohesive
  chunks with level 1 and 2 headers
  - E.g.,
    ```
    # Topic 1

    ## Topic 1.1

    * Slide 1

    * Slide 2
    ```

## Slides to Remove
- Remove slides whose content is redundant or unclear

## Slides to Merge
- Merge slides to remove redundant content

## Fix Content of Slides
- If a slide content is incorrect, propose how to fix it

## Ignore TODOs and Comments
- Leave the TODOs or comments in the format
  ```
  // ...
  ```
  untouched

# Ask the User Which Improvement Needs to Be Done
- After the user approves a subset of changes, perform the changes in place
