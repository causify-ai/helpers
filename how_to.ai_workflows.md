# AI Workflows: Topics, Skills, and Rules
- This document explains the conventions and tools used to organize AI-assisted
  work via Claude Code in this repo (e.g., **topics**, **skills**, **rules**) and
  the command-line tools that operate on them (`mdm`, `cc_lint.py`, `rig`)

- See `.claude/skills/skill.rules.md` for the full authoring conventions

## Definitions

### Topics
- A **topic** is a category that groups related skills and conventions (e.g.,
  `coding`, `testing`, `markdown`, `notebook`)
- Topics organize skills semantically; each topic may have a corresponding
  `.claude/skills/<TOPIC>.rules.md` file documenting its conventions
- List all topics with:
  ```bash
  > find .claude/skills -name "*.md" | sed 's|.claude/skills/||; s|\..*||' | sort | uniq
  ```
- Current topics include:
  - `architecture`: Architecture and design documentation
  - `auto_task`: Automated task definitions and workflows
  - `bash`: Bash scripting and shell commands
  - `blog`: Blog post creation and formatting
  - `cfile`: vim cfile conventions
  - `coding`: Python code style and conventions
  - `latex`: LaTeX document processing
  - `markdown`: Markdown formatting and structure
  - `notebook`: Jupyter notebook conventions
  - `pytest`: Testing framework and patterns
  - `readme`: README file creation and updates
  - `slides`: Presentation slide creation
  - `svg`: SVG graphics handling
  - `text`: General text and writing conventions
  - `tikz`: TikZ diagram creation
  - `tool_X_in_60_mins`: Tool tutorials and guides
  - `visuals`: Visual design and graphics

### Skills
- A **skill** is a specific, actionable task organized under a topic (e.g.,
  `coding.fix_comments`, `testing.write_unit_tests`)
- Each skill lives in `.claude/skills/<TOPIC>.<ACTION>/SKILL.md` and contains
  step-by-step instructions, examples, and verification steps
- Skills are invoked directly (e.g., `/coding.fix_comments`) or executed on
  files via `cc_lint.py --skill <TOPIC>.<ACTION>`
- See `.claude/skills/skill.rules.md` for the required frontmatter, naming
  convention, and content structure (`Goal`, `Workflow`, `Conventions`,
  `Constraints`, `Examples`, `Verification`)

### Rules
- A **rule file** (`.claude/skills/<TOPIC>.rules.md`) documents the conventions
  and standards for a topic:
  - Naming conventions and patterns
  - Code/content style guidelines
  - Decision criteria for consistency
  - Examples of good and bad practices
- Skills reference their topic's rule file to avoid duplicating conventions
  across related tasks
- `.claude/rules.md` is the top-level map from file type (e.g., `.py`, `.ipynb`,
  `.md`) to the rule file and template that apply to it; when operating on a
  file, read `.claude/rules.md` first to find which rules and templates to
  follow

### Templates
- A **template** (`.claude/templates/*.template.<ext>`) is a starting-point
  file to copy from when creating a new file of a given kind: it fixes the
  boilerplate (headers, imports, section markers, placeholders) so new content
  follows the same shape as existing content
- Unlike rules (conventions to check against) and skills (steps to execute),
  templates are files to instantiate directly
- `.claude/rules.md` pairs each file type with its template, e.g.:
  - `.claude/templates/coding.template.py` for `.py` files
  - `.claude/templates/testing.template.py` for `test_*.py` files
  - `.claude/templates/notebook.template.ipynb` for `.ipynb` files
  - `.claude/templates/readme.template.md` for `README.md` files
- Other templates cover specific artifacts referenced by individual skills
  rather than a whole file type, e.g. `architecture_doc.template.md`,
  `slides.template.md`, `github_PR_plan.template.md`, `book_map.template.md`,
  `graphviz.template.md`, `tikz.template.md`, `typst.template.typ`
- Placeholders inside a template use the `<VAR>` notation (e.g., `<Directory
  Name>`) per `.claude/skills/skill.rules.md`; fill them in and remove any
  optional sections that don't apply

## Tools

### `mdm`: Unified Markdown Content Manager
- `mdm` manages skills, blog posts, research ideas, and short stories across
  repositories with one consistent interface:
  `mdm <type> <action> [name_filter]`
- Full reference: `dev_scripts_helpers/system_tools/mdm.README.md`
- Common commands:
  ```bash
  > mdm skill list                     # List all skill names
  > mdm skill full_list                # List all skills with full paths
  > mdm skill describe blog.add_figures # Show a skill's frontmatter description
  > mdm skill edit coding.new_action   # Open (or scaffold) a skill in vim
  > mdm skill directory                # Print the path to .claude/skills
  > mdm skill types                    # List unique topic prefixes
  ```
- Type (`skill`, `blog`, `research`, `story`) and action (`list`, `full_list`,
  `describe`, `edit`, `directory`, `types`) both support prefix matching, so
  `mdm sk l` is equivalent to `mdm skill list`

### `cc_lint.py`: Apply Rules/skills to Files Via Claude Code
- Detects file types, builds a prompt from the matching rules or skill, and
  invokes Claude Code on the selected files
- Select files with `--files`, `--from_file`, `--modified`, `--branch`,
  `--last_commit`, or `--all_files`
- Select what to apply with `--topic`, `--skill`, or `--rule`
- `--mode` is required (no default): pick `one_shot_with_cc`, `one_shot`,
  `session`, or `stateless`
  ```bash
  # Apply the default rules for the file's topic (e.g., coding.rules.md)
  > cc_lint.py --files "file.py" --topic coding --mode one_shot_with_cc

  # Execute a specific skill on a file
  > cc_lint.py --files "file.py" --skill coding.fix_inline --mode one_shot_with_cc

  # Apply one specific rule section, identified three ways:
  # - Full path with header (validated against the file)
  > cc_lint.py --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions" --files "file.py" --mode one_shot_with_cc
  # - Line number only (extracts the section starting there)
  > cc_lint.py --rule ".claude/skills/coding.rules.md:58" --files "file.py" --mode one_shot_with_cc
  # - Keyword search (resolved to a unique rule via `rig --rule`)
  > cc_lint.py --rule "dassert" --files "file.py" --mode one_shot_with_cc
  ```
- Use `--dry_run` to print the command without executing it

### `rig`: Ripgrep Wrapper for Finding Rules, TODOs, and Definitions
- `rig <pattern> [<dir>] [<ext>] [--options]`, with mode flags that change the
  search target instead of the pattern:
  - `--rule`: search Markdown headers in `.claude/skills/*.rules.md` (used by
    `cc_lint.py --rule` to resolve a keyword to a specific rule section)
  - `--todo`: search for `TODO(ai_gp)`-style patterns
  - `--def`: search for Python `class`/`def` definitions
- `rigrule` is a shortcut for `rig --rule "$@"`
- `rigrulec` is the same, plus `--cfile` to capture results to a `cfile` and
  open them in vim with `:cfile cfile`

## Workflows

### Find and Apply a Specific Rule to a File
1. Locate the rule with `rigrule "<keyword>"` or by browsing
   `.claude/skills/<TOPIC>.rules.md`
2. Apply it with `cc_lint.py --rule "<keyword or path:line>" --files "<file>" --mode one_shot_with_cc`

### Lint Files by Topic Instead of a Single Rule
- Use `cc_lint.py --files "<files>" --topic <topic> --mode one_shot_with_cc`
  to apply the topic's full rules file, or `--modified` / `--branch` /
  `--last_commit` / `--all_files` instead of `--files` to select files by git
  state rather than by name

### Run a Skill on a File
- Use `cc_lint.py --files "<file>" --skill <topic>.<action> --mode one_shot_with_cc`
  to execute one skill (as opposed to a whole rules file) on a file

### Create or Browse a Skill
1. `mdm skill list` (or `mdm skill list <pattern>`) to see what already exists
2. `mdm skill edit <topic>.<action>` to open the skill, or scaffold a new one if
   it doesn't exist yet
3. Follow `.claude/skills/skill.rules.md` for frontmatter, structure, and
   naming; add or update the topic's `.claude/skills/<topic>.rules.md` if the
   skill introduces a new convention

### Add or Update a Rule
1. Decide rule vs. skill per `.claude/skills/skill.rules.md` ("Rules vs
   Skills"): rules capture conventions and decision criteria that apply across
   tasks; skills capture a single step-by-step task
2. Edit `.claude/skills/<TOPIC>.rules.md`, keeping related rules grouped under
   `#` sections with `##` sub-rules
3. Verify the rule is discoverable: `rigrule "<keyword>"` should resolve to it
   uniquely

### Start a New File From a Template
1. Look up the file type in `.claude/rules.md` to find its template (e.g.,
   `.py` -> `.claude/templates/coding.template.py`)
2. Copy the template to the new file's path and fill in the `<VAR>`
   placeholders
3. Apply the corresponding rules with `cc_lint.py --files "<file>" --topic
   <topic> --mode one_shot_with_cc` to check the new file follows conventions
   the template doesn't already encode (e.g., naming, docstring content)
