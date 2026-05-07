---
description: Reference rules for test design principles, test data guidelines, and test code hygiene. Load when deciding how to structure tests, choose test data, or evaluate test quality.
---

- This file contains test design principles, data rules, and code hygiene rules

# Test Design Principles

## Test One Thing
- A test class tests only one function or class
- A test method tests only one case (e.g., "for these inputs the function
  returns this output")
- Keeps each test simple and isolates the root cause when it fails

## Keep Tests Self-contained
- Each test must be independent — never assume execution order
- Include all information needed to understand the test within the test itself:
  specify input data explicitly rather than referencing shared state
- If multiple tests use the same data, repeat it in each or factor it into a
  builder helper rather than relying on shared mutable state

## Only Specify Data Related to What Is Being Tested
- Use the minimum data required — omit optional arguments that are not part of
  the case being tested

## Test Executable Scripts End-to-end
- A single end-to-end smoke test with all arguments present also validates the
  argument parser, saving coverage effort
- Factor logic out of `_main()` into a `_run()` function; test `_run()` directly

## Test From the Outside-in
- Start with public-facing methods and end-to-end behaviors before adding tests
  for internal helpers
- Interface-level tests survive refactoring; implementation-level tests do not

# Test Data Rules

## Use Text Files, Not Pickle Files
- Pickle files break across library version changes and are not human-readable
- Use CSV or plain text files; document how test data was generated or add a
  test that generates it

## Keep Test Data Small
- Use the smallest dataset that exercises the case: faster, easier to debug,
  more targeted
- Never check in fixtures larger than a few kilobytes

# Test Code Hygiene

## Keep Testing Code in Sync with Tested Code
- When renaming a tested class or file, rename the test class and test file at
  the same time

## Test Code Is Not Second-class Citizen
- Apply the same quality standards to test code as to production code: comments,
  docstrings, DRY helpers, no copy-paste
