---
description: Fix slides without changing their structure
---

- Given a markdown file with slides about technical material

- A slide title is prepended with `*` and has hierarchical bullets
  - E.g.,
    ```
    * How Can a Node Be Influenced by Its Children?

    - A **descendant can influence its ancestor** indirectly through _"explaining
      away"_
      - Evidence about the descendant can change what you believe about the
        ancestor through dependent paths
      - Information flows both ways in Bayesian networks
    ```

# Leave Structure Unchanged
- Do not change the structure of the text (e.g., in terms of title, bullet structure,
  div fenced blocks)
- Maintain the content of the existing text
- Do not add periods at the end of phrases

# Fix Mistakes
- Fix English grammar
- Fix any conceptual mistake only if you are sure about the correction
