---
description: Convert markdown slides to format that can be converted by pandoc to Typst
model: haiku
---

# Goal
- Convert a markdown slides file to Typst presentation format
- Preserve structure, content, and formatting
- Output clean, well-formatted markdown code suitable for conversion to Typst

## Input
- The user will provide:
  - A markdown slides file `<INPUT_FILE>`
  - (Optional) Target template or style preferences

- Read the input file `<INPUT_FILE>`

## Conversion Rules
- Convert $\EE$ to $bb(E)$
- Convert $\VV$ to $bb(V)$
- Convert $\Pr$ to $Pr$

- Keep all the variables and expressions in the text (e.g., x, f(x)) in math mode
  wrapping them in $...$
  - **Bad**
    ```
    Randomly permute the values of x_j across all samples
    ```
  - **Good**
    ```
    Randomly permute the values of $x_j$ across all samples
    ```

- Use the math version, instead of unicode characters
  - **Bad**: `Ω(g) penalizes complexity...`
  - **Good**: `$\Omega(g)$ penalizes complexity...`
  - **Bad**: →
  - **Good**: $\to$

- Use math expressions instead of superscript and subscripts 
  - **Bad**: P₀
  - **Good**: $P_0$

- In math expressions use
  - **Bad**: `g^* = arg min_(g in G)`
  - **Good**: `$g^* = op("arg min")_(g in G)`

- Do not use math for numbers
  - **Bad**
    ```
    - Local: _"This house is priced \$50k above average because it has 4
      bedrooms ($+\$30$k) and is near a school ($+\$20$k)"_
    ```
  - **Good**
    ```
    - Local: _"This house is priced \$50k above average because it has 4
      bedrooms (+\$30k) and is near a school (+\$20k)"_
    ```

- For complex formulas use
  ```{=typst}
  $ Pr(X_1 , ... , X_n) = product_(i = 1)^n Pr(X_i | "Parents"(X_i)) $
  ```

## Quality Checks
- Verify all markdown elements are converted
- Check that slide hierarchy is preserved
- Ensure no content is lost or corrupted
