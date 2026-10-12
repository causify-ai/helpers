---
description: Break a complex feature into an ordered PR plan, with a spec per complex PR
model: opus
---

# Goal

- Given a request from the user to implement a complex feature or component, break
  it into an ordered sequence of small, reviewable PRs, and write a full spec for
  every PR complex enough to need one, without implementing any code

## Input

- The user passes a description of the feature/component to implement and optionally
  an existing plan file to extend

# When to Use This Skill

- Use it when one request is too large for a single PR: it needs more than one
  logical, independently reviewable change, and at least one of those changes has
  a design decision worth writing down
- For a request that already fits in one PR, skip straight to "Write a Spec for a
  PR" below, with that PR being the whole request

# Workflow

## Understand the Request

- Read related code in the codebase and existing code in the target directory
- If the user references a roadmap/plan file (e.g., `plan.<TOPIC>.md`), read it to
  extract the exact scope of the requested PR/feature
- If an architecture doc already exists for the target directory, read it to
  understand the current design
- If the problem or the desired solution is not perfectly clear, follow
  `.claude/skills/auto_task.rules.md` section "Ask for Clarification Before
  Executing an Unclear Plan" before decomposing anything

## Decompose into PRs

- Break the feature into an ordered sequence of small, cohesive PRs; each PR must
  be reviewable and testable on its own
- Prefer PRs that change whole files over splitting one file's logic across
  multiple PRs
- State each PR's dependency on the PRs before it explicitly; do not leave a
  dependency implicit
- Merge PRs that are individually low risk and low complexity into one PR instead
  of over-fragmenting the sequence

## Decide Which PRs Need a Full Spec

- A PR needs a full spec when it introduces a new interface (class, function, CLI
  flag), makes a non-obvious design decision or trade-off, or carries meaningful
  risk (touches shared/core code, hard to reverse, many call sites)
- A small, mechanical, low-risk PR (rename, config tweak, adding a test) does not
  need one; its bullet description in the plan is enough
- For every PR that needs one, write its spec by following "Write a Spec for a
  PR" below, passing it `<TOPIC>_PR<NUM>` as the topic and pointing it at the plan
  file written below so it can read the PR's exact scope
  - This produces `spec.<TOPIC>_PR<NUM>.md` for that PR

## Write a Spec for a PR

- Create a markdown document following the template
  `.claude/templates/specs.template.md`
- Follow the rules in `.claude/skills/markdown.rules.md` and
  `.claude/skills/text.rules.md`
- Save the result in a file `spec.<TOPIC>.md` in the current directory
  - E.g., to spec out `PR_P2b` from `plan.Noesis.md`, save `spec.PR_P2b.md`
  - Do not name it `plan.<TOPIC>.md`: that name is reserved for the roadmap
    document that lists PRs, not for a single PR's spec
- Do not implement any code: describe the architecture only
  - Short illustrative snippets are fine (e.g., a class interface, a schema, a
    function signature) as long as they are not a full implementation
- Distinguish facts (derived from reading the existing code) from decisions made
  in the spec
- Reference actual code artifacts (file, class, function names) instead of
  paraphrasing them generically
- The entire spec should be no longer than 100 lines using 85 wrapped text
- Update an architecture file, if one exists, following the instructions in
  `.claude/skills/readme.write_architecture/SKILL.md`
  - Only add what matters to understand how the pieces work together, not how
    the new component works internally

## Write the Plan

- Create (or update) the plan file (e.g. `tasks.md`) following
  `.claude/templates/auto_task.template.md`
- Fill in the `* Repo:` checklist per `.claude/skills/auto_task.rules.md` section
  "Multi-Repo Issues, Branches, and PRs"
- For each `PR<NUM>` bullet, link its spec file when one was written:
  `- [ ] PR<NUM>: <Goal> (see spec.<TOPIC>_PR<NUM>.md)`
- Write the bullets according to `.claude/skills/markdown.rules.md` and
  `.claude/skills/text.rules.md` with minimal text
- Do not make any change to the code: only propose the plan and the specs

## Rank the PRs

- Order PR bullets by dependency first: a PR never appears before a PR it depends
  on
- Among PRs with no dependency on each other, order by increasing complexity,
  starting from the PR with the highest confidence in its design

# Conventions

- Follow `.claude/skills/auto_task.rules.md` for plan format, task list format, and
  issue/branch/PR naming
- Follow `.claude/skills/architecture.rules.md` for layering and interface design,
  and for how the decomposition should respect layering
- Follow `.claude/skills/coding.rules.md` and `.claude/skills/testing.rules.md` for
  any illustrative code/test snippets

# Constraints

- Do not implement any code
- Do not create the GitHub issue or branch: that happens later, in whichever
  `auto_task.execute_*` skill runs the plan
- Distinguish facts (derived from reading the existing code) from decisions made
  while decomposing the feature

# Verification

- [ ] The plan file follows `.claude/templates/auto_task.template.md`
- [ ] Every `PR<NUM>` bullet states a standalone goal and its dependencies
      explicitly
- [ ] Every PR complex enough to need one has a `spec.<TOPIC>_PR<NUM>.md`, not
      named `plan.<TOPIC>.md`, linked from its bullet
- [ ] Every spec's section in `.claude/templates/specs.template.md` is filled in
      or explicitly marked "Not applicable"
- [ ] No spec contains full implementation code, only interfaces/illustrative
      snippets
- [ ] Every spec's architecture doc was updated, if one exists for the target
      directory
- [ ] PRs are ordered by dependency, then by decreasing confidence / increasing
      complexity
- [ ] No code was changed: only the plan file and any spec files were written
- [ ] Any unclear problem or solution was raised with the user before the plan was
      finalized
