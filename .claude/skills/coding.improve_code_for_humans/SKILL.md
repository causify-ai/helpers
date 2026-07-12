---
description: Make the code more readable and debuggable
model: haiku
---

# Goal
The user will pass you one of more files `<FILES>` and you will make the code
more readable and debuggable for humans.

# Workflow

## Add Comments
- Improve code readability by adding concise comments with these rules

- Add comments for every cohesive code block that is at least 3-5 lines long
  explaining what the code block does
  - **Bad** (different chunks of code without comments)
    ```
    num_passed = info.get("log_num_passed", 0) or 0
    num_failed = info.get("log_num_failed", 0) or 0
    duration = f"{info['pytest_duration_in_secs']}s"
    res = {
        "passed": num_passed,
        "failed": num_failed,
        "duration": duration,
    }
    ```
  - E.g., (add comments to chunks)
    ```
    # Extract info.
    num_passed = info.get("log_num_passed", 0) or 0
    num_failed = info.get("log_num_failed", 0) or 0
    duration = f"{info['pytest_duration_in_secs']}s"
    # Assemble result.
    res = {
        "passed": num_passed,
        "failed": num_failed,
        "duration": duration,
    }
    ```
- Add comments that explain _why_ rather than _what_
  - Add comments describing important invariants, assumptions, or guarantees
    maintained by the code
  - Keep all comments as short and precise as possible
  - Avoid obvious line-by-line comments
  - Do not restate the code in English

- If there are empty comments separating chunks of code, add a comment
  - **Bad** (empty comment)
    ```
    #
    stacktraces_file = hpytest.get_output_file_path(
        "stacktraces.txt", build_name=build_name
    )
    hpytest.write_test_stacktraces(info, stacktraces_file)
    _LOG.info("Created '%s'", stacktraces_file)
    ```
  - **Good**
    ```
    # Stacktraces.
    stacktraces_file = hpytest.get_output_file_path(
        "stacktraces.txt", build_name=build_name
    )
    hpytest.write_test_stacktraces(info, stacktraces_file)
    _LOG.info("Created '%s'", stacktraces_file)
    ```

- Do not remove any comment, only add new ones when needed

- Follow the rules in `.claude/skills/coding.rules.md` `# Comments`

## Add Functions to Track Entering in a Function
- For free-standing functions and class methods add at the beginning:
  - `_LOG.debug(hprint.to_str("a b c"))` with the variables that are most
    important and not too big to print (e.g., large text, dictionary and so on)
- Use parameter names (omit `self` for methods)

## Add `_LOG.debug` to Track the Execution in a Function
- Use `_LOG.debug` to add debugging info in functions that can help a programmer
  to track the issues and execution

## Add `_LOG.debug` to Track the Resulting Values of a Function
- Refactor code to avoid more than one `return` statement when possible
- Instrument the code to print the exit value of a function
  ```python
  _LOG.debug("return=%s", ...)
  ```

## Conventions
- Use `_LOG.debug(hprint.to_str("a b c")` when possible

- Do not print large object, e.g.,
  - If there is an array of objects print only the first element
  - If there is a dictionary print only the first key

- Do not change the behavior of the code in any way

- You must follow the rules in `.claude/skills/coding.rules.md`
