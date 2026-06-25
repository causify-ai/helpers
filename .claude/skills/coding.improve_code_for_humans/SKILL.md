---
description: Make the code more readable and debuggable
model: haiku
---

- I will pass you one of more files `<FILES>`

# Goal

## Add Comments
- Improve its readability by adding concise comments with these rules

- Add comments for every cohesive code block that is at least 5 lines long
  explaining what the code block does
- Add comments describing important invariants, assumptions, or guarantees
  maintained by the code
- Add comments that explain _why_ rather than _what_
  - Keep all comments as short and precise as possible
  - Avoid obvious line-by-line comments
  - Do not restate the code in English
- Do not remove any comment, only add new ones when needed
- Follow the rules in `.claude/skills/coding.rules.md` `# Comments`

## Add Functions to Track Entering in a Function
- For each function add at the beginning either
  - `_LOG.debug(hprint.func_signature_to_str())` or
  - `_LOG.debug(hprint.to_str("a b c")`
     with the variables that are most important and not too big to print (e.g.,
     large text, dictionary and so on)

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

- Follow the rules in `.claude/skills/coding.rules.md`
