---
description: Make a LaTeX/TikZ or SVG figure look professional by applying the tikz/svg rules, then show a before/after comparison
model: sonnet
---

# Goal
- Take an existing figure (`<FILE>.tex`/TikZ or `<FILE>.svg`) and polish it into a
  publication-quality figure by applying the project's figure conventions
- Prove the improvement by rendering a before/after image and opening it

# Workflow

## Identify the Figure Type
- `.tex` (TikZ/LaTeX source): apply `.claude/skills/tikz.rules.md`
- `.svg` (SVG source): apply `.claude/skills/svg.rules.md`
- If unsure which rules apply, inspect the file extension/content before
  proceeding: never mix the two rule sets on one figure

## Render the Original (Before)
- Render the figure exactly as given, without any edits, to `before.png`
  - TikZ:
    ```bash
    > dev_scripts_helpers/dockerize/dockerized_tikz_to_bitmap.py \
        -i <FILE>.tex -o before.png
    ```
  - SVG:
    ```bash
    > inkscape <FILE>.svg --export-type=png --export-filename=before.png
    ```
- Keep this file untouched: it is the baseline for the comparison at the end

## Apply the Rules
- Read the relevant rules file in full (`tikz.rules.md` or `svg.rules.md`) and
  edit `<FILE>.tex`/`<FILE>.svg` to conform to every section, in particular:
  - Layout & spacing (grid alignment, no cramped or overlapping elements)
  - Color system (restrained, semantic palette; no raw saturated colors)
  - Typography (label-size hierarchy, sentence case, consistent font)
  - Strokes & geometry (consistent line weights, consistent arrowheads/corners)
  - The "What NOT to Do" / anti-pattern list at the end of the rules file
- Do not change the figure's meaning or content: only its visual execution

## Render the Result and Iterate
- Re-render to `after.png` using the same command as above (swap `-o after.png`
  / `--export-filename=after.png`)
- Inspect `after.png`. If it still violates a rule (cramped spacing, overlapping
  labels, inconsistent strokes, non-semantic colors, etc.), fix the source and
  re-render. Repeat until the figure is professional per the rules

## Compare Side by Side
- Build one image with the before and after panels next to each other and open
  it:
  ```bash
  > montage before.png after.png -tile 2x1 -geometry +10+10 -label '%f' comparison.png
  > open comparison.png
  ```

# Verification
- `comparison.png` opened and shows `before.png` and `after.png` clearly
  labeled side by side
- `after.png` has no unresolved violation from the rules file applied above
- The figure's content/meaning is unchanged from the original: only styling
  improved
