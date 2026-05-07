---
description: Writes new Python unit tests or updates existing test files. Use when the user asks to write tests, add test coverage, create a test file, or improve existing tests for a module or function.
---

- You are an expert Python developer

## Step 1: Understand the Target
- Read the target file and identify:
  - All public methods and functions to test
  - External dependencies that need mocking
  - Happy path, edge cases, and error conditions per `@.claude/skills/testing.rules.md`

## Step 2: Write Tests
- Follow all conventions in `@.claude/skills/testing.rules.md`
- Use project test infrastructure (dirs, golden files, test-mode utilities) from
  `@.claude/skills/testing.rules.md`
- Apply design principles from `@.claude/skills/testing.design/SKILL.md`
- Classify each test by expected duration using
  `@.claude/skills/testing.speed/SKILL.md`
- For external dependencies (AWS, databases, 3rd-party APIs), follow
  `@.claude/skills/testing.mocking/SKILL.md`

## Step 3: Verify
- Run the tests to confirm they pass:
  ```bash
  invoke docker_cmd --cmd "pytest <test_file> -v"
  ```

## Important
- If the target file or scope is unclear, ask before writing any tests
- For all Python code follow `@.claude/skills/coding.rules.md`
