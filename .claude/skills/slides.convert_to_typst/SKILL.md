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

- Convert $\EE$ to $frak(E)$
- Convert $\VV$ to $frak(V)$

- Keep all the variables, e.g., x and f(x) in math mode

- Do not use P₀ but $P_0$

## Conversion Rules


    ```{=typst}
    $ Pr(X_1 , ... , X_n) = product_(i = 1)^n Pr(X_i | "Parents"(X_i)) $
    ```

## Quality Checks
- Verify all markdown elements are converted
- Check that slide hierarchy is preserved
- Ensure no content is lost or corrupted
- Validate Typst syntax (no unclosed brackets, proper formatting)
