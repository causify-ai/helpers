- TODOs are organized in different stage of executing , using H1 markdown headers
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

- In general the same topics should be present in all H1 levels
  - If there is a task in one stage, it should have the same 

- Each task is represented by a H3 markdown header, under the corresponding H2 header
  ```
  ### [ ] Finish dev_scripts_helpers/ai/README.md
  - ...
  - ...
  ```

- There is a file called `DONE.md` that contains all the tasks that were completed
  using the same organization of H2 markdowns as the 
