---
description: Convert formulas to Latex
---

- Convert formulas to Latex leaving the structure of the text exactly the
  same

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
    P(M \mid D) \propto P(D \mid M)\, P(M)
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
      \mathbb{E}_{M \sim P(M \mid D)}\left[
        \text{Goal} \mid do(a), M
      \right]
    $$
    ```

# Step 2: Convert symbols to Latex

- Convert symbols into Latex ones, together with variables if needed→
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

- After the conversion run 
  ```
  > lint_txt.py -i $FILE
  ```
