# Design: <Component>

## Goal

- <What the component does>
- Where it fits: <upstream> -> <this component> -> <downstream>
- Requirements: PRD [`R<N>`](/<project>/docs/01-prd.md#r<n>-<short-description>)
- Decisions: [D<N>](/<project>/docs/03-decisions.md#d<n>-<decision-title>)

## Diagram

```plantuml
!pragma layout smetana
!include <C4/C4_Component>
LAYOUT_TOP_DOWN()
title <Component>: Components
Component(comp1, "<Component Name>", "<Technology>", "<Description>")
Component(comp2, "<Component Name>", "<Technology>", "<Description>")
Rel(comp1, comp2, "<Relationship>")
```

## Files and Import Graph

- `<file>`: <what lives here>
- `<file>` imports `<file>`

## One Request End to End

- <Step 1>
- <Step 2>

## Configuration, Interfaces, and Known Limits

- Configuration: <parameters and defaults>
- Interfaces: <endpoints, functions, CLI flags>
- Known limits: <limit>

## Deliberately Not Built

- <What is out of scope, and where it is tracked>

## Open Questions

1. <Question>
