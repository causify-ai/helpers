---
description: Convert formulas in text to their Latex equivalent
---

- Convert formulas to Latex leaving the structure of the text exactly the
  same

- Use the rules and conventions in `@.claude/skills/latex.rules.md`

# Step 1: Convert mathematical formulas

- Convert mathematical formulas to Latex without changing their meaning
  and formatting so that they are easily readable
  - **Bad**
    ```
    P(M | D) ∝ P(D | M) P(M)
    ```
  - **Good**
    ```
    $$
    \Pr(M | D) \propto \Pr(D | M)\, \Pr(M)
    $$
    ```

  - **Bad**
    ```
    a* = argmax_a E_{M~P(M|D)}[Goal | do(a), M]
    ```
  - **Good**
    ```
    $$
    a^* = \arg\max_a
      \EE_{M | \Pr(M | D)}
      \left[
        \text{Goal} | do(a), M
      \right]
    $$
    ```

# Step 2: Convert symbols to Latex

- Convert symbols into Latex ones, together with variables if needed:
  - **Bad**
    ```
    X → Y
    ```
  - **Good**
    ```
    $X \to U$
    ```
- If there are expressions then leave them unchanged
  - **Bad**
    ```
    "If battery low" → seek charging station
    ```
  - **Bad**
    ```
    "If battery low" $\to$ seek charging station
    ```

# Step 3: Lint the file

- After the conversion run the command:
  ```bash
  > lint_txt.py -i <file>
  ```
