---
description: Update docstrings, comments, and assertions in a Python file to be in sync with the code without changing logic
---

Given the passed Python file

# Docstrings

- Update the docstring to functions and file that are not in sync with the code
  - **Bad**:
  ```python
  def calculate_total(items):
      """Calculate something."""
      return sum(item.price for item in items if item.active)
  ```
  - **Good**
  ```python
  def calculate_total(items):
      """Calculate sum of prices for all active items.
      
      :param items: List of Item objects with price and active attributes
      :return: Total price as float
      """
      return sum(item.price for item in items if item.active)
  ```

- Make sure all the functions have a REST comments in docstrings
  - Add docstrings to functions and file that are missing

# Comments

- Update and clarify the comments that are not in sync with the code, explaining
  the logic ("why") rather than what is done ("what" and "how")
  - **Bad** (redundant/obvious)
    ```python
    # Loop through each user.
    for user in users:
        # Add one to the counter.
        count += 1
    ```
  - **Good**
    ```python
    # Prioritize active users first, then sort by registration date for fairness.
    users_sorted = sorted(users, key=lambda u: (not u.active, u.registered_at))
    ```

- Use periods at the end of all comments

- Make sure that there are comments in large chunks of code explaining the "why"
  of each chunk of code

- Do not use empty lines within functions but use comments to separate chunks of
  code

# Leave Existing Comments Untouched

- Leave untouched comments that represent examples of input-output relationships
  - E.g.,
    ```python
    # Transform:
    #   ('a2bfc704', ['head_hash', 'remh_hash'])
    # into
    #   'head_hash = remh_hash = a2bfc704'
    ```

- Leave comments that represent running a command and getting a result
  - E.g.,
    ```python
    # > git config --file /Users/saggese/src/.../.gitmodules --get-regexp path
    # submodule.amp.path amp
    ```

# Assertions
- For each `dassert_*()` assertion make sure there is a message explaining why
  the assertion is important
  - **Bad**
    ```python
    hdbg.dassert(len(results) > 0)
    ```
  - **Good**
    ```python
    hdbg.dassert(len(results) > 0, "Query must return at least one result")
    ```
  - **Bad**
    ```python
    hdbg.dassert_eq(len(results), expected_len, "error")
    ```
  - **Good**
    ```python
    hdbg.dassert_eq(len(results), expected_len, 
                f"Expected number of results doesn't match the passed one")
    ```

- When adding a comment try to not repeat information already present in the
  assertion
  - **Bad** since `dassert_in()` will already print the valid values
    ```python
    hdbg.dassert_in(
      method,
      ["auto", "github_api", "linear_scan"],
      f"Invalid method '{method}'; must be one of: auto, github_api, linear_scan",
    )
    ```
  - **Good**
    ```python
    hdbg.dassert_in(
      method,
      ["auto", "github_api", "linear_scan"],
      "Invalid method specified"
    )
    ```

- When adding a comment do not use the f-string formatting, but use the
  printf-style string formatting
  - **Bad**
    ```python
    hdbg.dassert(
        branch.startswith(prefix),
        f"Remote branch '{branch}' must start with '{prefix}' prefix",
    )
    ```
  - **Good**
    ```python
    hdbg.dassert(
      branch.startswith(prefix),
        "Remote branch '%s' needs to start with '%s'",
        branch,
        prefix,
    )
    ```

# Constraints
- You must not change the actual intention or behavior of the Python code
- For all the code you must follow the instructions in
  `@.claude/skills/coding.rules.md`
