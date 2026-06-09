---
description: Check the references in all the skill files
model: haiku
---

# Goal
- Check that all the skill and rule files have references

# Step 1: Find Files
- Look for all the markdown files both `SKILL.md` and `<TOPIC>.rules.md`
  ```
  > find .claude/skills -name "*.md"
  ```

# Step 2: Read Context
- Read context about rules from `.claude/skills/skill.rules.md`

# Step 3: Check Rules
- For each file apply all the following rules and report violations as described
  below

## Check File Exists
- Make sure the referred file links exists
  - E.g., 
    ```
    - For all the code you must follow the instructions in
      - `.claude/skills/coding.rules.md`
      - `.claude/skills/testing.rules.md`
    ```
    the files `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md`
    must exist
- If not report as a violation as described later

## Check that Frontmatter is Correct
- Make sure that each `<SKILL.md>` file has a description and a model in the
  YAML frontmatter
  - **Bad**
    ```
    ---
    description: Check the references in all the skill files
    ---
    ```
  - **Good**
    ```
    ---
    description: Check the references in all the skill files
    model: haiku
    ---
    ```
- If not report as a violation as described later

## Check Header References
- When there are references to files and specific headers make sure they exist
  - E.g., 
    ```
    - Write comments using the style from `.claude/skills/coding.rules.md`
      `# Documentation and Comments`
    ```
    you can run
    ```
    > grep -q '^# Documentation and Comments$' .claude/skills/coding.rules.md
    ```
- If not report as a violation as described later

## Check for Other Violations
- Use the rules in `.claude/skills/skill.rules.md` to look for clear violations
- Report them only if you are really sure about it

# Step 4: Report Violations

- Report all the violations in a file `cfile` using the format
  `.claude/skills/cfile.rules.md`

# Step 5: Ask Users Whether to Fix the Problems
- Ask for the user which problems should be fixed by printing a list of problem
  with indices
