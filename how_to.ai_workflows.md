# AI Workflows: Topics, Skills, and Rules
- This document explains the conventions and tools used to organize AI-assisted
  work via Claude Code in this repo (e.g., **topics**, **skills**, **rules**) and
  the command-line tools that operate on them (`mdm`, `lint_cc.py`, `rig`)

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
  files via `lint_cc.py --skill <TOPIC>.<ACTION>`
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

### `lint_cc.py`: Apply Rules/skills to Files Via Claude Code
- Detects file types, builds a prompt from the matching rules or skill, and
  invokes Claude Code on the selected files
- Select files with `--files`, `--from_file`, `--modified`, `--branch`,
  `--last_commit`, or `--all`
- Select what to apply with `--topic`, `--skill`, or `--rule`:
  ```bash
  # Apply the default rules for the file's topic (e.g., coding.rules.md)
  > lint_cc.py --files "file.py" --topic coding

  # Execute a specific skill on a file
  > lint_cc.py --files "file.py" --skill coding.fix_inline

  # Apply one specific rule section, identified three ways:
  # - Full path with header (validated against the file)
  > lint_cc.py --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions" --files "file.py"
  # - Line number only (extracts the section starting there)
  > lint_cc.py --rule ".claude/skills/coding.rules.md:58" --files "file.py"
  # - Keyword search (resolved to a unique rule via `rig --rule`)
  > lint_cc.py --rule "dassert" --files "file.py"
  ```
- Use `--dry_run` to print the command without executing it

### `rig`: Ripgrep Wrapper for Finding Rules, TODOs, and Definitions
- `rig <pattern> [<dir>] [<ext>] [--options]`, with mode flags that change the
  search target instead of the pattern:
  - `--rule`: search Markdown headers in `.claude/skills/*.rules.md` (used by
    `lint_cc.py --rule` to resolve a keyword to a specific rule section)
  - `--todo`: search for `TODO(ai_gp)`-style patterns
  - `--def`: search for Python `class`/`def` definitions
- `rigrule` is a shortcut for `rig --rule "$@"`
- `rigrulec` is the same, plus `--cfile` to capture results to a `cfile` and
  open them in vim with `:cfile cfile`

## Workflows

### Find and Apply a Specific Rule to a File
1. Locate the rule with `rigrule "<keyword>"` or by browsing
   `.claude/skills/<TOPIC>.rules.md`
2. Apply it with `lint_cc.py --rule "<keyword or path:line>" --files "<file>"`

### Lint Files by Topic Instead of a Single Rule
- Use `lint_cc.py --files "<files>" --topic <topic>` to apply the topic's full
  rules file, or `--modified` / `--branch` / `--last_commit` / `--all` instead
  of `--files` to select files by git state rather than by name

### Run a Skill on a File
- Use `lint_cc.py --files "<file>" --skill <topic>.<action>` to execute one
  skill (as opposed to a whole rules file) on a file

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
