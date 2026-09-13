---
description: Move completed tasks from ai_task_queue.md and TODO.md into DONE.md, organized by the topics in ai_task_queue.md's ALL TOPICS section
---

# Goal

- Find every top-level completed task (`### [x] <Title>`) in `ai_task_queue.md` and
  `TODO.md`
- Move each one into `DONE.md`, grouped under the same `## <Topic>` headers used in
  the `# ALL TOPICS` section of `ai_task_queue.md`
- Leave in-progress (`[ ]`, `[.]`) tasks and nested checklist items untouched

# References

- `.claude/skills/todo.rules.md`: defines the H1 stage / H2 topic / H3 task
  organization, and the rule that `DONE.md` reuses the `# ALL TOPICS` H2 headers from
  `ai_task_queue.md`

# Workflow

## Load the Conventions

- Read `.claude/skills/todo.rules.md`
- Read the `# ALL TOPICS` section of `ai_task_queue.md` and extract the ordered list
  of `## <Topic>` headers (ignore `// <group>` comment lines, they are just visual
  grouping, not topics)

## Find Completed Tasks

- In `ai_task_queue.md` and `TODO.md`, find every H3 header that matches exactly
  `### [x] <Title>`
  - Do NOT move `### [ ]`, `### [.]`, or any other marker
  - Do NOT move nested checklist items like `- [x] ...`; those are subtask progress
    inside a task that is not itself done
- For each match, capture the full task block: the header line through everything up
  to (but not including) the next H1/H2/H3 header

## Determine the Target Topic

- Find the nearest enclosing H2 header for the task in its source file
- If that H2 header name matches (case-insensitively) one of the ALL TOPICS entries,
  use it as the target topic
- Otherwise (e.g. the enclosing header is a placeholder like `## ?`, or the file uses
  a different H2 taxonomy, as `TODO.md` often does), infer the target topic from the
  task's content against the ALL TOPICS list
- If no ALL TOPICS entry is a plausible match, do not guess: list the task and ask
  the user which topic to use, or whether to add a new topic to `# ALL TOPICS`

## Move the Tasks

- For each completed task, in source-file order:
  - Remove the task block from its source file, closing the resulting blank line gap
    so surrounding spacing stays normal
  - Append the task block, unchanged, under the matching `## <Topic>` header in
    `DONE.md`
    - If `DONE.md` has no header for that topic yet, create one, keeping the new
      headers in the same order as `# ALL TOPICS`
    - Keep multiple tasks for the same topic together under one header

## Report

- List every moved task as `<Title> (<source file>) -> ## <Topic>`
- List separately any completed task that could not be confidently mapped to a topic,
  and why

# Verification

- [ ] Every `### [x] ...` task originally in `ai_task_queue.md` or `TODO.md` is now
      in `DONE.md`, and no longer in its source file
todo.move_done- [ ] No `[ ]`, `[.]`, or nested `- [x]` item was moved or altered
- [ ] Each moved task sits under a `## <Topic>` header that also appears in
      `ai_task_queue.md`'s `# ALL TOPICS` section
- [ ] Task content (title, body) is unchanged from the source file
- [ ] Source files still have correct markdown structure (no orphaned blank headers,
      no broken spacing) after removal
