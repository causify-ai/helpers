---
description: Convert markdown slides to Typst-compatible format via pandoc
model: sonnet
---

# Goal
- Convert a markdown slides file to Typst presentation format
- Preserve structure, content, and formatting
- Output clean, well-formatted markdown code suitable for conversion to Typst

## Workflow

1. **Read input file**: markdown slides file (e.g., `lectures.md`)
2. **Apply conversion rules**: systematically fix math, unicode, and formatting
3. **Validate output**: verify no content loss, structure preserved
4. **Output file**: write converted markdown with same base name

## Conversion Rules

### LaTeX Custom Commands
- Replace presentation-specific commands with Typst equivalents:
  - `$\EE$` → `$bb(E)$` (blackboard E)
  - `$\VV$` → `$bb(V)$` (blackboard V)
  - `$\Pr$` → `$Pr$` (remove backslash)

### Variables & Math Expressions
- Wrap all variables, parameters, and math expressions in `$...$`:
  - **Bad**: `Randomly permute the values of x_j across all samples`
  - **Good**: `Randomly permute the values of $x_j$ across all samples`
  - **Bad**: `Compute f(x) and g(x)`
  - **Good**: `Compute $f(x)$ and $g(x)$`

### Unicode → LaTeX
- Replace unicode math characters with LaTeX:
  - Ω → `$\Omega$`
  - → → `$\to$`
  - ≤ → `$\leq$`
  - × → `$\times$`

### Subscripts & Superscripts
- Use math mode for all subscripts/superscripts:
  - **Bad**: P₀ or P^n
  - **Good**: `$P_0$` or `$P^n$`

### Math Operators
- Use `op()` for named operators in Typst:
  - **Bad**: `$g^* = arg min_(g in G)$`
  - **Good**: `$g^* = op("arg min")_(g in G)$`
  - Also: `$max_i x_i$` → `$op("max")_i x_i$`

### Plain Numbers & Currency
- Do NOT wrap pure numbers in math mode:
  - **Bad**:
    ```
    The house costs $50k because it has 4 bedrooms ($+\$30$k)
    ```
  - **Good**:
    ```
    The house costs \$50k because it has 4 bedrooms (+\$30k)
    ```

### Block Formulas
- Use Typst code blocks for complex multi-line formulas:
  ```{=typst}
  $ Pr(X_1 , ... , X_n) = product_(i = 1)^n Pr(X_i | "Parents"(X_i)) $
  ```

## Quality Checks

- All slide headers & hierarchy preserved  
- No content deleted or truncated  
- All math expressions wrapped (`$...$`)  
- No unicode math characters remain  
- Operators properly formatted with `op()`  
- Code blocks and lists intact  
- File is valid markdown
