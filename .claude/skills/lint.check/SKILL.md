---
description: Check with convention rules need to be applied
model: haiku
---

Given the file passed by the user `<file>`

- Read `.claude/rules.md` which maps file types to the set of rules to use

- Find what files of rules `<rule_file>` apply to the file passed by the user

- Print the file that needs to be used as
  ```
  Rules: <rule_file>
  ```

- Read that file `<rule_file>`

- Check the rules from `<rule_file>` one by one on the user file `<file>`, and
  list the ones that are not satisfied

- Ask the user if the violations should be fixed
