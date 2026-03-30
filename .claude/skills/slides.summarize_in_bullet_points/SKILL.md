---
description: Summarize the text into markdown bullet points for a slide
model: haiku
---

- Use a `*` for top-level topic headers
  - E.g., `* Markov Chains`

- Convert the text into structured markdown bullet points following the rules in
  @.claude/skills/text.summarize_in_bullet_points/SKILL.md

- Example
  ```
  * Chains
  - In case of $T \to M \to Y$:
    - $M$ is "mediator" since it mediates the relationship between $T$ and $Y$
    - Causation flows only in the direction of the arrows
    - Association flows both ways
  ```
