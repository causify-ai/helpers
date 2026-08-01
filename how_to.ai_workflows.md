There are skills, topics and rules
See .claude/skills/skill.rules.md

**Skills** are specific, actionable tasks organized by topic (e.g., `coding.format`, `testing.create`).
Each skill lives in `.claude/skills/<TOPIC>.<ACTION>/SKILL.md` and contains step-by-step instructions, examples, and verification steps.

**Topics** are categories that group related skills and conventions (e.g., `coding`, `testing`, `markdown`, `notebook`).
Topics organize skills semantically and each topic may have a corresponding `.claude/skills/<TOPIC>.rules.md` file documenting conventions.

The topics are:
- `architecture` - Architecture and design documentation
- `auto_task` - Automated task definitions and workflows
- `bash` - Bash scripting and shell commands
- `blog` - Blog post creation and formatting
- `cfile` - C/C++ file conventions
- `coding` - Python code style and conventions
- `latex` - LaTeX document processing
- `markdown` - Markdown formatting and structure
- `notebook` - Jupyter notebook conventions
- `pytest` - Testing framework and patterns
- `readme` - README file creation and updates
- `slides` - Presentation slide creation
- `svg` - SVG graphics handling
- `text` - General text and writing conventions
- `tikz` - TikZ diagram creation
- `tool_X_in_60_mins` - Tool tutorials and guides
- `visuals` - Visual design and graphics

The rules are:
Convention and standards files (`.claude/skills/<TOPIC>.rules.md`) that define best practices for each topic.
These files contain:
- Naming conventions and patterns
- Code/content style guidelines
- Decision criteria for consistency
- Examples of good and bad practices
Rules are referenced by skills to maintain consistency and avoid duplication across related tasks.

see .claude/skills/

Rules are specified
# - Full path (path:line:header format with header validation)
#   ```
#   --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions"
#   ```
# - Line number only (extracts the section starting at that line)
#   ```
#   --rule ".claude/skills/coding.rules.md:58"
#   ```
# - Keyword search: (searches for unique matching rule using rigrule)
#   ```
#   --rule "dassert"
#   ```
> lint_cc.py --rule ".claude/skills/coding.rules.md:58:## Mark Private Functions" --files "file.py"
# #############################################################################

mdm_skill.md
