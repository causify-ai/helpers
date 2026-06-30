---
description: Propose visuals for each slides
model: haiku
---

- Given a markdown file with slides, propose visuals for each slide

- Read `.claude/skills/slides.rules.md` and follow strictly the conventions and
  rules

## Propose a Visual for Each Slide
- If a slide doesn't contain a picture or a diagram (e.g., graphviz), consider
  what can be used to illustrate the concepts visually, e.g.,
  - Propose a graphviz diagram
  - Find an image on the Internet (download and save it in a dir
    `proposed_images`)
  - Propose the description of an image in the format
    ```
    <image>
    Description of the image
    </image>
    ```

## Ask User to Confirm and Decide
- Make numbered list of proposed changes for the user
- Once user confirms changes, perform the changes

## Constraints
- Maintain the structure of the text and keep the content of the existing text
