<!-- toc -->

- [AI Tools Onboarding](#ai-tools-onboarding)
  * [Overview](#overview)
  * [Claude Code Skills System](#claude-code-skills-system)
    + [Invoking a Skill](#invoking-a-skill)
    + [Directory Structure](#directory-structure)
    + [Rules Files](#rules-files)
    + [Writing a New Skill](#writing-a-new-skill)
    + [SKILL.md Format](#skillmd-format)
    + [Design Rationale](#design-rationale)
    + [Tradeoffs and Alternatives](#tradeoffs-and-alternatives)
  * [`mdm`: Markdown Document Manager](#mdm-markdown-document-manager)
    + [The Problem `mdm` Solves](#the-problem-mdm-solves)
    + [Content Types Managed](#content-types-managed)
    + [Core Actions](#core-actions)
    + [Key Commands](#key-commands)
    + [Prefix Matching](#prefix-matching)
  * [`rig`: Ripgrep Shortcuts](#rig-ripgrep-shortcuts)
    + [Why Ripgrep?](#why-ripgrep)
    + [Basic Ripgrep Usage](#basic-ripgrep-usage)
    + [`rig`: Team Wrapper Around Ripgrep](#rig-team-wrapper-around-ripgrep)
    + [`rig` Shortcuts](#rig-shortcuts)
    + [Vim Integration](#vim-integration)
    + [Practical Ripgrep Patterns](#practical-ripgrep-patterns)

<!-- tocstop -->

# AI Tools Onboarding

## Overview
AI coding assistants like Claude Code are stateless — every conversation starts
from zero. Without a system, each developer re-explains the same conventions
differently, and Claude interprets each phrasing differently, producing
inconsistent output

The team has built a layer of tooling on top of Claude Code to solve this:

- **Skills**: markdown files that encode exactly how to do one task, invoked
  with a single slash command
- **Rules files**: the team's conventions, written once and referenced by many
  skills
- **Templates**: reference implementations that rules and skills point to
- **mdm**: a unified CLI for managing skills, rules, blog posts, and research
  notes
- **rig**: a ripgrep wrapper with smart shortcuts for navigating code and skills

## Claude Code Skills System
Skills live in `.claude/skills/` as `<topic>.<action>/SKILL.md`. Each skill
encodes one specific task and references its topic's rules file for conventions

### Invoking a Skill
Open a file in Claude Code and run a slash command:
```bash
# Fix docstrings in the current file.
/coding.fix_docstring

# Format a test file following the testing rules.
/testing.format

# Format a markdown document.
/markdown.format
```

### Directory Structure
```
.claude/
  skills/
    coding.fix_docstring/SKILL.md   # one skill per directory
    coding.rules.md                  # conventions for all coding skills
    testing.format/SKILL.md
    testing.rules.md
  templates/
    code.template.py                 # canonical Python file structure
    testing.template.py              # canonical test file structure
    notebook_template.ipynb          # canonical notebook structure
```

### Rules Files
A **rules file** (`<topic>.rules.md`) is the single source of truth for a
domain's conventions. When a convention changes, update the rules file once —
every skill that references it picks up the change automatically

### Writing a New Skill
Read `.claude/skills/skill.rules.md` before writing a new skill. It defines:

- File format (YAML frontmatter with `description` and optional `model`)
- Naming conventions (`<topic>.<action>/SKILL.md`)
- How to reference rules files and templates
- Good/bad examples for content style

### SKILL.md Format
Every `SKILL.md` starts with YAML frontmatter followed by imperative markdown
instructions

Minimal skill (most skills look like this):
```markdown
---
description: Format Python code according to project coding conventions and style rules
---

- Format the Python files according to the rules in
  `.claude/skills/coding.rules.md`

- Make sure that the intention of the code is not changed
```

Skill with model override (use `haiku` for cheap, fast tasks):
```markdown
---
description: Format markdown files according to conventions
model: haiku
---

- Apply the guide from `.claude/skills/markdown.rules.md`
- Run `lint_txt.py -i <file>` after formatting
```

Key conventions for `SKILL.md` files:

- Description uses an imperative verb, under 80 characters
- File references use backtick paths: `.claude/skills/coding.rules.md`
- Variables use angle-bracket notation: `<file>`, not `$file`
- Headers start at `##` (no single `#` inside the skill body)
- Instructions use imperative language: "Format the files", not "You should
  format"

### Design Rationale
- **Markdown-first**: Skills live in plain markdown files that are
  version-controlled with git — diffs are readable, history is auditable, and
  PRs are reviewable like code
- **Separation of rules from skills (DRY)**: Convention lives once in
  `<topic>.rules.md`; skills are thin wrappers. Updating a rule propagates
  automatically to every skill that references it — no need to update each skill
  individually
- **Composability**: Skills can reference other skills and multiple rules files;
  a complex workflow can be composed from simpler, tested skills
- **Model selection per skill**: The `model:` frontmatter field allows expensive
  models (Opus) for reasoning-heavy tasks and cheap models (Haiku) for routine
  formatting — declared once in the skill, not re-specified in every invocation

### Tradeoffs and Alternatives
**Skills vs long system prompts**

|                     | Skills                      | Long system prompts    |
| ------------------- | --------------------------- | ---------------------- |
| **Scope**           | Per-task                    | Global                 |
| **Discoverability** | Listed by `mdm skill list`  | Buried in config       |
| **Composability**   | Reference rules files       | Monolithic             |
| **Maintenance**     | Update one rule, propagates | Edit one long file     |
| **Review**          | Each skill is a diff        | Hard to review changes |

System prompts in `CLAUDE.md` are appropriate for project-wide invariants (e.g.,
"never commit without permission"). Skills are appropriate for repeatable,
scoped tasks

**Skills vs custom agents**

- Custom agents require code (Python, TypeScript) and deployment
- Skills are plain markdown — any team member can create or edit them without
  programming knowledge
- Skills are preferable for encoding conventions; agents are preferable for
  complex multi-step orchestration that involves branching logic or tool use

**Skills vs ad-hoc instructions**

- Ad-hoc instructions produce inconsistent output: different phrasings yield
  different interpretations, and Claude has no memory of past sessions or
  decisions
- Skills are consistent, auditable, and reusable across the entire team

## `mdm`: Markdown Document Manager
`mdm` unifies management of research ideas, blog posts, and Claude Code skills
across multiple repositories into one command-line tool

### The Problem `mdm` Solves
- Different types of markdown content live in separate directories
  - Blog posts in one location
  - Claude Code skills in another
  - Research ideas in a third
- Each type required knowing its directory, its command prefix, and its workflow
- `mdm` replaces the old `skill*`, `blog*`, `res*`, `story*` bash families with
  one consistent interface

### Content Types Managed
| Type       | Location                                           |
| ---------- | -------------------------------------------------- |
| `skill`    | `<helpers_root>/.claude/skills/`                   |
| `rules`    | `<helpers_root>/.claude/skills/` (as `*.rules.md`) |
| `blog`     | `<blog_repo>/blog/posts/`                          |
| `research` | `<umd_classes1>/research/ideas/`                   |
| `story`    | `<notes1>/short_stories/`                          |

### Core Actions
- **list**: List markdown files with optional name filter
- **full_list**: List files with full paths
- **describe**: Show descriptions (for skills with YAML metadata)
- **edit**: Open in vim; creates file with template if new
- **copy**: Copy a skill to a new name as a starting point
- **directory**: Print the directory path for a given type
- **types**: Print unique topic prefixes

### Key Commands
```bash
# List all skills.
mdm skill list

# List skills in a specific domain.
mdm skill list coding

# Show descriptions without opening files.
mdm skill describe

# Create or edit a skill (generates a template if the file is new).
mdm skill edit coding.fix_empty_lines

# Copy an existing skill as a starting point.
mdm skill copy coding.fix_comments coding.fix_todo

# Get the directory path for a content type.
mdm skill directory
```

### Prefix Matching
Both type and action support prefix matching — first match wins:

| Short | Expands to  |
| ----- | ----------- |
| `sk`  | `skill`     |
| `bl`  | `blog`      |
| `res` | `research`  |
| `st`  | `story`     |
| `ru`  | `rules`     |
| `l`   | `list`      |
| `f`   | `full_list` |
| `e`   | `edit`      |
| `d`   | `describe`  |
| `c`   | `copy`      |

So `mdm sk l coding` is equivalent to `mdm skill list coding`

## `rig`: Ripgrep Shortcuts

### Why Ripgrep?
`ripgrep` (`rg`) is a fast search tool with smart defaults:

- **Speed**: Often 5–10x faster than `grep`, written in Rust with parallel
  execution
- **Smart defaults**: Automatically respects `.gitignore`, skips binary files,
  and excludes hidden directories
- **Rich features**: Supports regex, file type filtering, and context display

Speed comparison on a typical codebase:

| Tool      | Time (seconds) |
| --------- | -------------- |
| `grep -r` | 4.2            |
| `ack`     | 3.5            |
| `rg`      | 0.4            |

### Basic Ripgrep Usage
```bash
# Search for a pattern in the current directory.
rg "pattern"

# Search only Python files.
rg "pattern" -t py

# Search in a specific directory.
rg "pattern" helpers/

# Case-insensitive search.
rg -i "pattern"

# Show 3 lines of context around each match.
rg "pattern" -C 3

# List only filenames that match (no lines).
rg "pattern" -l

# Match whole words only.
rg -w "word"
```

### `rig`: Team Wrapper Around Ripgrep
`rig` is the team's Python wrapper around `rg` with smart modes and vim
integration. All rig scripts live in `dev_scripts_helpers/system_tools/`

**Main tool syntax:**
```bash
rig <pattern> [<dir>] [<ext>] [--options]
```

```bash
# Search for "hdbg" in Python files under helpers/.
rig "hdbg" helpers py

# Search for "TODO" in all files in the current directory.
rig "TODO"

# Case-insensitive search.
rig "import" . py -i
```

### `rig` Shortcuts
| Command    | Equivalent           | Purpose                                      |
| ---------- | -------------------- | -------------------------------------------- |
| `rigc`     | `rig --cfile`        | Capture output to vim quickfix file          |
| `rigdef`   | `rig --def`          | Search Python class/function definitions     |
| `rigrule`  | `rig --rule`         | Search Markdown headers in `.claude/skills/` |
| `rigtodo`  | `rig --todo`         | Find all `TODO(ai_gp)` markers               |
| `rigtodoc` | `rig --todo --cfile` | TODOs → vim quickfix                         |
```bash
# Find all Python functions/classes named "build".
rigdef "build"

# Browse all rule headers across the skills library.
rigrule

# Find a specific rule section.
rigrule "Docstring"

# List all open AI TODOs.
rigtodo

# Open TODOs in vim quickfix for navigation.
rigtodoc
```

### Vim Integration
`rig --cfile` captures output to a `cfile` quickfix file and opens it in vim:
```vim
" After running rigc or rigtodoc, navigate matches with:
:cn   " next match
:cp   " previous match
:copen  " open quickfix window
```

### Practical Ripgrep Patterns
```bash
# Find all TODO/FIXME comments in Python files.
rg "TODO|FIXME" -t py

# Find all function definitions matching a name.
rg "^def \w+\(" -t py

# Find all imports of a module.
rg "^import pandas|^from pandas" -t py

# Replace text across files (ripgrep + sed).
rg "old_pattern" -l | xargs sed -i 's/old_pattern/new_pattern/g'

# Count total occurrences across all files.
rg "pattern" -c | awk -F: '{sum+=$2} END {print sum}'
```