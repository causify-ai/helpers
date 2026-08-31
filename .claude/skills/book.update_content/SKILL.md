---
description: Update the content of a book given the changes in the corresponding source content
model: opus
---

- Given the content of a book in the form of a markdown or tex file `<TARGET>` and
  a source file `<SOURCE>`, find and incorporate the changes from `<SOURCE>` into
  `<TARGET>`

- The file `<SOURCE>` contains a header with the last version, in terms of Git hash
  and timestamp, of the material used to generate the current version of
  `<TARGET>`
  - E.g.,
    ```text
    % git_hash=<GIT_HASH>, timestamp=<TIMESTAMP>
    % <SOURCE>
    ```
  - E.g.,
    ```text
    % git_hash=f15bc6b9, timestamp=2026-07-15 14:41:12 EDT
    % book_springer/lectures_source/Lesson02.1_From_Data_Science_To_Decision_Science.txt
    ```

- Find what changed in `<SOURCE>` from `<GIT_HASH>` to now, and modify `<TARGET>` to
  incorporate those changes

- Follow the same style as `<TARGET>` (e.g., read the corresponding
  `.claude/skills/*.rules.md`)
