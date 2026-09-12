---
description: Convert formulas in text to their Latex equivalent
model: haiku
---

# Goal
- Convert formulas to Latex leaving the structure of the text exactly the same
- Use the rules and conventions in `.claude/skills/latex.rules.md`

# Workflow

## Convert Mathematical Formulas
- Convert mathematical formulas to Latex without changing their meaning
  and formatting so that they are easily readable
  - **Bad** (uses Unicode symbols instead of LaTeX)
    ```text
    P(M | D) ∝ P(D | M) P(M)
    ```
  - **Good** (uses LaTeX macros for a readable formula)
    ```latex
    $$
    \Pr(M | D) \propto \Pr(D | M)\, \Pr(M)
    $$
    ```

  - **Bad** (plain text notation, not LaTeX)
    ```text
    a* = argmax_a E_{M~P(M|D)}[Goal | do(a), M]
    ```
  - **Good** (LaTeX formula)
    ```latex
    $$
    a^* = \arg\max_a
      \EE_{M | \Pr(M | D)}
      \left[
        \text{Goal} | do(a), M
      \right]
    $$
    ```

## Convert Symbols to Latex
- Convert symbols into Latex ones, together with variables if needed:
  - **Bad** (Unicode arrow instead of LaTeX)
    ```text
    X → Y
    ```
  - **Good** (LaTeX symbol)
    ```latex
    $X \to U$
    ```
- If there are expressions then leave them unchanged
  - **Bad**
    ```text
    "If battery low" → seek charging station
    ```
  - **Bad**
    ```text
    "If battery low" $\to$ seek charging station
    ```

## Lint the File
- After the conversion run the command:
  ```bash
  > lint_text.py -i <FILE>
  ```

# Verification
- [ ] Confirm all formulas render correctly in LaTeX
- [ ] Confirm non-formula expressions remain unchanged
- [ ] Confirm `lint_text.py -i <FILE>` completes without errors
