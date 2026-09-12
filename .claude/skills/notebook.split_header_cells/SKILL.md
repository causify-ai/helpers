---
description: Split notebook header cells so each cell has a single header and comment
model: haiku
---

# Goal
- Split each markdown cell in a Jupyter notebook so it contains at most one
  header

# Workflow

## Split Markdown Cells
- Make sure that each markdown cell in a Jupyter notebook contains at most one
  header and some text, but not more than one header
  - **Bad** (there are 3 headers in the same cell: one H1, one H2, one H3)
    ```
    # %% [markdown]
    # Part 3: Composition Examples

    ## Example 1: Minimal End-to-End Workflow

    Rain -> Sprinkler -> Grass Wet
    
    ### Mental Model
    ```
  - **Good** (each header is in a different cell)
    ```
    # %% [markdown]
    # Part 3: Composition Examples

    # %% [markdown]
    ## Example 1: Minimal End-to-End Workflow

    Rain -> Sprinkler -> Grass Wet

    # %% [markdown]
    ### Mental Model
    ```
  - Do not change the content of the markdown text besides splitting cells into
    multiple ones

## Remove Empty Lines
- Remove empty lines at the beginning or end of a markdown cell
  - **Bad** (there are two headers in the same cell, one H1 and one H2)
    ```

    # %% [markdown]
    # Part 3: Composition Examples


    ```
  - **Good** (each header is in a different cell)
    ```
    # %% [markdown]
    # Part 3: Composition Examples
    ```

## Sync with Jupytext
- At the end of the transformation, run `jupytext --sync` to update the Python
  paired notebook, following the conventions in
  `# Code Architecture and Responsibility` -> `## Utilities vs. Notebook
  Responsibilities` in `.claude/skills/notebook.rules.md`

# Constraints
- Do not change or remove any Python code cell
- Do not change the content of the markdown text besides splitting cells

# Verification
- [ ] Confirm no markdown cell contains more than one header
- [ ] Confirm every Python code cell is unchanged
- [ ] Confirm the `.ipynb` and paired `.py` file are in sync via Jupytext
