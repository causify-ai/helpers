# Project List

## Summary

- This document lists the projects in this repo that follow
  [`docs/planning/all.plan_work.how_to_guide.md`](/docs/planning/all.plan_work.how_to_guide.md)
- A project is in the list if its `docs/` dir has at least one doc of the doc set
  - `01-prd.md`
  - `02-design.architecture.md` and `02.<N>-design.<component>.md`
  - `03-decisions.md`
  - `04-plan.md`
  - `07-progress.md`
  - `08-how_we_work.md`
- The docs of every project use the fixed slot numbers of
  [`docs/planning/all.plan_work.how_to_guide.md`](/docs/planning/all.plan_work.how_to_guide.md#name-the-docs-with-a-slot-number)
  - A missing doc leaves its slot empty
  - `README.md` and the docs that are not in the doc set have no number
- The docs are found by file name: the content was not checked against
  `.claude/skills/project.rules.md`
- Add a row in the same PR that adds a project or a doc to a project

## Projects

### Full Doc Set

- [`research/Noesis/`](/research/Noesis/)
  - Has the plan, the progress log, the decisions log, and the meta-doc
  - Is the example used in the guide
  - Index of the docs:
    [`research/Noesis/docs/README.md`](/research/Noesis/docs/README.md)

### Partial Doc Set

- [`helpers_root/dev_scripts_helpers/coding_tools/call_graph/`](/helpers_root/dev_scripts_helpers/coding_tools/call_graph/)
  - Has the plan, the progress log, the decisions log, and the `README.md`
- [`research/Estimate_academic_paper_quality/`](/research/Estimate_academic_paper_quality/)
  - Has the PRD, the architecture design, the decisions log, and one design doc
    per component
  - Missing the plan and the progress log
- [`class_project/msml610/Fall2026/projects/UmdTask733_MSML610_Fall2026_Causal_Analysis_of_Financial_Tradability/`](/class_project/msml610/Fall2026/projects/UmdTask733_MSML610_Fall2026_Causal_Analysis_of_Financial_Tradability/)
  - Has the progress log and the decisions log
  - Missing the plan
- [`class_project/msml610/Fall2026/projects/UmdTask677_MSML610_Fall2026_Counterfactual_Attribution_of_Agent_Failures/`](/class_project/msml610/Fall2026/projects/UmdTask677_MSML610_Fall2026_Counterfactual_Attribution_of_Agent_Failures/)
  - Has the plan
  - Missing the progress log and the decisions log

## Doc Coverage

- Every path in the first column is relative to the repo root
- Every project keeps its docs in its `docs/` dir

  | Project                                                                                                             | `01-prd.md` | `02*-design.*.md` | `03-decisions.md` | `04-plan.md` | `07-progress.md` | `08-how_we_work.md` | `README.md` |
  | :------------------------------------------------------------------------------------------------------------------ | :---------- | :---------------- | :---------------- | :----------- | :--------------- | :------------------ | :---------- |
  | `research/Noesis/`                                                                                                  |             | x                 | x                 | x            | x                | x                   | x           |
  | `helpers_root/dev_scripts_helpers/coding_tools/call_graph/`                                                         |             |                   | x                 | x            | x                |                     | x           |
  | `research/Estimate_academic_paper_quality/`                                                                         | x           | x                 | x                 |              |                  |                     |             |
  | `class_project/msml610/Fall2026/projects/UmdTask733_MSML610_Fall2026_Causal_Analysis_of_Financial_Tradability/`     |             |                   | x                 |              | x                |                     |             |
  | `class_project/msml610/Fall2026/projects/UmdTask677_MSML610_Fall2026_Counterfactual_Attribution_of_Agent_Failures/` |             |                   |                   | x            |                  |                     |             |

- `research/Noesis/docs/` has no `01-prd.md`: it has `old.mvp_prd.md` instead
