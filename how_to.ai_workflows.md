There are skills, topics and rules
See .claude/skills/skill.rules.md

TODO(ai_gp): Describe

The topics are:
TODO(ai_gp): Describe

The rules are:
TODO(ai_gp): Describe

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
