## Reorganize invokes

### [ ] Unit test the invokes

- Find all the invoke related to git and gh
- Unit test all of them
  - Try to extract functions without side effects so they can be tested independently
  - Use hunteuti.assert_sys_calls( and hunteuti.assert_sys_calls

- Propose a plan, before executing it

### [ ] Factor out scripts

- Propose what code from invoke function body can be moved to a script and have
  invoke just be a pass-through

### [ ] Unify the interfaces

- Make sure that all the git and gh related invoke have the same parameters
  named in the same way
  - E.g., add --repo-short-name and --dry-run

### [ ] 
- Make sure they have all the same format <object>_<action>

### [ ] Improve git_branch_next_name

- `invoke git_branch_next_name` does not return the expected name for an issue-based
  branch
  - Without `--branch-name`, it computes the next name from the current
    branch instead of the target task
    ```bash
    > invoke git_branch_next_name
    ...
    branch_next_name='gp_scratch_37_1'
    ```
  - With `--branch-name HelpersTask1331_Implement_TODOs`, it works via the
    GitHub API and finds the correct next free suffix
    ```bash
    > invoke git_branch_next_name --branch-name HelpersTask1331_Implement_TODOs
    ...
    branch_next_name='HelpersTask1331_Implement_TODOs_2'
    ```


### [ ] Improve git_branch_create
- Implement create the next stacked sub-branch for the issue
  ```bash
  > invoke git_branch_create --issue-id 1331 --suffix 1
  ```

- Check that Re-running the command for a suffix that already
  exists fails instead of finding the next free one
  ```text
  Branch 'HelpersTask1331_Implement_TODOs_1' already exists
  ```

- Add an option to detect the next branch name
- Factor out this code across invokes
