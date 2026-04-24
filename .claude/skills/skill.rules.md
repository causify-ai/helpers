- This document contains conventions and rules to create agentic skills.

# Overview and Topics

## Skill Topics

- All skills should refer to a specific "topic"

- You can find the topics running a command like
  ```
  > find .claude/skills -name "*.md" | sed 's|.claude/skills/||; s|\..*||' | sort | uniq
  ```

- Example of topics
  ```
  bash
  blog
  book
  coding
  coding_qa
  cxo_slides
  demo
  docker
  git
  github
  graphviz
  gws
  markdown
  notebook
  paper
  readme
  skill
  slides
  testing
  text
  tikz
  tutorials
  X_in_60_min
  ```

# SKILL.md File Format

## Frontmatter

- Every SKILL.md file must start with YAML frontmatter:
  ```yaml
  ---
  description: Brief action-oriented description of what the skill does
  model: haiku
  ---
  ```

- **Guidelines for description**:
  - Use imperative verb: "Format Python code", "Write unit tests", "Create slides"
  - Keep it under 80 characters
  - Be specific about what transformation or task the skill performs
  - Example: `description: Format Python code according to project coding conventions and style rules`

## Directory Structure

- Skills are organized in directories: `.claude/skills/<topic>.<action>/SKILL.md`
  - **Good**
    - `coding.format/SKILL.md`
    - `testing.format/SKILL.md`
    - `notebook.format/SKILL.md`

- Each skill directory may contain:
  - `SKILL.md`: Main skill instruction file
  - Supporting directories or files (e.g., templates, examples)

## Skill Rule File
- For the passed skill file `<SKILL_FILE>` in the format
  ```
  .claude/skills/<topic>.<action>/SKILL.md
  ```
  there should be a corresponding rule file `<RULE_FILE>`
  ```
  .claude/skills/<topic>.rules.md
  ```
  - E.g., for a skill file `.claude/skills/coding.fix_comments/SKILL.md` the
    corresponding rule file is `.claude/skills/coding.rules.md`

## Naming Conventions

- Directory naming: `<topic>.<action>`
  - E.g.,
    - `coding.format`: Format code for the coding topic
    - `testing.format`: Format tests for the testing topic
    - `notebook.interactive_cell.format`: Format interactive cells in notebooks
    - `demo.create_script`: Create a demo script

- Topics should be singular and lowercase

## Content Structure

Skills should be organized with clear sections:

1. **Frontmatter**: YAML description
2. **Introduction**: 1-2 sentences describing what the skill does
3. **Main Sections**: Organized by topic area or workflow step
4. **Examples**: Good/Bad patterns and concrete examples
5. **Scope/Limitations** (if applicable): What the skill covers or doesn't cover

- Use headers from `## ` down (skip `#` for section titles)
- Keep sections focused and actionable

# Writing Conventions

## Writing Rules
- Use imperative language ("Do X")
- Avoid vague words (properly, nicely, appropriately, etc.)
- Prefer measurable criteria
- Keep formatting consistent across skills

## Add examples
- Skills should contain positive and negative examples
  ````
  - **Good**
    ```
    ...
    ```
  - **Bad**
    ```
    ...
    ```
  ````
- Use realistic, concrete cases

## File References

- Enclose files into backticks with `@` prefix:
  - **Bad**
    ```
    A file looks like `@.claude/skills/markdown.format/SKILL.md`
    ```
  - **Good**
    ```
    A file looks like `@.claude/skills/markdown.format/SKILL.md`
    ```

## Variable Notation

- Variables should be referred as `<var>` and not `$var`
  - **Bad**
    ```
    The variable $files ...
    ```
  - **Good**
    ```
    The variable `<files>` ...
    ```

## Code Examples

- Use "Good" and "Bad" patterns to illustrate conventions
- Format examples consistently:
  ```
  - **Bad** (explain why)
    ```language
    code here
    ```
  - **Good** (explain why)
    ```language
    code here
    ```
  ```

- Provide reasoning for each example to help users understand the principle

## Language and Tone

- Use direct, imperative language:
  - Good: "Format Python code according to...", "Create a test class that..."
  - Bad: "Formatting Python code...", "You should create..."

- Assume the reader is executing the skill or following the instructions
- Be prescriptive rather than descriptive

## Markdown Standards

- Make sure the file follows the markdown conventions in
  `@.claude/skills/markdown.rules.md`

# References and Dependencies

## Rules Files

- Each topic might have a "rules" file, in the format `<topic>.rules.md` that
  contains all the convention for that specific topic

## Referencing Rules Files

- Skills should defer to topic-specific rules files for conventions
- Always reference the rules file at the top when applicable:
  ```
  - Format Python code according to the rules in `@.claude/skills/coding.rules.md`
  ```

- If no rules file exists for a topic, create one before adding multiple skills
  in that topic

## Cross-Referencing Skills

- When a skill depends on understanding from another skill, reference it:
  ```
  - Follow the coding style conventions described in `@.claude/skills/coding.format/SKILL.md`
  ```

- Use backticks and full path with `@` prefix for clarity

## File Validation

- All file references in skills must point to existing files
- Paths should be verifiable: `@.claude/skills/<topic>.<action>/SKILL.md`
- If you reference a template or example, verify it exists:
  ```bash
  > find .claude -name "code_template.py" -o -name "*_template.*"
  ```

- All references in the skills should be to existing files
- If there is a non-existing reference try to find it

# Guidelines and Decisions

## Rules vs Skills

- Create/update `<RULE_FILE>` `<topic>.rules.md` when documenting:
  - Conventions and standards for a topic
  - Principles that apply across multiple related tasks
  - Decision criteria for formatting or style

- Create/update `<SKILL_FILE>` `<topic>.<action>/SKILL.md` when documenting:
  - A specific transformation or task
  - Step-by-step instructions for a particular action
  - Implementation guidance for achieving a specific output

## Keep Rules organized in the Rule File
- In the `<RULE_FILE>` `<topic>.rules.md` keep group related rules (with header
  of level 2 ##) into logical sections (with header of level 1 #)
  ```
  # <Group 1>

  ## <Rule 1.1>

  ## <Rule 1.2>

  ...

  # <Group 2>
  ```

# Quality Checklist

## Skill Validation

When creating a new SKILL.md file, verify:

- [ ] **Frontmatter**: Contains YAML with action-oriented description
- [ ] **File References**: All paths enclosed in backticks with `@` prefix
- [ ] **Variables**: All variables use angle brackets `<var>` notation
- [ ] **Examples**: Include both "Good" and "Bad" patterns with explanations
- [ ] **Rules Reference**: Links to applicable `<topic>.rules.md` file if it exists
- [ ] **Markdown**: Follows conventions in `@.claude/skills/markdown.rules.md`
- [ ] **Language**: Uses imperative, direct tone
- [ ] **Headers**: Uses `##` and below (no single `#`)
- [ ] **Cross-References**: Links to related skills where applicable
- [ ] **File Existence**: Verify all referenced files actually exist
