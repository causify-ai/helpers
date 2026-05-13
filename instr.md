Add a phase in lint_txt.py to convert ` - ` as separators into `: `

- E.g., convert
1. **Summary** - One paragraph describing the directory's purpose
2. **Structure of the Dir** - List subdirectories and their roles
3. **Description of Files** - Alphabetical list of all files with 1-2 line descriptions
4. **Description of Executables** - Detailed docs for each script/tool

into

1. **Summary**: One paragraph describing the directory's purpose
2. **Structure of the Dir**: List subdirectories and their roles
3. **Description of Files**: Alphabetical list of all files with 1-2 line descriptions
4. **Description of Executables**: Detailed docs for each script/tool

- Convert
  ```
  - Format: `- <filename>` - description (1-2 lines max)
  ```
  into
  ```
  - Format: `- <filename>`: description (1-2 lines max)
  ```

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- When writing code you must always follow the instructions in
  `@.claude/skills/coding.rules.md`

- Generate unit tests for the new code following the instructions in
  `@.claude/skills/testing.rules.md`
