---
description: Removes or reduces mocking in unit tests by redesigning for testability. Use when tests over-mock internal code, when the user wants to reduce test fragility from mocks, or when a test is difficult to maintain due to excessive patching. When mocking IS appropriate, see `@.claude/skills/testing.mocking/SKILL.md`.
---

# Step 1: Diagnose
- Read the test file and list every mock (`@umock.patch`, `umock.Mock()`,
  `umock.MagicMock()`)
- For each mock, classify it:
  - **External** (3rd-party library, AWS/S3, database, GitHub API) → keep; see
    `@.claude/skills/testing.mocking/SKILL.md` for the correct pattern
  - **Internal** (code inside this repo) → refactor using the strategies below
- Only proceed with the strategies below for mocks classified as **internal**

# Goal
- Apply the following transformations to remove internal mocking from unit
  testing code without changing observable behavior
- Mocking internal code often signals that your design could be more modular
  - Avoiding mocking in Python unit tests means designing code so dependencies
    are easy to control naturally, rather than being intercepted artificially

- Avoid internal mocking using the strategies below

## Prefer Pure Functions
- Functions that depend only on inputs and return outputs are trivial to test
  - **Example:**
    ```python
    def add(a: int, b: int) -> int:
        return a + b
    ```
- No mocking needed because there are no external dependencies

## Allow to Disable Assertion
- Pass a parameter `skip_dassert_exists` (default `False`) to skip checking
  `dassert_file_exists` and `dassert_dir_exists`

## Design for Dependency Injection (DI)
- Instead of hard coding dependencies inside functions or classes, pass them in
- **Bad approach:**
  ```python
  from typing import Any
  import requests

  def get_user(user_id: int) -> Any:
    return requests.get(f"https://api.com/users/{user_id}").json()
  ```
- **Good approach:**
  ```python
  from typing import Any, Protocol

  class HttpClient(Protocol):
      def get(self, url: str) -> Any: ...

  def get_user(user_id: int, http_client: HttpClient) -> Any:
    return http_client.get(f"https://api.com/users/{user_id}").json()
  ```
- **Bad approach:**
  ```python
  class Database: pass

  class UserService:
    def __init__(self) -> None:
      self.db: Database = Database()
  ```
- **Good approach:**
  ```python
  class Database: pass

  class UserService:
    def __init__(self, db: Database) -> None:
      self.db: Database = db
  ```

## Create Lightweight Fakes Instead of Mocks
- A fake is a real implementation with simplified behavior
  - More maintainable and less brittle than mocks
  - **Example:**
    ```python
    from typing import Any

    class FakeDatabase:
        def __init__(self) -> None:
            self.data: dict[str, Any] = {}

        def save(self, key: str, value: Any) -> None:
            self.data[key] = value

        def get(self, key: str) -> Any:
            return self.data.get(key)
    ```

## Separate Side Effects From Logic
- Keep core logic independent from I/O
- **Bad approach:**
  ```python
  from typing import Any

  def process_user(user_id: int) -> None:
      user: Any = db.get(user_id)
      send_email(user)
  ```
- **Good approach:**
  ```python
  from typing import Any, Callable

  def process_user(user: Any, send_email_fn: Callable[[Any], None]) -> None:
      send_email_fn(user)
  ```
- Now you can test logic without mocking the database or email system

## Test Behavior Via Public Interfaces
- Avoid testing internal calls (which often leads to mocking)
- Focus on outputs and state changes
  - Verify the final result or state instead of verifying a method was called

## Use Real Collaborators When Cheap
- If a dependency is fast and deterministic, just use it
  - JSON parsing
  - Simple utility classes
  - Pure transformations
- Mocking these adds unnecessary complexity

## Use Integration Tests Strategically
- Sometimes the best way to avoid mocking is not to unit test in isolation, but
  to test a small system working together

# Verify
- Run the refactored test file inside a Docker container to confirm all tests
  still pass:
  ```bash
  invoke docker_cmd --cmd "pytest <test_file> -v"
  ```
- Fix any failures before reporting done

# Important
- All invariants and conventions for unit tests are documented in
  `@.claude/skills/testing.rules.md`
- For mocking that remains necessary, follow
  `@.claude/skills/testing.mocking/SKILL.md`
- For all code you must follow the instructions in
  `@.claude/skills/coding.rules.md`
