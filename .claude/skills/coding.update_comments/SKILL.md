---
description: Update docstrings, comments, and assertions in a Python file to be in sync with the code without changing logic
---

Given the passed Python file

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

- Add docstrings to functions and file that are missing

- Update and clarify the comments that are not in sync with the code, explaining
  the logic (why) rather than what is done (what and how)
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

- You must not change the actual intention or behavior of the Python code
- For all the code you must follow the instructions in
  `@.claude/skills/coding.rules.md`
