---
description: Read, criticize, and propose improvements for a proposed book chapter in a table of content
model: opus
---

# Goal
- Criticize a proposed chapter (or set of chapters) in a book's table of content
  and propose concrete, ranked improvements to topics, ordering, scope, and
  audience fit
- Target: a `## N: Title` section of a `book_map.md`
  - E.g., `## 15: Building Stakeholder Alignment` from `book.springer/book_map.md`

- Read the structure of a `book_map.md` which is defined in
  `.claude/templates/book_map.template.md`

# Workflow

## Step 1: Read Context
- Read `.claude/templates/book_map.template.md` for the expected structure
- The `book_map.md` it lives in, read whole for context, not just the target
  section
  - Read the `**Title**` and `**Target audience**` at the top of `book_map.md`
  - Read the target chapter's overview line, `### Topics`, and `### Lessons`
  - Read the `# Part` heading and scope description the chapter belongs to
  - Read the sibling chapters in that Part and the immediate neighbors, chapter
    N-1 and N+1, to judge continuity


## Step 2: Criticize
- Evaluate along these axes, reporting only issues you are confident about:
  - **Internal flow**: order of the `### Topics` bullets, prerequisite ordering,
    redundant or overlapping bullets, a bullet that is really two topics
  - **Cross-chapter flow**: overlap with neighbors or others in the same Part, a
    topic that belongs earlier or later, forward references to concepts not yet
    introduced
  - **Part fit**: does the chapter match the scope description of its `# Part`
    (foundations vs. advanced theory vs. deployment); flag misplaced chapters
  - **Structure conformance**: missing overview line, empty required
    subsections, Lessons without a FULL/PART/WEAK tag, references not following
    `.claude/skills/book.rules.md`
  - **Audience fit**: matches the stated audience; level too high or low, assumed
    background, unexplained jargon
  - **Scope and balance**: too much or too little for one chapter; candidates to
    split or merge

- Rank each issue by severity:
  - **CRITICAL**: breaks the chapter's logic or misplaces it
  - **HIGH**: misleads or confuses the reader
  - **MEDIUM**: hurts clarity or completeness
  - **LOW**: minor polish

- Emit one section per axis, most severe issue first:
  ```markdown
  # Criticism: <chapter header>

  ## Internal flow
  1. [CRITICAL/HIGH/MEDIUM/LOW] <issue>: <why>; <suggested fix>
  ...

  ## Cross-chapter flow
  ...

  ## Part fit
  ...

  ## Structure conformance
  ...

  ## Audience fit
  ...

  ## Scope and balance
  ...
  ```
- Follow `.claude/skills/markdown.rules.md` to write the comments

## Step 3: Wait for Approval
- Present the criticism to the user
- Wait for the user to select items to apply by index and give corrections
- Only then edit `book_map.md`
- Make sure to update all the sections (e.g., Topics, Lessons, Tutorials, Related
  packages, Related books, Related papers)
