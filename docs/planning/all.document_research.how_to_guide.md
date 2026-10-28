# How to Document Research

## Summary

- Goal: a reader sees what was run, what result came out, and what to do next,
  without asking
- Use this guide for a project that runs experiments, e.g., in notebooks
- The implementation, the findings, and the decisions go in `progress.md`
  - See [`docs/planning/all.plan_work.how_to_guide.md`](/docs/planning/all.plan_work.how_to_guide.md#keep-a-progress-log)
- The visual evidence (e.g., screenshots of the results) goes in a Google Doc

## Keep a Google Doc per Project

- Keep one Google Doc for the research of each project
  - The Google Doc holds the visual evidence
  - `progress.md` holds the findings and the decisions made to implement the
    mechanisms
- Save the Google Doc in the shared
  [research dir](https://drive.google.com/drive/folders/1XQ5zrk80eScbcynOsc1loDppzAjGNy2x)
  - Create a subdir named exactly like the GH issue of the project
  - Put the Google Doc and its supporting files in that subdir
- Link the Google Doc from the GH issue, the PR, and `progress.md`

## Make the Research Reproducible

- Add unit tests for the notebooks
  - Fast tests as smoke tests, with a small run
  - Slow and superslow tests to freeze important research results
  - See `.claude/skills/notebook.rules.md` section "Testing Notebook"
- Add unit tests for the code with the same approach
  - See `.claude/skills/testing.rules.md`
- Use a `config` (e.g., a Python dict) that controls all the parameters of an
  experiment
  - The `config` becomes the signature of the experiment
  - Given the `config`, one can reproduce exactly the set up

## Write One Entry per Day of Work

- Write one entry for every day of work with:
  - Screenshots of the results from the notebooks
  - Pointers to the relevant sections and files
    - E.g., the notebook, the section header, the script
  - Comments on what each experiment means
  - What was learned
  - What is next
- Use this skeleton for each daily entry:
  ```text
  Date: <date>

  Screenshots:
  - <Screenshot of a result from a notebook>
    - Where: <notebook / section / file>
    - What it does: <what the code or the plot does>

  Learned:
  - <What was learned from the results>

  Next:
  - <The next step>
  ```
