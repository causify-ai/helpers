---
description: Reorganize ai_task_queue.md .md so every H2 topic matches ALL TOPICS and every H3 task sits under the right topic, keeping its H1 stage
---

# Goal

- Align the H2 topic headers in `ai_task_queue.md` with the canonical list in
  `ai_task_queue.md`'s `# ALL TOPICS` section
- Fold in stray H2 topics: either add them to `# ALL TOPICS` in the right place, or
  merge them into an existing topic
- Move each H3 task under the correct H2 topic, without moving it out of its current
  H1 stage
- Normalize every H3 task header to carry a checkbox marker, without changing markers
  that already exist

# References

- `.claude/skills/todo.rules.md`: defines the H1 stage / H2 topic / H3 task
  organization and the `# ALL TOPICS` master list

# Workflow

## Load the Conventions

- Read `.claude/skills/todo.rules.md`
- Read `ai_task_queue.md`'s `# ALL TOPICS` section; record the ordered list of
  `## <Topic>` headers, keeping the `// <group>` comment lines as group boundaries
  (they mark where a topic belongs, they are not topics themselves)

## Reconcile the Topic Taxonomy

- For every other H1 stage in `ai_task_queue.md` (`IN PROGRESS`, `HIGH PRIORITY`,
  `BACKLOG`, `ICEBOX`, ...) list its H2 headers
- For each H2 header, check whether it matches (case-insensitively) an ALL TOPICS
  entry
  - Match -> keep it, using the exact ALL TOPICS spelling as the canonical header
  - No match -> decide:
    - If it clearly restates or overlaps an existing ALL TOPICS entry (e.g. "Build &
      Infrastructure" vs "Build is green"), merge: rename its header to the existing
      entry and fold its tasks under that topic
    - If it is a genuinely new topic, add it to `# ALL TOPICS` under the closest
      matching `// <group>` comment (or a new group if none fits), then keep it as
      its own H2
    - Placeholder headers with no descriptive name (e.g. `## ?`) are never kept:
      classify every task under them individually by content instead of by header
  - Do not guess silently on an ambiguous case: list it and ask the user to pick the
    merge target vs. a new topic before proceeding
- Apply merges/additions to `# ALL TOPICS` first, so the rest of the pass has one
  final taxonomy to file tasks against

## File Every H3 Task Under the Correct Topic

- Within each H1 stage/section, for every H3 task:
  - Determine its topic from the enclosing (now-canonical) H2 header
  - If the task's content clearly belongs to a different ALL TOPICS entry than its
    current header, move the task block there instead
  - Move only within the same H1 stage: never move a task from `BACKLOG` into
    `HIGH PRIORITY`, as part of this reorg
  - Order the H2 headers within each H1 stage/section to match `# ALL TOPICS`'s
    order; drop any header left with zero tasks after moves
- Keep every moved task block (title, checkbox marker, body) byte-for-byte unchanged
  except for its position

## Normalize Task Checkboxes

- For every H3 header `### <Title>` with no `[ ]`, `[x]`, or `[.]` marker, rewrite it
  to `### [ ] <Title>`
- Leave `### [x] ...`, `### [.] ...`, or any other existing marker exactly as it is

## Ask User
- List any ambiguous case the user and ask them how to resolve it
- Do not make decisions unless you are certain

## Report

- List every topic merge and every new topic added to `# ALL TOPICS`
- List every task moved, as `<Title> (<file>, <H1 stage>): <old H2> -> <new H2>`
- List every checkbox added, as `<Title> (<file>)`

# Verification

- [ ] Every H2 header remaining in `ai_task_queue.md` (outside `# ALL TOPICS`)
      matches an entry in `# ALL TOPICS`
- [ ] No H2 header is left with zero H3 tasks under it
- [ ] Every H3 task still sits under the same H1 stage/section it started in
- [ ] Every H3 task header carries a `[ ]`, `[x]`, or `[.]` marker; markers that
      existed before the reorg are unchanged
- [ ] Task content (title, body) is unchanged aside from its position
- [ ] `# ALL TOPICS` order/grouping is preserved except for the additions made during
      this pass
