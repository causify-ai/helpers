---
description: Check a file against convention rules need to be applied
model: opus
---

# Goal
- Find the violations of the rules for the given file and create a plan
  to fix them

# Step 1: Select Rules
- Given the file passed by the user `<FILE>`
- If the user specifies a set of rules apply those
- Otherwise read the following rules which maps file types to the set of rules to
  use
   `@.claude/rules.md`  
  - Find what files of rules `<RULE_FILE>` apply to the file passed by the user
  - Print the file that needs to be used as
    ```
    Rules: <RULE_FILE>
    ```

# Step 2: Read Rules
- Read that file `<RULE_FILE>`

- Check the rules from `<RULE_FILE>` one by one on the user file `<FILE>`
- List the ones that are not satisfied, in order of importance and effort

# Step 3: Save the Plan to File
- Do not implement any change but create a `<FILE>.plan.md` to describe
  all the transformations that need to be done to follow the rule without
  changing the content and the intention of `<FILE>`
