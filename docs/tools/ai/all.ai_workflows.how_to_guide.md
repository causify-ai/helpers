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
  - `architecture`: Architecture and design documentation, including project design
    docs
  - `auto_task`: Automated task definitions and workflows
  - `bash`: Bash scripting and shell commands
  - `blog`: Blog post creation and formatting
  - `cfile`: vim cfile conventions
  - `coding`: Python code style and conventions
  - `latex`: LaTeX document processing
  - `markdown`: Markdown formatting and structure
  - `notebook`: Jupyter notebook conventions
  - `project`: Docs that plan and track a project (PRD, design, plan, progress log)
  - `pytest`: Testing framework and patterns
  - `readme`: README file creation and updates
  - `slides`: Presentation slide creation
  - `svg`: SVG graphics handling
  - `text`: General text and writing conventions
  - `tikz`: TikZ diagram creation
  - `tutorial_in_60_mins`: Tool tutorials and guides
  - `visuals`: Visual design and graphics
// TODO(ai_gp): Add tools_in_30_mins and other missing ones

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

## Run a Skill

- There are three ways to run a skill `<topic>.<action>`, depending on how much
  control you need
  - See the "Related Docs" section for the docs of each tool

### Slash Command in a Claude Code Session

- Type the skill name with a leading `/` in a Claude Code session, followed by the
  file to operate on
  ```text
  claude> /<topic>.<action> <file>
  ```
  - E.g., `/coding.fix_comments helpers/hio.py`
- Use this to run one skill interactively and review the result before moving on

### `cc_lint.py` From the Shell

- Run the skill on one or more files outside a session:
  ```bash
  > cc_lint.py --files "<file>" --skill <topic>.<action> --mode one_shot_with_cc
  ```
- Select files by git state instead of by name with `--modified`, `--branch`,
  `--last_commit`, or `--all_files`
- Use this to run the same skill over many files, or from a script
- Use `--dry_run` to print the command without executing it

### `cc` Wrapper for Interactive Sessions

- `cc` starts an interactive Claude Code session with the repo defaults
  - Passes extra arguments to `claude`
  - Selects the model with flags (e.g., `--anth`, `--ds`, `--model MODEL_STR`)
  - Renames the tmux pane while the session runs
- Start a session, then run a skill with a slash command:
  ```bash
  > cc
  ```
  ```text
  claude> /<topic>.<action> <file>
  ```
- Use `cc -p "<prompt>"` to run a single prompt non-interactively
- See `dev_scripts_helpers/ai/README.md` for all the options

### Pick the Right Way

- Slash command: one skill, one file, you review as it runs
- `cc_lint.py --skill`: many files, scripted runs, or a fixed model per run
- `cc`: open-ended sessions that mix several skills and manual edits

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
- Locate the rule with `rigrule "<keyword>"` or by browsing
  `.claude/skills/<TOPIC>.rules.md`
- Apply it with
  ```bash
  > cc_lint.py --rule "<keyword or path:line>" --files "<file>" --mode one_shot_with_cc`
  ```

### Lint Files by Topic Instead of a Single Rule
- Use `cc_lint.py --files "<files>" --topic <topic> --mode one_shot_with_cc`
  to apply the topic's full rules file, or `--modified` / `--branch` /
  `--last_commit` / `--all_files` instead of `--files` to select files by git
  state rather than by name

### Run a Skill on a File
- Execute one skill (as opposed to a whole rules file) on a file
  - See the "Run a Skill" section above for the three ways to do it

### Create or Browse a Skill
- `mdm skill list` (or `mdm skill list <pattern>`) to see what already exists
- `mdm skill edit <topic>.<action>` to open the skill, or scaffold a new one if
  it doesn't exist yet
- Follow `.claude/skills/skill.rules.md` for frontmatter, structure, and naming; add
  or update the topic's `.claude/skills/<topic>.rules.md` if the skill introduces a
  new convention

### Add or Update a Rule
- Decide rule vs. skill per `.claude/skills/skill.rules.md` ("Rules vs Skills"):
  rules capture conventions and decision criteria that apply across tasks; skills
  capture a single step-by-step task
- Edit `.claude/skills/<TOPIC>.rules.md`, keeping related rules grouped under `#`
  sections with `##` sub-rules
- Verify the rule is discoverable: `rigrule "<keyword>"` should resolve to it
  uniquely

### Start a New File From a Template
- Look up the file type in `.claude/rules.md` to find its template (e.g., `.py` ->
  `.claude/templates/coding.template.py`)
- Copy the template to the new file's path and fill in the `<VAR>` placeholders
- Apply the corresponding rules with
  ```
  > cc_lint.py --files "<file>" --topic <topic> --mode one_shot_with_cc
  ```
  to check the new file follows conventions the template doesn't already encode
  (e.g., naming, docstring content)

## Coding Workflows

- These workflows use the `coding.*` skills on Python files
- Commit before running a skill, so that each skill produces a separate, easy to
  review diff
  - See `docs/tools/ai/all.ai_review.how_to_guide.md`

### Coding Skills at a Glance

| Skill                            | Use when                                        |
| :------------------------------- | :---------------------------------------------- |
| `coding.todoai_gp`               | Implement the `TODO(ai_gp)` items in a file     |
| `coding.annotate_with_todoai`    | Add a `TODO(ai_gp)` for each rule violation     |
| `coding.reorg_functions`         | Reorder the functions in a file                 |
| `coding.factor_common_code`      | Remove duplicated code, mostly in test files    |
| `coding.fix_from_imports`        | Replace `from X import Y` with `import X`       |
| `coding.fix_use_helpers`         | Replace ad-hoc code with `helpers` functions    |
| `coding.fix_bloated_imports`     | Import big packages only where they are needed  |
| `coding.fix_type_hints`          | Fix type hints                                  |
| `coding.fix_dasserts`            | Fix `dassert` calls                             |
| `coding.fix_pyright`             | Run `pyright` and fix the reported lints        |
| `coding.fix_comments`            | Fix docstrings and comments, no logic change    |
| `coding.fix_empty_lines`         | Remove empty lines inside functions             |
| `coding.improve_code_for_humans` | Add comments and `_LOG.debug` statements        |
| `coding.rename`                  | Rename a file, function, or variable everywhere |
| `coding.find_doc`                | Find and summarize the docs of code             |

- The other `coding.*` skills (e.g., `fix_inline`, `make_function_private`,
  `use_single_return`) follow the same pattern
  - List them with `mdm skill list coding`

### Implement TODOs in a File

- This is the most common coding workflow
- Write the instruction in the code as a `TODO(ai_gp)` comment
  ```python
  # TODO(ai_gp): Factor out this block into a helper function
  # TODO(ai_gp): Add a test for the empty input case
  # TODO(ai_gp): foo_bar -> compute_foo_bar
  ```
  - `-> XYZ` means "rename to `XYZ`" and updates all the references
- List the pending TODOs with `rig --todo`
- Run the skill on the file
  ```text
  claude> /coding.todoai_gp <file>
  ```
  - It fixes also the other instances of the same TODO in the file
  - It removes a TODO only if it was implemented
  - If it cannot do it, it leaves the TODO and adds a comment with the reason
- Review the diff and run the unit tests of the file
- To fix a single TODO, pass the `rig --todo` output line instead of the file
  ```text
  claude> /coding.todoai_gp <file>:<line>:# TODO(ai_gp): ...
  ```

### Let the Rules Write the TODOs, Then Implement Them

- Use this to review a file against `.claude/skills/coding.rules.md` before
  changing any code
- Add the TODOs without modifying the code
  ```bash
  > cc_lint.py --files "<file>" --add_todos --mode one_shot_with_cc
  ```
  - Alternatively, run `/coding.annotate_with_todoai <file>`
    - It annotates the file, asks you to commit, and then runs
      `/coding.todoai_gp` after you confirm
    - Test files also get the `testing.rules.md` rules
- Read the TODOs and delete the ones you disagree with
- Commit, then implement the remaining ones with `/coding.todoai_gp <file>`

### Clean Up a Python File With a Sequence of Skills

- Use this on a new or messy file, e.g., a script or a `*_utils.py`
- Run the skills in this order, committing between steps
  1. Structure: `/coding.reorg_functions <file>`
  2. Duplication: `/coding.factor_common_code <file>`
  3. Imports: `/coding.fix_from_imports`, `/coding.fix_use_helpers`,
     `/coding.fix_bloated_imports`
  4. Types and lints: `/coding.fix_type_hints`, `/coding.fix_dasserts`,
     `/coding.fix_pyright`
  5. Text last: `/coding.fix_empty_lines`, `/coding.fix_comments`,
     `/coding.improve_code_for_humans`
  6. Run the unit tests of the file
- Comments go last since the earlier steps change the code they describe
- Run the same sequence from the shell, one skill per call
  ```bash
  > for skill in coding.fix_from_imports coding.fix_type_hints coding.fix_comments; do
      cc_lint.py --files "<file>" --skill $skill --mode one_shot_with_cc
    done
  ```
- To apply all the coding rules in a single call, use the topic instead of skills
  ```bash
  > cc_lint.py --files "<file>" --topic coding --mode session
  ```
  - `session` applies one rules section per turn in the same session
  - Skills give more control since you review the diff after each one

### Remove Duplication in Test Files

- Preview first with `--dry_run`
  ```text
  claude> /coding.factor_common_code <test_file> --dry_run
  ```
  - It reports the proposed helper functions and the duplicated locations
  - It writes a vim quickfix `cfile` to jump to the duplicated blocks
    (`:cfile cfile`)
- Run it again without `--dry_run` to apply the refactoring
- Then run `/coding.fix_type_hints <test_file>` and the unit tests

### Fix `pyright` Lints

- Run the skill on one file at a time for large sets of files
  ```text
  claude> /coding.fix_pyright helpers/hpandas_*.py one file at the time
  ```
- It saves `tmp.pyright_before.txt` and `tmp.pyright_after.txt`: check that the
  second has fewer issues
- It runs the matching `test/test_<file>.py`

## Notebook Workflows

- These workflows use the `notebook.*` skills
- A notebook is a triplet of files, kept in sync with `jupytext`
  - `<name>.ipynb`: The notebook
  - `<name>.py`: The paired Python file
  - `<name>_utils.py`: The code behind the cells
- The notebook skills sync the pair at the end
  - Pair a new notebook with
    `jupytext.py --action pair --files <name>.ipynb`
- Follow `.claude/skills/notebook.rules.md` for the conventions

### Notebook Skills at a Glance

| Skill                               | Use when                                         |
| :---------------------------------- | :----------------------------------------------- |
| `notebook.brainstorm_outline`       | Get 5 notebook ideas from some material          |
| `notebook.create_outline`           | Write the cell-by-cell plan of a notebook        |
| `notebook.implement_outline`        | Build the notebook from an outline               |
| `notebook.create_api_intro`         | Build a notebook that teaches a package API      |
| `notebook.lint_numbered_cells`      | Renumber cells and sync function names           |
| `notebook.split_header_cells`       | One header per markdown cell                     |
| `notebook.split_cells`              | One logical task per code cell                   |
| `notebook.format_md_cells`          | Format markdown cells as nested bullets          |
| `notebook.format_interactive_cells` | Fix the markdown around interactive cells        |
| `notebook.fix_logging`              | Use the standard logging init                    |
| `notebook.refactor_to_utils`        | Move notebook code into `*_utils.py`             |
| `notebook.delete_dead_code`         | Remove unused functions                          |
| `notebook.fix_packages`             | Align Docker files and install packages in cells |
| `notebook.create_animation`         | Make an animation from an `interact` function    |

### Notebook From Lecture Material

- Use this to turn a lecture or a doc into an interactive notebook
- Brainstorm (optional)
  ```text
  claude> /notebook.brainstorm_outline <lecture file>
  ```
  - It writes `notebook_ideas.<TAG>.md` with 5 ideas
- Create the outline from a lecture, a URL, or the ideas file
  ```text
  claude> /notebook.create_outline <lecture file, URL, or notebook_ideas.<TAG>.md>
  ```
  - It writes `notebook_outline.<TAG>.md` with no code
  - Review and edit the outline: this is the cheap place to fix the design
- Implement it
  ```text
  claude> /notebook.implement_outline <dir>/notebook_outline.<TAG>.md
  ```
  - It creates the `.ipynb`, the paired `.py`, and the `*_utils.py`
- Polish with the skills below, then run the notebook (see "Check That a Notebook
  Runs")

### Polish a Generated Notebook

- Run these skills on the notebook, committing between steps
  1. `/notebook.split_header_cells <notebook>`
  2. `/notebook.format_interactive_cells <notebook>` for widget notebooks
  3. `/notebook.format_md_cells <notebook>`
  4. `/notebook.lint_numbered_cells <notebook>`
  5. `/notebook.fix_logging <notebook>` if the init cell is not the standard one
- Then clean the paired `*_utils.py` with the coding skills
  - `/coding.fix_from_imports`, `/coding.fix_empty_lines`, `/coding.fix_comments`,
    `/coding.fix_type_hints`
- Run `lint_numbered_cells` last: it renames the `cellN_*()` functions in the
  notebook and in `*_utils.py` to match the headers

### Notebook for a Package API

- Use this to teach the API of a package, one concept per cell
- Prerequisite: a project dir with the Docker files, e.g., cloned from
  `class_project/project_template`
- Create the notebook
  ```text
  claude> /notebook.create_api_intro <package> <doc URL> and save it in tutorials/<package>/<package>.01.API.<topic>.ipynb
  ```
  - Use the next `<ID>` for each new topic, e.g., `02.API.datasets`
- Polish it
  1. `/notebook.split_header_cells <notebook>`
  2. `/notebook.format_md_cells <notebook>`
  3. `/notebook.lint_numbered_cells <notebook>`
  4. `/coding.fix_from_imports <utils file>`
- Check that the notebook runs

### Refactor an Existing Notebook

- Use this when cells hold too much code or the notebook grew organically
- Run the skills in this order, committing between steps
  1. `/notebook.refactor_to_utils <notebook>`: move code to `*_utils.py`
  2. `/notebook.delete_dead_code <notebook>`: remove unused functions
  3. `/notebook.split_cells <notebook>`: one task per code cell
  4. `/coding.fix_empty_lines`, `/coding.fix_comments`, `/coding.fix_type_hints`
     on `*_utils.py`
  5. `/notebook.lint_numbered_cells <notebook>`
- Run `refactor_to_utils` again after the other steps if new inline code appears

### Align Packages and Docker Files

- Use this when a notebook needs a package that is not in the shared image
  ```text
  claude> /notebook.fix_packages <lesson dir> [<notebook> ...]
  ```
  - It aligns `Dockerfile` and `requirements.txt` with the project template
  - It adds a pinned `!pip install` cell to the notebook that needs the package
  - It also scans `*_utils.py`, since the imports of a notebook are not the full
    list

### Check That a Notebook Runs

- Run the paired Python file in Docker
  ```bash
  > docker_cmd.sh "python /git_root/<dir>/<name>.py"
  ```
  - A `# !pip install` cell is a comment in the `.py` file
  - Chain `pip install -q <package>==<version> &&` before `python` for those
    packages
  - See `## Testing Notebook` in `.claude/skills/notebook.rules.md`
- Edit interactively with `docker_jupyter.sh`, then sync the pair with
  `jupytext.py --action sync --files <name>.ipynb`

### Apply All Notebook Rules in One Call

- Use the topic instead of skills for a quick pass
  ```bash
  > cc_lint.py --files "<notebook>" --topic notebook --mode session
  ```
- Use skills when you need to review each transformation

## Related Docs

- Use these docs for details on the tools and conventions mentioned above
  - `docs/planning/all.plan_work.how_to_guide.md`: The sequence of skills from an
    idea to a merged PR, and how to plan and log a project
  - `docs/tools/ai/all.create_pr_with_claude_code.how_to_guide.md`: Do a task
    with Claude Code, from picking the task to a PR
  - `docs/tools/ai/all.auto_task.how_to_guide.md`: Delegate a task list to agents,
    from GitHub issue to merged PR
  - `docs/tools/ai/all.ai_review.how_to_guide.md`: Review flows with LLMs
    (`llm_transform.py`, `ai_review.py`, `inject_todos.py`)
  - `linters2/cc_lint.README.md`: Full reference for `cc_lint.py`
  - `dev_scripts_helpers/system_tools/mdm.README.md`: Full reference for `mdm`
  - `dev_scripts_helpers/ai/README.md`: Options of the `cc` wrapper
  - `.claude/skills/skill.rules.md`: How to write a skill
  - `.claude/rules.md`: Map from file type to rules and templates
- `ai_review.py` is the older prompt-based flow
  - It does not use skills
  - Prefer skills run via `cc_lint.py --skill` for new workflows
