# `<TOPIC>`: <Title> - Implementation Spec

- One paragraph (or a few bullets) summarizing what was requested and what
  this document specifies
- Scope: what this spec covers, quoting or paraphrasing the source request
  (e.g., a roadmap PR entry in a `plan.<topic>.md`) if there is one
- Roadmap position, if applicable: what this depends on / what depends on it
- State explicitly that this is a specification only: no code in this
  document has been implemented

## Design Decisions

- One bullet (or `### <Decision Name>` subsection) per decision
- For each decision, state the choice and justify it against alternatives,
  existing code, or conventions
- Reference actual code artifacts (file, class, function names) instead of
  paraphrasing them generically

## Trade-off and Alternative Design

- Alternatives considered and why they were not chosen
- The trade-off being made explicit (e.g., simplicity vs. flexibility,
  performance vs. maintainability)

## Out of Scope

- Bullet list of what is deliberately excluded from this spec
- For each item, note why (e.g., separate PR, follow-up, infra work) and
  where it is tracked, if known

## Current State

- Describe the existing code this spec builds on: relevant classes,
  functions, files (`file.py:<line>`)
- Call out the gaps in the current code that this spec needs to close
- Mark this section "Not applicable" for a component built from scratch

## Implementation

- One-line description of how the new code is organized (new files vs.
  changes to existing files)

### `<file1.py>`: `<Class1>`

- Describe the interface: constructor parameters, public methods, return
  types
- Include short illustrative snippets (signatures, schema, pseudocode) only;
  do not write the full implementation

### `<file2.py>`: `<Class2>`

- ...

## Interaction with Existing Code

- Call sites that change and new call sites added
- Data/control flow between the new and existing code
- Backward compatibility: what happens to existing callers/tests unchanged
  by this spec

## Configuration and Secrets

- New environment variables, config files, or secrets introduced, and their
  defaults
- Mark this section "Not applicable" if there is none

## Unit Test Plan

- Follow `.claude/skills/testing.rules.md`
- List test files/classes and one line per test case describing what is
  verified, not how
- Note any existing tests that must keep passing unchanged, as a regression
  signal that default behavior did not change

## Risks and Limitations to Call Out

- Known risks introduced by this design (correctness edge cases,
  performance, migration hazards)
- Anything a reviewer should scrutinize closely

## Result (to Fill in Once Implemented)

- Placeholder: once implemented, record what was actually built vs.
  deferred, and any deviation from this spec
