---
name: X_in_60_mins.format_rules
description: Format a directory to follow the "Learn X in 60 Minutes" tutorial
  conventions described in
  website/docs/blog/posts/all.learn_X_in_60_minutes.how_to_guide.md
---

- You are an expert at structuring self-contained, reproducible data-science
  tutorials
- I will pass you a directory `$TARGET` (e.g., `tutorials/Autogen`) that
  contains, or will contain, a "Learn X in 60 Minutes" tutorial
- Use `tutorials/Autogen` as the canonical reference implementation

# Step 1: Read the spec and reference

- Read `website/docs/blog/posts/all.learn_X_in_60_minutes.how_to_guide.md` for
  the full spec
- Read `tutorials/Autogen/` to understand what a finished tutorial looks like
- Note the package name (abbreviated below as `XYZ`, e.g., `autogen`)

# Step 2: Docker build system

- The Docker build system should follow the style in
  `.claude/skills/docker.use_standard_style/SKILL.md`

# Step 3: Content

Organise the tutorial content as follows:

```
tutorials/XYZ/
├── XYZ_utils.py          # All reusable helper functions (no notebook logic)
├── XYZ.API.ipynb         # Paired notebook: native API walkthrough
├── XYZ.API.py            # Jupytext percent-format mirror of the above
├── XYZ.example.ipynb     # Paired notebook: full end-to-end application
├── XYZ.example.py        # Jupytext percent-format mirror of the above
└── artifacts/            # Static files needed by the notebooks (images, etc.)
```

## `XYZ_utils.py`

- Module docstring with `Import as:` line, e.g.:
  ```python
  """
  Utility functions for XYZ-based workflows.

  Import as:

  import tutorials.XYZ.XYZ_utils as txyzuti
  """
  ```
- One `import helpers.hdbg as hdbg` at the top; use `hdbg.dassert` for
  assertions
- Group functions under `# ###...### / # Section name / # ###...###` banners
- Every function has a Google-style docstring with `:param:` and `:return:`
- No notebook-level side effects at module import time (no `input()`, no
  `display()`, no `plt.show()`)

## `XYZ.API.ipynb` / `XYZ.API.py`

- Notebook title cell (markdown): `# XYZ API Overview`
- Brief description of what the technology is and what the notebook covers
- Section structure mirrors the library's own concept hierarchy (Agents,
  Messages, Teams, etc.)
- Each concept has:
  - A markdown cell with a short explanation and bullet-point summary
  - One or more code cells with minimal, runnable examples
  - Comments inside code cells explaining non-obvious lines
- Use synthetic / lightweight examples so the notebook runs in under a few
  minutes
- Import `XYZ_utils` for any helper logic already moved there

## `XYZ.example.ipynb` / `XYZ.example.py`

- Notebook title cell (markdown): `# XYZ: <Application Name>`
- Introduction markdown describing the full application and its workflow
- Top-of-notebook setup cell:
  ```python
  # %load_ext autoreload
  # %autoreload 2
  import logging
  ...
  import XYZ_utils
  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```
- Divided into labelled parts (e.g., `## Part 1: ...`, `## Part 2: ...`)
- Each part has a markdown cell explaining its objective and design decisions
- Heavy logic lives in `XYZ_utils.py`; the notebook only orchestrates and
  displays results
- The notebook must run end-to-end after kernel restart

## Merge Markdown into Notebooks

- Merge markdown files into the corresponding ipynb (a.g., API or example)
  - E.g., `tutorial_asana.md` explaining the API of Asana should be merged into
    `asana.API.ipynb`

## Jupytext pairing

- Every `.ipynb` must be paired with a `.py` file in `percent` format
- The `.py` header:
  ```python
  # ---
  # jupyter:
  #   jupytext:
  #     formats: ipynb,py:percent
  #     text_representation:
  #       extension: .py
  #       format_name: percent
  #       format_version: '1.3'
  #       jupytext_version: 1.19.1
  #   kernelspec:
  #     display_name: Python 3 (ipykernel)
  #     language: python
  #     name: python3
  # ---
  ```

# Step 4: Create a README

- Filename: `README.md`
- Required sections (use the Autogen README as the template):
  1. `# XYZ Tutorial` — one-line description
  2. `## Quick Start` — four bullet points:
     - `cd tutorials/XYZ`
     - `./docker_build.sh`
     - `./docker_jupyter.sh`
     - Ordered list of notebooks to open and what each one covers
  3. Link to the project template README for Docker details

- Keep the README short (< 35 lines); the notebooks are the documentation

# Step 5: Checklist

Before marking the tutorial as done, verify each item:

- [ ] All Docker files present and follow `class_project/project_template`
- [ ] `requirements.txt` has pinned versions grouped by section
- [ ] `XYZ_utils.py` contains all reusable functions with proper docstrings
- [ ] `XYZ.API.ipynb` covers the native API with simple examples
- [ ] `XYZ.example.ipynb` contains a complete real-world application
- [ ] Both notebooks are paired with Jupytext `.py` files
- [ ] Both notebooks run end-to-end after kernel restart
- [ ] `README.md` follows the Quick Start template
- [ ] `linters2/lint_branch.sh` passes with no errors
