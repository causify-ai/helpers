---
description: Convert markdown slides to Typst-compatible format via pandoc
model: haiku
---

# Goal
- Convert a markdown slides file to Typst presentation format
- Preserve structure, content, and formatting
- Output clean, well-formatted markdown code suitable for conversion to Typst

# Workflow

## Read Input File
- Read the markdown slides file (e.g., `lectures.md`)

## Apply Conversion Rules
- Systematically fix math, unicode, and formatting

## Validate Output
- Verify no content loss and structure preserved

## Output File
- Write converted markdown with same base name

## Conversion Rules

### LaTeX Custom Commands
- Replace presentation-specific commands with Typst equivalents:
  - `$\EE$` → `$bb(E)$` (blackboard E)
  - `$\VV$` → `$bb(V)$` (blackboard V)
  - `$\Pr$` → `$Pr$` (remove backslash)

### Variables & Math Expressions
- Wrap all variables, parameters, and math expressions in `$...$`:
  - **Bad** (unwrapped, renders as plain text): `Randomly permute the values
    of x_j across all samples`
  - **Good** (wrapped in math mode): `Randomly permute the values of $x_j$
    across all samples`
  - **Bad** (unwrapped function notation): `Compute f(x) and g(x)`
  - **Good** (wrapped in math mode): `Compute $f(x)$ and $g(x)$`

### Unicode → LaTeX
- Replace unicode math characters with LaTeX:
  - Ω → `$\Omega$`
  - → → `$\to$`
  - ≤ → `$\leq$`
  - × → `$\times$`

### Subscripts & Superscripts
- Use math mode for all subscripts/superscripts:
  - **Bad** (unicode subscript or bare caret, invalid Typst math): P₀ or P^n
  - **Good** (math mode syntax): `$P_0$` or `$P^n$`

### Math Operators
- Use `op()` for named operators in Typst:
  - **Bad** (named operator unwrapped, Typst renders it as variables): `$g^* =
    arg min_(g in G)$`
  - **Good** (wrapped with `op()`): `$g^* = op("arg min")_(g in G)$`
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

## Verification
- [ ] Make sure that the converted slides render correctly, e.g.,
  ```bash
  > gen_slides.py -i <FILE> --notes_to_pdf_args="--skip_action open_pdf"
  ```
