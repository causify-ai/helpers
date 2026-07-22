---
description: Read, criticize, and propose improvements for a table of content of a book
model: opus
---

# Goal
- Review and criticize the table of content for a chapter (or set of chapters) in
  a book
- Identify mistakes and improvement opportunities, focusing on factual errors,
  rather than style suggestions
- Propose concrete, ranked improvements to topics, ordering, scope, and audience fit

# Workflow

## Step 1: Read the Material
- Read `.claude/templates/book_map.template.md` for the expected structure of a
  table of content of a book

- Read the `book_map.md` that stores the `### Topics` making up the table of
  content for the book
  - Read `**Title**`, `**Target audience**` at the top of `book_map.md`
  - Read the `# Part` heading description the chapter belongs to
  - Read the target chapter's `### Topics` that the user refers to
  - Ignore the rest of the sections besides `### Topics`
    - I.e., `### Lessons`, `### Tutorials`, `### Related packages`,
      `### Related books`, `### Related papers`
  - Read the `### Topics` in the sibling chapters in that Part and the immediate
    neighbors, chapter N-1 and N+1, to judge continuity

## Step 2: Criticize
- Read `.claude/skills/text.criticize/SKILL.md` to understand general approaches
  to review and criticize text

- Evaluate along these axes, reporting only issues you are confident about:
  - **Internal flow**:
    - Order of the `### Topics` bullets
    - Prerequisite ordering,
    - Redundant or overlapping bullets
    - A bullet that is really two topics
  - **Cross-chapter flow**:
    - Overlap with neighbors or others in the same Part
    - A topic that belongs earlier or later
    - Forward references to concepts not yet introduced
  - **Part fit**:
    - Does the chapter match the scope description of its `# Part` (foundations
      vs. advanced theory vs. deployment)
    - Flag misplaced chapters
  - **Structure conformance**:
    - Compare the structure to `.claude/templates/book_map.template.md`
    - Report parts that don't follow the 
    subsections, Lessons without a FULL/PART/WEAK tag, 
    references not following
    `.claude/skills/references.rules.md`
  - **Audience fit**: matches the stated audience; level too high or low, assumed
    background, unexplained jargon
  - **Scope and balance**: too much or too little for one chapter; candidates to
    split or merge

- Rank each issue by severity:
  - **CRITICAL**: breaks the chapter's logic or misplaces it
  - **HIGH**: misleads or confuses the reader
  - **MEDIUM**: hurts clarity or completeness
  - **LOW**: minor polish

## Step 3: Write Result
- Write results using the same format and file as in 
  `## Step 4: Write the Results` in `.claude/skills/text.criticize/SKILL.md`

## Step 4: Wait for Approval
- Present the criticism to the user
- Wait for the user to select items to apply by index and give corrections
- Only then edit `book_map.md`
- Make sure to update all the sections (e.g., Topics, Lessons, Tutorials, Related
  packages, Related books, Related papers)
