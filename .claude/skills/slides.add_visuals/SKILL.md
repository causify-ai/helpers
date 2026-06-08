---
description: Propose visuals for each slides
model: haiku
---

- Given a markdown file with slides for a college class, where each slide title
  is prepended with `*`

# For Each Slide
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

# Ask User to Confirm and Decide
- Make numbered list of proposed changes for the user
- Once user confirms changes, perform the changes

# Leave Structure Unchanged
- Maintain the structure of the text and keep the content of the existing text
