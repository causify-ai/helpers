---
description: Remove mocking approach from unit tests
---

- When the user passes a test file, apply the following transformations to remove
  using mocking in unit testing code, making sure that there is no change in
  behavior

- Mocking is often a sign your design could be more modular
  - Avoiding mocking in Python unit tests is mostly about designing your code so
    that dependencies are easy to control naturally, rather than being
    intercepted artificially

- Avoid to use mock using the following strategies

# Prefer Pure Functions

- Functions that depend only on inputs and return outputs are trivial to test
  - **Good**
    ```
    def add(a, b):
        return a + b
    ```

- No mocking needed because there are no external dependencies

# Allow to Disable Assertion

- Passing a parameter `skip_dassert_exists` set by default to False to skip
  checking `dassert_file_exists` and `dassert_dir_exists`

# Design for Dependency Injection (DI)

- Instead of hard coding dependencies inside your functions or classes, pass them
  in
- **Bad**
  ```
  import requests

  def get_user(user_id):
    return requests.get(f"https://api.com/users/{user_id}").json()
  ```
- **Good**
  ```
  def get_user(user_id, http_client):
    return http_client.get(f"https://api.com/users/{user_id}").json()
  ```
- **Bad**
  ```
  class UserService:
    def __init__(self):
      self.db = Database()
  ```
- **Good**
  ```
  class UserService:
    def __init__(self, db):
      self.db = db
  ```

# Create lightweight fakes instead of mocks

- A fake is a real implementation with simplified behavior.
  - This is often more maintainable and less brittle than mocks.
  - E.g.,
    ```
    class FakeDatabase:
        def __init__(self):
            self.data = {}

        def save(self, key, value):
            self.data[key] = value

        def get(self, key):
            return self.data.get(key)
    ```

# Separate side effects from logic

- Keep core logic independent from I/O.
  - **Bad**
    ```
    def process_user(user_id):
        user = db.get(user_id)
        send_email(user)
    ```
  - **Good**
    ```
    def process_user(user, send_email_fn):
        send_email_fn(user)
    ```

- Now you can test logic without mocking the database or email system

# Test behavior via public interfaces

- Avoid testing internal calls (which often leads to mocking). Focus on outputs
  and state changes.
  - Instead of verifying a method was called, prefer verifying the final result
    or state

# Use real collaborators when cheap

- If a dependency is fast and deterministic, just use it.
  - E.g.,
    - JSON parsing
    - Simple utility classes
    - Pure transformations

- Mocking these adds unnecessary complexity.

# Use integration tests strategically

- Sometimes the best way to avoid mocking is not to unit test in isolation, but
  to test a small system working together

# Important

- All invariants and conventions for unit tests are documented in
  `@.claude/skills/testing.rules.md`
- For all the code you must follow the instructions in
  `@.claude/skills/coding.rules.md`
