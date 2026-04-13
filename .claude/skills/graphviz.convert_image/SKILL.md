---
description: Convert an image of a graph into a Graphviz Dot in an accurate way
---

- Given the input image of a graph

# Step 1: Create Graphviz

- Create a Graphviz Dot to match exactly the figure
- Save the result in `graph.dot`

# Step 2: Render to Image

- After the graph description is generated, generate an image with:
  ```
  > dot -Tpng graph.dot -o graph.png
  > open graph.png
  ```

# Step 3: Read the PNG file

- If the generated PNG image is different from the input image:
  - Find the differences in terms of layout, e.g.,
    - Check the position of the nodes 
    - Check the colors of the nodes are the same
  - Apply changes to `graph.dot` to approximate the input image, e.g.,
    - Use rank to keep the nodes in the same relative position
    - Change the color of nodes in `graph.dot` to match the input image
