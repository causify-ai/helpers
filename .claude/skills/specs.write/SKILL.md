---
description: Write specification to implement a software component given user request
model: opus
---

# Goal
- Given a request from the user, write a markdown document specifying how to
  implement the requested Python functionality, without implementing it

# Workflow

## Step 1: Understand the Context
- Read related code in the codebase
- Read existing code in the target directory
- If the user references a roadmap/plan file (e.g., `plan.<topic>.md`), read
  it to extract the exact scope of the requested PR/feature
- If an architecture doc already exists for the target directory, read it to
  understand the current design

## Step 2: Write the Spec
- Create a markdown document following the template
  `.claude/templates/specs.template.md`
- Follow the rules in `.claude/skills/markdown.rules.md` and
  `.claude/skills/text.rules.md`
- Save the result in a file `spec.<topic>.md` in the current directory
  - E.g., to spec out `PR_P2b` from `plan.Noesis.md`, save `spec.PR_P2b.md`
  - Do not name it `plan.<topic>.md`: that name is reserved for the roadmap
    document that lists PRs, not for a single PR's spec

## Step 3: Update the Architecture Doc
- Update an architecture file, if one exists, following the instructions in
  `.claude/skills/readme.write_architecture/SKILL.md`
  - Only add what matters to understand how the pieces work together, not
    how the new component works internally

# Conventions
- Follow `.claude/skills/architecture.rules.md` for layering and interface
  design
- Follow `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md`
  for any illustrative code/test snippets
- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for formatting

# Constraints
- Do not implement any code: describe the architecture only
  - Short illustrative snippets are fine (e.g., a class interface, a schema,
    a function signature) as long as they are not a full implementation
- Distinguish facts (derived from reading the existing code) from decisions
  made in this spec
- Reference actual code artifacts (file, class, function names) instead of
  paraphrasing them generically

- The entire spec should be no longer than 100 lines using 85 wrapped text

# Verification
- [ ] File saved as `spec.<topic>.md`, not `plan.<topic>.md`
- [ ] Every section in `.claude/templates/specs.template.md` is filled in or
  explicitly marked "Not applicable"
- [ ] No full implementation code, only interfaces/illustrative snippets
- [ ] Architecture doc updated, if one exists for the target directory
