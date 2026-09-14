---
description: Check a file against applicable convention rules and list violations
model: opus
---

# Goal
- Find the violations of the rules that apply to the given file `<FILE>` and
  create a plan to fix them

# Workflow

## Select Rules
- Given the file passed by the user `<FILE>`
- If the user specifies a set of rules, apply those
- Otherwise, read `@.claude/rules.md`, which maps file types to the set of
  rules to use
  - Find what rule files `<RULE_FILE>` apply to `<FILE>`
  - Print the file that needs to be used as
    ```text
    Rules: <RULE_FILE>
    ```

## Read Rules
- Read `<RULE_FILE>`
- Check the rules from `<RULE_FILE>` one by one on `<FILE>`
- List the ones that are not satisfied, in order of importance and effort

## Save the Plan to File
- Do not implement any change; create `<FILE>.plan.md` to describe all the
  transformations needed to follow the rules without changing the content or
  intention of `<FILE>`

# Verification
- [ ] `<FILE>` itself was not modified
- [ ] `<FILE>.plan.md` lists every violation found, ordered by importance and
      effort
- [ ] The plan does not change the content or intention of `<FILE>`
