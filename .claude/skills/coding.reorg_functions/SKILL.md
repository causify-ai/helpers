---
description: Reorganize the Python functions in a file
---

# Reorganize Python Functions Within a File

Reorganize the Python functions in the user-provided file according to the
following rules.

## Organize functions into logical layers

- Group related functions into sections separated by headers in the following format:
  ```python
  # #############################################################################
  # <Layer Description>
  # #############################################################################
  ```

- Examples of layers:
  - Constants / configuration
  - Low-level utility functions
  - Parsing helpers
  - Data transformation helpers
  - Core business logic
  - Public API functions
  - CLI / entry points

## Order layers by abstraction level

- Arrange layers from lower-level/simple functionality to higher-level/complex
  functionality

- General rule:
  - Fundamental utilities first
  - High-level orchestration last

## Order functions within each layer

- Inside each layer, organize functions from:
  - More primitive / reusable
  - To more specialized / higher-level

- Functions should generally appear before functions that depend on them.

## Mark file-private functions as private

- Rename functions that are only used internally within the file to use a leading
  underscore
  - Example:
    ```python
    def foo_bar(...):
    ```

    becomes:

    ```python
    def _foo_bar(...):
    ```

- Only do this for functions that are not part of the module's public interface

## Keep Related Functions Together
- Keep related helper functions physically close together
  - E.g., if there is a public or private function used only in one place in a
    file, move that function close to where it is used

## Additional Guidance

- Avoid circular ordering where possible
- Preserve existing comments and docstrings
- Keep public entry points easy to locate near the end of the file
- Prefer cohesion and readability over strict categorization

# Constraints

## Preserve behavior exactly

- Do not modify functionality, logic, signatures, control flow, side effects, or semantics
- The resulting code must behave identically to the original.

## Move code only

- The refactor must be structural only.
  Allowed changes:

  - Reordering functions
  - Adding section headers
  - Renaming internal/private functions consistently

- Disallowed changes:
  - Rewriting logic
  - Simplifying implementations
  - Changing APIs
  - Changing imports unnecessarily
  - Modifying formatting beyond what is required for reorganization
