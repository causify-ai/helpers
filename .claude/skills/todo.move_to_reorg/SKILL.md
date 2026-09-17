---
description: Move tasks out of ai_task_queue.md's TO REORG section into the right H1 stage and H2 topic, using an optional Priority tag, after user confirmation
---

# Goal

- Find every H3 task sitting under `# TO REORG` in `ai_task_queue.md`
- For each task, determine its target H1 stage (from an optional
  `- Priority: <Stage>` line in the body, defaulting to `# BACKLOG` when absent) and
  its target H2 topic (from the `# ALL TOPICS` list)
- Present the full set of proposed moves to the user and get explicit confirmation
  before changing the file
- Move each confirmed task under `## <Topic> (<Stage>)` in its target H1 section,
  stripping the now-consumed `Priority:` line
- Remove the `# TO REORG` header once it has no tasks left under it

# References

- `.claude/skills/todo.rules.md`: defines the H1 stage / H2 topic / H3 task
  organization, the `## <Topic> (<Stage>)` header convention, and the `# ALL TOPICS`
  master list

# Workflow

## Load the Conventions

- Read `.claude/skills/todo.rules.md`
- Read `ai_task_queue.md`'s `# ALL TOPICS` section; record the ordered list of
  `## <Topic>` headers (ignore `// <group>` comment lines, they are visual grouping,
  not topics)
- Record the H1 stage headers that exist in the file (e.g. `# IN PROGRESS`,
  `# BACKLOG - HIGH PRIORITY`, `# BACKLOG`, `# ICEBOX`); these are the only valid
  move targets

## Find the Tasks to Reorg

- In `ai_task_queue.md`, find every H3 header under `# TO REORG`
- For each one, capture the full task block: the header line through everything up to
  (but not including) the next H1/H2/H3 header

## Determine the Target H1 Stage

- Look for a line matching `- Priority: <Stage>` anywhere in the task body
  - Match `<Stage>` case-insensitively against the file's H1 stage headers (e.g
    `Icebox` -> `# ICEBOX`, `High Priority` -> `# BACKLOG - HIGH PRIORITY`, `Backlog`
    -> `# BACKLOG`, `In Progress` -> `# IN PROGRESS`)
  - If `<Stage>` doesn't clearly match any existing H1, do not guess: list the task
    and ask the user which H1 stage to use
- If no `- Priority:` line is present, propose `# BACKLOG` as the default target
  stage; this is only a proposal and can be overridden at the confirmation step

## Determine the Target H2 Topic

- Match the task's content against the `# ALL TOPICS` list, the same way
  `todo.move_done` infers a topic
- If no ALL TOPICS entry is a plausible match, do not guess: list the task and ask
  the user whether to use the closest existing topic or add a new one to
  `# ALL TOPICS`

## Propose the Moves

- Before changing anything, print one line per task in the form:

  ```
  ### <Title> -> ## <Topic> (<Stage>)
  ```

- Group the list by target `<Stage>` so the user can scan it stage by stage
- Flag, next to the line, any task whose stage came from the default (no `Priority:`
  tag found) so the user knows it's a guess, not a tag-driven placement
- Stop and wait for explicit user confirmation of this list (as a whole, or with
  corrections) before making any edit to `ai_task_queue.md`

## Execute the Moves

- Only after the user confirms, for each approved task in source order:
  - Remove the `- Priority: <Stage>` line (and the blank line it leaves behind) from
    the task body; this tag only exists to route the task out of `# TO REORG` and
    isn't part of the normal task format
  - If the H3 header carries no `[ ]`, `[x]`, or `[.]` marker, rewrite it to
    `### [ ] <Title>`; leave an existing marker unchanged
  - Cut the task block from `# TO REORG`, closing the resulting blank line gap
  - Append the task block under `## <Topic> (<Stage>)` in the confirmed H1 section
    - If that H2 doesn't exist yet under the target H1, create it at the end of the
      section
    - Keep multiple tasks for the same topic together under one header

## Clean Up

- After all confirmed tasks are moved, if `# TO REORG` has no task content left,
  remove the `# TO REORG` header entirely
- If some tasks were left unresolved (ambiguous stage or topic), keep `# TO REORG`
  with only those tasks remaining

# Ask User

- Any task whose `Priority:` value doesn't match an existing H1 stage
- Any task whose topic can't be confidently matched to `# ALL TOPICS`
- The full proposed move list, before any file edit happens
- Do not guess on an ambiguous case: list it and ask

# Report

- List every executed move as `<Title>: TO REORG -> ## <Topic> (<Stage>)`
- List every task left in `# TO REORG` unresolved, and why
- State whether the `# TO REORG` header was removed or kept

# Verification

- [ ] No file edit happened before the user confirmed the proposed move list
- [ ] Every moved task sits under a `## <Topic> (<Stage>)` header whose bare topic
      also appears in `# ALL TOPICS`
- [ ] Every moved task's H1 section matches its confirmed target stage
- [ ] No `- Priority:` line remains in any moved task
- [ ] Every H3 task header carries a `[ ]`, `[x]`, or `[.]` marker after the move
- [ ] Task content (title, body) is unchanged aside from the removed `Priority:` line
      and its position
- [ ] `# TO REORG` is removed if empty, or left with only unresolved tasks
- [ ] `# ALL TOPICS` is unchanged except for topics explicitly added during this pass