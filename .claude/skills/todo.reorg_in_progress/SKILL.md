---
description: Reorganize ai_task_queue.md so in-progress tasks, not-started tasks, and mislabeled topic headers sit under the right H1 stage
---

# Goal

- Move every `### [.] <Title>` task (in progress) into the `# IN PROGRESS` section,
  under its topic's `(IN PROGRESS)` H2
- Move every `### [ ] <Title>` task (not started) that sits under `# IN PROGRESS` into
  `# BACKLOG`, under its topic's `(BACKLOG)` H2
- Move any H2 topic header whose `(<Stage>)` suffix doesn't match its enclosing H1
  stage to the H1 stage the suffix names, together with all its tasks
- Leave `### [x] ...` tasks and nested checklist items (`- [ ]`, `- [x]`, `- [.]`)
  untouched

# References

- `.claude/skills/todo.rules.md`: defines the H1 stage / H2 topic / H3 task
  organization and the `## <Topic> (<Stage>)` header convention

# Workflow

## Load the Conventions

- Read `.claude/skills/todo.rules.md`
- Identify the H1 stage headers present in `ai_task_queue.md` (e.g. `# IN PROGRESS`,
  `# BACKLOG - HIGH PRIORITY`, `# BACKLOG`, `# ICEBOX`, `# ALL TOPICS`)
- Never touch the `# ALL TOPICS` section in this skill

## Phase 1: Refile Mislabeled H2 Topics

- Do this phase first: fixing a misfiled topic before the task-marker rules run keeps
  the topic's tasks together instead of letting Phase 2/3 split them across stages
- For every H2 header `## <Topic> (<Stage>)` found outside `# ALL TOPICS`:
  - Compare `<Stage>` to the name of its enclosing H1
  - Mismatch -> cut the entire H2 block (the header line through everything up to the
    next H2 or H1) and move it under the H1 that matches `<Stage>`
    - If an H2 with the same bare `<Topic>` already exists under that H1, append the
      moved block's task content there and drop the duplicate header line, instead of
      creating a second header for the same topic
    - Otherwise, insert the moved H2 block at the end of that H1's section (right
      before the next H1 header)
    - If `<Stage>` names an H1 that does not exist anywhere in the file, do not create
      it silently: list the header and ask the user whether to create that stage or
      use a different one
  - Keep the moved block's content (task titles, markers, bodies) byte-for-byte
    unchanged aside from its position
  - Example: `## Noesis (BACKLOG - HIGH PRIORITY)` sitting under `# IN PROGRESS` is cut
    and moved, with all its `### ...` tasks, under `# BACKLOG - HIGH PRIORITY`

## Phase 2: Consolidate In-Progress Tasks

- For every `### [.] <Title>` task anywhere in the file that is not already under
  `# IN PROGRESS` (including one exposed by a Phase 1 move):
  - Find its enclosing H2's bare topic name
  - Move the task block (the header line through the next H2, H3, or H1) under
    `## <Topic> (IN PROGRESS)` in the `# IN PROGRESS` section
    - If that H2 doesn't exist yet under `# IN PROGRESS`, create it at the end of the
      section
  - If the task's original H2 is left with no task content, remove the now-empty H2
    header

## Phase 3: Demote Not-Started Tasks Out of In Progress

- For every `### [ ] <Title>` task that sits under `# IN PROGRESS` after Phase 1 and 2
  have run:
  - Find its enclosing H2's bare topic name
  - Move the task block under `## <Topic> (BACKLOG)` in the `# BACKLOG` section
    - If that H2 doesn't exist yet under `# BACKLOG`, create it at the end of the
      section
  - If the task's original H2 under `# IN PROGRESS` is left with no task content,
    remove the now-empty H2 header

## Leave Untouched

- `### [x] ...` tasks (handled by `todo.move_done`, not this skill)
- Nested checklist items (`- [ ]`, `- [x]`, `- [.]`) inside a task body: these are
  subtask progress, not task headers
- Any H3 header with no `[ ]`, `[x]`, or `[.]` marker: flag it to the user instead of
  guessing a marker for it
- The `# ALL TOPICS` section

## Ask User

- Any H2 whose `(<Stage>)` suffix names a stage with no matching H1 in the file
- Any H3 task header carrying a marker other than `[ ]`, `[x]`, or `[.]`
- Any case where a task's bare topic name doesn't clearly match an existing H2 and it's
  unclear whether to create a new topic H2 or reuse a close match
- Do not guess: list the ambiguous item and ask before moving it

## Report

- List every H2 topic block moved as `<Topic>: <old H1> -> <new H1>`
- List every `[.]` task moved into IN PROGRESS as
  `<Title> (<old H2>) -> IN PROGRESS / <Topic>`
- List every `[ ]` task demoted out of IN PROGRESS as `<Title> -> BACKLOG / <Topic>`
- List every empty H2 header removed as a result of these moves

# Verification

- [ ] No `### [.] ...` task remains outside the `# IN PROGRESS` section
- [ ] No `### [ ] ...` task remains under the `# IN PROGRESS` section
- [ ] No H2 header outside `# ALL TOPICS` has a `(<Stage>)` suffix that mismatches its
      enclosing H1
- [ ] No H2 header is left empty (zero task content) after the moves
- [ ] `### [x] ...` tasks and nested checklist items are unchanged and in their
      original location
- [ ] Task content (title, body) is unchanged aside from its position
- [ ] `# ALL TOPICS` section is unchanged
