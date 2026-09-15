## Execution Stages

- TODOs are organized in different stage of execution, using H1 markdown headers,
  e.g.,
  ```
  # IN PROGRESS
  <Tasks that are in progress>

  # HIGH PRIORITY
  <Tasks that need to be executed soon>

  # BACKLOG
  <Tasks that are ready to be executed>

  # ICEBOX
  <Tasks that are low priority or not completely specified>

  # ALL TOPICS
  <Contains a list of all the possible H2 topics, separated by // in mega-topics>
  ```

## Topic
  
- Each "topic" groups several tasks and uses H2 markdown headers
  - Some topics are general engineering 
    ```
    ## Unit tests
    ...
    ## Build breaks
    ...
    ## Reorg the docs
    ...
    ## Springer Book
    ...
    ## Worktree
    ...
    ```
  - Some topics are related to specific tools
    ```
    ## notes_to_pdf.py
    ...
    ## invoke gh_watch
    ...
    ```

- Make sure that the same topics are present in all H1 levels
  - If there is a task `### ...` in one stage, it should be under the correct H2
    header

- Since the same topic name repeats under multiple H1 stages, each H2 header
  (except in `# ALL TOPICS`) must be suffixed with its stage in parenthesis,
  `## <Topic> (<Stage>)`, e.g.,
  ```
  ## umd_msml610 (IN PROGRESS)
  ...
  ## umd_msml610 (BACKLOG)
  ...
  ## umd_msml610 (ICEBOX)
  ```
  - The `# ALL TOPICS` list keeps the bare topic name (no stage suffix), since
    it is the canonical list of topics matched by `todo.reorg` and
    `todo.move_done`

## Task

- Each task is represented by a H3 markdown header, under the corresponding H2 header
  ```
  ### [ ] Finish dev_scripts_helpers/ai/README.md
  - ...
  - ...
  ```

## DONE.md
- The `DONE.md` contains all the tasks that were completed
- It uses the same organization of H2 markdowns as in `# ALL TOPICS` in
  `ai_task_queue.md`
- Only tasks marked as completed can be there `### [x] <Title>`
