---
description: Update the content of a book given the changes in the corresponding source content
model: opus
---

- Given the content of a book in the form of a markdown or tex file `<TARGET>` and a
  source `<FILE>`, find and incorporate the changes from `<FILE>` into `<TARGET>`

- E.g., the file `<FILE>` contains a header like:
  ```
  % git_hash=<GIT_HASH>, timestamp=<TIMESTAMP>
  % <FILE>
  ```
  with the last version in terms of Git hash and timestamp of the material that was
  used to generate the current version of `<TARGET>`

- E.g.,
  ```
  % git_hash=f15bc6b9, timestamp=2026-07-15 14:41:12 EDT
  % book_springer/lectures_source/Lesson02.1_From_Data_Science_To_Decision_Science.txt
  ```

- Find what has changed in file `<FILE>` from `<GIT_HASH>` to now and modify
  `<TARGET>` to incorporate those changes

- Follow the same style of `<TARGET>` (e.g., read the corresponding
  `.claude/skills/*.rules.md`)
