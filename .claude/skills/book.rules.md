Conventions for maintaining a book map (`map.md`) that tracks a book's title,
audience, roadmap, and chapter-by-chapter table of contents mapped to existing
course lecture materials.

# Concepts
- `map.md`: the map of a book / course, e.g.,
  - `/Users/saggese/src/umd_classes2/book_springer/map.md`
  - `/Users/saggese/src/umd_classes1/book.AI_for_data_science/map.md`
  - `/Users/saggese/src/umd_classes1/book.Modern_AI_for_Finance/map.md`
  - `/Users/saggese/src/umd_classes1/msml610/map.md`
  ...
- `chap_toc`: contains a description of a book chapter
  - It is `### topics` in a map
- `skeleton_slides`
  - describes the high level flow of slides
  - contain only H1, H2, * and optionally `// From <file>:<line number> 'reference'`
- `lesson_slides`: complete slides on a topic
  - E.g., data605, msml610, book_springer
  - The slides can be on a topic (e.g., from data605, msml610) or merged slides
    from existing lesson slides (e.g., book_springer)
  - Merged slides cite their lecture/paper sources with `// From: ...`
    comments right under the slide title; see `.claude/skills/slides.rules.md`
    ("Source Attribution") for the exact syntax
- `slide_tutorials`: notebooks associated with `lesson_slides`
- `book_chap`: a tex / typst file storing the text of the book corresponding to
   the `lesson_slides`

## Invariants
- We need to maintain in sync the following data:
  - `map`
  - `chap_toc`
  - `lesson_slides`
  - `slide_tutorials`
  - `book_chap`
  since they are representation at different levels of abstraction of the same
  content (i.e., a book / course)

# Overall Structure

- A book map follows this top-level section order:
  - **Summary**: Title, Target Audience, Approach of the Book, Short TOC, All
    Lesson Materials
  - **Roadmap**: tracking tables for slide/criticize/tutorial/book progress,
    plus tutorial inventories and a TODOs list
  - **Detailed TOC**: one `# Part <N>: <Part Title>` heading per part, one
    `## <NN>: <Chapter Title>` heading per chapter, each following the Chapter
    Template below
  - **Appendix**: optional, for material that does not belong to a chapter

# Writing Conventions

- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for text formatting
- Keep coverage percentages grounded in the actual lecture files, not guessed
- Chapter numbers in `## <NN>: <Chapter Title>` are zero-padded two digits and
  match the numbering in `## Short TOC`

# Section Details

## Title
- 1-2 bullets giving alternative titles/framings for the same book

## Target Audience
- 2-3 bullets: who the reader is, and what background/prerequisites are assumed

## Approach of the Book
- Bullets describing what the book focuses on (minimal math, intuition, toy
  examples, making theory operational via packages, notebooks) and what
  resources it points readers to for going one level deeper (classes, books,
  papers)

## Short TOC
- Nested bullets: level-1 is the part name, level-2 is `<NN>, <Chapter Title>`
- Lists every part and chapter in book order; kept in sync with the `# Part` and
  `## <NN>:` headings in Detailed TOC

## All Lesson Materials
- Inventory of candidate source directories/globs each chapter's `### Lesson
  Materials` can draw from, one bullet pair per course:
  ```markdown
  - `course/all_tocs.md`
  - `course/resources.md`
  - `course/lectures_source/*.txt`
  ```
- Regenerate with the pointed-to script (e.g., `./generate_all_tocs.sh`) instead
  of hand-editing the list

# Chapter Template

- Each chapter (`## <NN>: <Chapter Title>`) uses this fixed set of `###`
  subsections, in this order:
  - `Goals`
  - `Topics`
  - `TODO` (optional)
  - `Slides`
  - `Lesson Materials`
  - `Notes` (optional)

## Goals
- 3 bullets, each under 100 characters, stating what the chapter achieves

## Topics
- Nested bullets: level-1 bullets are subchapter titles, level-2 bullets are a
  short list of topics under that subchapter
- Template:
  ```markdown
  ### Topics
  - Topic 1
    - Subtopic 1.1
    - Subtopic 1.2
  - Topic 2
    ...
  ```
- Keep the section under 20-25 lines and 175-200 words

## TODO
- Optional; open items for the chapter as a checkbox list (`- [ ] ...`)

## Slides
- Pointer(s) to the `lectures_source/*.txt` (or `.smd`) file(s) holding the
  chapter's slide deck
- Each deck should be about 30-35 slides

## Lesson Materials
- For each chapter, read its `### Topics` and the candidate lecture ToCs listed
  in `## All Lesson Materials`, then list which lectures cover which topics
- Order lectures by descending coverage percentage
- Reference the actual lecture files (not just their titles) to verify coverage
- Close with a `_Not covered_` (or `- Not covered`) bullet naming the topics no
  lecture addresses
- Template:
  ```markdown
  ### Lesson Materials
  - `pointer to a lecture`
    - [<Amount used>]: topics
  - ...
  - _Not covered_
    - [<Amount of topics not covered by any lesson>]: <topics>
  ```
- Example:
  ```markdown
  ### Lesson Materials
  - `msml610/lectures_source/Lesson11.1-Decision_Making_with_Causal_Models.txt`
    - [95%]: Causal effects to expected value, EVPI/EVSI, Bayesian optimization,
      causal multi-armed bandits, exploration vs. exploitation
  - `msml610/lectures_source/Lesson09.3-Multi_Armed_Bandits.txt`
    - [90%]: Thompson sampling, UCB, epsilon-greedy, contextual bandits, regret
      bounds
  - _Not covered_
    - [50%]: Minimax/distributional robustness against model misspecification,
      formal sensitivity analysis, advanced acquisition-function design
  ```

## Notes
- Optional freeform bullets for open questions or caveats about the chapter

# Roadmap Section

- Tracking tables use `|`-delimited Markdown tables with a bold
  `**Part Title**` row (all other columns empty) separating parts
- Typical columns: chapter/slide name, source slide file, and one column per
  pipeline stage (e.g., `Slides %`, `Criticize`, `Tutorial`, `Book`), each cell
  a completion percentage or `yes`/blank
- Tutorial inventories are a `>` blockquote with the `find` command used to list
  them, followed by a fenced (no language) block with the resulting file paths:
  ```markdown
  > find book_springer/tutorials -name *.ipynb
  book_springer/tutorials/LessonNN_topic/notebook.ipynb
  ```
- `## TODOs` is a flat bullet list of outstanding cross-chapter work

# Examples
- `book_springer/map.md`
