---
description: Update slides to match changes in the source slides they cite
model: sonnet
---

# Goal
- Given a slides file `<TARGET>` (`.smd`) whose slides cite their source slides
  with `// From: <SOURCE>:<LINE> '<source line>'` comments, find what changed in
  each `<SOURCE>` and incorporate it into the citing slide of `<TARGET>`

- Optionally the user passes a scope (a slide title or a line range in
  `<TARGET>`): process only the slides in that scope

# Workflow
- Read the conventions in `.claude/skills/slides.rules.md`, especially
  `## Source Attribution (`// From: ...`)`

## List the Citations
- Extract every `// From:` line of `<TARGET>` with its line number
  ```bash
  > grep -n "^// From:" <TARGET>
  ```
- Attach each citation to the slide it sits under, i.e., the nearest preceding
  `* <slide title>` line
- Skip a bare `// From: ...` (nothing after the colon): it marks a slide with no
  identified source. Do not guess a source and do not drop the line
- Group the citations by `<SOURCE>` file, so each `<SOURCE>` is read once

## Resolve Each Source Slide
- Check that `<SOURCE>` exists. If it does not exist, report it and go to the
  next citation
- Find the current position of the cited line in `<SOURCE>`
  - Search for the verbatim `'<source line>'` text (including its leading
    `* `, `#`, `## `, `### ` marker), since `<LINE>` drifts whenever `<SOURCE>` is
    edited above it
    ```bash
    > grep -nF -- '<source line>' <SOURCE>
    ```
  - If several lines match, pick the one closest to the recorded `<LINE>`
  - If nothing matches, the source slide was renamed, moved, or deleted
    - Search for the title text without its marker, and for a close variant
    - If a single clear candidate exists, use it and record the new text in the
      `// From:` line
    - If no candidate exists, report it as "source missing", leave the slide and
      its `// From:` line unchanged, and go to the next citation
- Extract the source content
  - For a `* <slide title>` line: the lines up to the next `* ` slide or `#`
    header line
  - For a `#`, `##`, `###` header line: the lines up to the next header of the
    same or higher level. Only the part that matches the topic of the citing
    slide is relevant
  - For a `- [P<NNN>]` or `- [B<NNN>]` entry in `related_papers.md` or
    `related_books.md`: the entry itself. Compare only its text (authors,
    title, year, link) with the reference used in the slide

## Find What Changed
- The optional `<BASE>` (a Git hash) is the version of `<SOURCE>` the slide was
  last synced with
  - If the user passes it, use it
  - Otherwise use the last commit that touched `<TARGET>`:
    ```bash
    > git log -1 --format=%H -- <TARGET>
    ```
- Get the diff of `<SOURCE>` once per file, not once per slide:
  ```bash
  > git diff <BASE> -- <SOURCE>
  ```
  - Use the diff as a hint to find the changed slides fast
  - Always compare the current source text with the citing slide text too,
    because a slide may have been synced from an older version than `<BASE>`
- Compare the source content with the citing slide and classify each difference
  - **Substantive** (incorporate it)
    - A new or changed definition, claim, number, equation, or example
    - A new bullet that adds an idea absent from the slide
    - A retracted or corrected fact
    - A changed `graphviz`, `mermaid`, `tikz` code block or image link
  - **Cosmetic** (ignore it)
    - Rewording, reordering, or formatting that the slide already adapted
    - Tag, bold, or punctuation changes that only follow `slides.rules.md`

## Incorporate Changes
- Edit the citing slide of `<TARGET>` to reflect every substantive change
- Keep the slide as an adaptation, not a copy
  - Keep the slide title, the structure, and the wording that the author already
    adapted
  - Rename the slide only if the change renames the concept
  - Do not paste the source text over the slide
- When a slide cites several sources, reconcile each `// From:` line in turn
  - Keep the content that comes from the other sources
  - Remove content only if its own source dropped or retracted it
- Do not delete slide content only because the source no longer has a
  counterpart: the slide may combine several sources or add material of its own.
  Remove content only when the diff shows that the fact or example was changed or
  retracted, not merely moved
- Write the new text following `.claude/skills/slides.rules.md`
  - E.g., semantic tags, 80 columns, no back-reference to other lessons, no
    dashes as punctuation
- If a change cannot be applied without a decision from the user (e.g., the source
  restructured one slide into three), do not guess: leave the slide unchanged
  and report the question

## Update the `// From:` Lines
- Rewrite each resolved `// From:` line to the current position and text of its
  source line
  ```text
  // From: <SOURCE>:<NEW_LINE> '<NEW_SOURCE_LINE>'
  ```
  - `<NEW_LINE>` is the current line number of the source line in `<SOURCE>`
  - `<NEW_SOURCE_LINE>` is that line verbatim, including its leading marker
- Do this for every resolved citation, including the ones with no content change,
  since an edit above the source slide shifts its line number
- Do not touch a bare `// From: ...` line or a source-missing citation
- Keep one `// From:` line per source, stacked directly under the slide title, in
  the original order

## Report
- Print one line per citation with one status
  - `updated`: content changed, with a short list of what changed
  - `unchanged`: content in sync (line number possibly refreshed)
  - `source missing`: the source file or slide was not found
  - `needs decision`: a change that needs the user
- Do not commit. The user reviews the diff of `<TARGET>` first

# Conventions
- Follow the slide conventions in `.claude/skills/slides.rules.md`
- The related skill `.claude/skills/book.update_from_source/SKILL.md` does the same
  synchronization for a book chapter (`.typ`, `.tex`, `.md`) instead of `.smd`
  slides

# Constraints
- Never modify `<SOURCE>`
- Never change a slide that has no `// From:` line or only a bare `// From: ...`
- Never invent a source, a line number, or a source line text: copy them from
  `<SOURCE>`
- Never commit

# Verification
- [ ] Every non-bare `// From: <SOURCE>:<LINE> '<source line>'` in `<TARGET>`
  points at a line that exists in `<SOURCE>`, and that line matches the quoted text
  ```bash
  > sed -n '<LINE>p' <SOURCE>
  ```
- [ ] Every substantive change found in the diff of `<SOURCE>` is reflected in the
  citing slide, or listed as `needs decision` in the report
- [ ] No slide lost content that its source still supports
- [ ] The edited slides still follow `.claude/skills/slides.rules.md`
  - For a full check, run `.claude/skills/slides.lint/SKILL.md` on `<TARGET>`
- [ ] `git diff <TARGET>` shows only the intended slide and `// From:` changes
