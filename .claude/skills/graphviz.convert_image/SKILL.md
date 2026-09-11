---
description: Convert an image of a graph into a Graphviz Dot in an accurate way
model: haiku
---

# Goal
- Given the input image of a graph, convert it into a Graphviz DOT file that
  matches it exactly

# Workflow

## Create the Graphviz File
- Create a Graphviz DOT file to match exactly the figure
- Save the result in `graph.dot`

## Render to Image
- After the graph description is generated, generate an image with:
  ```bash
  > dot -Tpng graph.dot -o graph.png
  > open graph.png
  ```

## Compare and Refine
- If the generated PNG image is different from the input image:
  - Find the differences in terms of layout, e.g.,
    - Check the position of the nodes
    - Check the colors of the nodes are the same
  - Apply changes to `graph.dot` to approximate the input image, e.g.,
    - Use rank to keep the nodes in the same relative position
    - Change the color of nodes in `graph.dot` to match the input image

# Verification
- [ ] Confirm `graph.dot` renders without errors
- [ ] Confirm `graph.png` matches the input image in node positions and colors
