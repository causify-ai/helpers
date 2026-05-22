# Learn X in 60 Minutes Tutorial Format

## Overview
Create a hands-on, beginner-friendly tutorial that teaches a Big Data, AI, LLM,
or data science technology in 60 minutes

### Reader Experience
The 60-minute tutorial follows this time breakdown:

1. **Setup (5 min)**: Clone repo, start Docker container, verify environment
2. **Introduction (10 min)**: Read overview markdown, understand use cases
3. **API Exploration (20 min)**: Work through `{project}.API.ipynb` notebook
4. **Complete Example (25 min)**: Work through `{project}.example.ipynb`
   notebook

### Tutorial Goals
Each tutorial provides:

- **Conceptual understanding**: Clear explanations of what the technology is and
  when to use it
- **Practical application**: A complete example showing real-world usage with
  working code that runs immediately
- **Reproducibility**: Guaranteed to work through automated testing with all
  dependencies and setup handled via Docker

### Standards
All tutorials must:

- Follow the same consistent structure across all topics
- Use GitHub with standard code organization
- Handle all packages through Docker (`docker_build`, `docker_bash`)

## Architecture

### Deliverables
Every tutorial consists of three core files:

- **`{project}_utils.py`**: Python module with reusable helper functions and
  wrappers
  - Contains all logic, helper functions, and tool wrappers
  - No notebook-level side effects at import time
  - Notebooks call functions from this module instead of embedding complex code

- **`{project}.API.ipynb`**: Jupyter notebook exploring the native API
  - Walkthrough of core classes, functions, and configuration
  - Describes the lightweight wrapper layer on top of the native API
  - Uses simple/synthetic examples so it runs quickly
  - Most code is moved to `*_utils.py`

- **`{project}.example.ipynb`**: Jupyter notebook with end-to-end application
  - Demonstrates a complete real-world application
  - Orchestrates logic from `*_utils.py` and displays results
  - Shows how to use the wrapper layer according to project specifications

### Folder Structure
Organize the tutorial directory as:
```
tutorials/XYZ/
├── XYZ_utils.py          # Reusable helper functions (no notebook logic)
├── XYZ.API.ipynb         # Native API walkthrough (paired with XYZ.API.py)
├── XYZ.API.py            # Jupytext percent-format mirror
├── XYZ.example.ipynb     # End-to-end application demo (paired with XYZ.example.py)
├── XYZ.example.py        # Jupytext percent-format mirror
├── Dockerfile
├── docker_build.sh       # Build the Docker image
├── docker_bash.sh        # Open shell in container
├── docker_jupyter.sh     # Launch Jupyter in container
├── docker_clean.sh       # Remove container and image
├── requirements.txt      # Python dependencies (pinned versions)
├── README.md             # Quick start guide
└── artifacts/            # (Optional) Static files used by notebooks (images, etc.)
```

## Build the Implementation

### Create `{project}_utils.py`
- Start with module docstring and `Import as:` line:
  ```python
  """
  Utility functions for XYZ-based workflows.

  Import as:

  import tutorials.XYZ.XYZ_utils as txyzuti
  """
  ```
- Import `helpers.hdbg` at the top; use `hdbg.dassert` for assertions
- Group functions under section banners (e.g.,
  ```
  # ###...###
  # Section name
  # ###...###
  ```
- Every function must have a docstring with `:param:` and `:return:` tags
- No notebook-level side effects at import time (no `input()`, `display()`,
  `plt.show()`)

### Create `{project}.API.ipynb`
- Title cell (markdown): `# XYZ API Overview`
- Brief description of the technology and what the notebook covers
- Structure sections to mirror the library's concept hierarchy (e.g., Agents,
  Messages, Teams)
- Each concept section:
  - Markdown cell with short explanation and bullet-point summary
  - Code cells with minimal, runnable examples
  - Comments explaining non-obvious lines
- Use synthetic/lightweight examples so the notebook runs in under a few minutes
- Import and use `XYZ_utils` for helper logic

### Create `{project}.example.ipynb`
- Title cell (markdown): `# XYZ: <Application Name>`
- Introduction markdown describing the full application and workflow
- Top-of-notebook setup cell with:
  ```python
  %load_ext autoreload
  %autoreload 2

  import logging
  import XYZ_utils

  logging.basicConfig(level=logging.INFO)
  _LOG = logging.getLogger(__name__)
  ```
- Divide into labeled parts (e.g., `## Part 1: ...`, `## Part 2: ...`)
- Each part has markdown explaining its objective and design decisions
- Place heavy logic in `XYZ_utils.py`; notebook only orchestrates and displays
- **Must run end-to-end after kernel restart**

## Complete the Tutorial

### 4. Set Up Docker
The Docker container structure should follow
[`class_project/project_template/`](https://github.com/gpsaggese/gpsaggese.github.io/tree/master/class_project/project_template)

- Container must have everything needed to run tutorials and develop
- Include all dependencies in `requirements.txt` with pinned versions
- Group dependencies by section (core, optional, dev)

### Create Jupytext Pairing
Every `.ipynb` must be paired with a `.py` file in `percent` format

- Run `jupytext --set-formats ipynb,py:percent <ipynb-file>` to set up pairing
- After modifying the notebook, sync with `jupytext --sync <python-file>`
- The Jupytext header format is automatically generated

### Merge Markdown Into Notebooks
- Incorporate standalone markdown files directly into the corresponding notebook
- Example: `tutorial_asana.md` explaining the API should be merged into
  `asana.API.ipynb`

### Create README.md
- Required sections (use the Autogen README as template):
  1. `# XYZ Tutorial`: one-line description
  2. `## Quick Start`: bullets for:
     - `cd tutorials/XYZ`
     - `./docker_build.sh`
     - `./docker_jupyter.sh`
     - Numbered list of notebooks to open and what each covers
  3. Link to project template README for Docker details
- Keep it short (< 35 lines); notebooks are the documentation

## Validation Checklist
Before submission, verify:

- [ ] Docker files present and follow `class_project/project_template`
- [ ] `requirements.txt` has pinned versions grouped by section
- [ ] `XYZ_utils.py` contains all reusable functions with docstrings
- [ ] `XYZ.API.ipynb` covers native API with simple examples
- [ ] `XYZ.example.ipynb` is a complete real-world application
- [ ] Both notebooks are paired with Jupytext `.py` files
- [ ] Both notebooks run end-to-end after kernel restart
- [ ] `README.md` follows the Quick Start template
- [ ] Linter passes with no errors (`linters2/lint_branch.sh`)

## Tools of the Trade
- Format markdown: `lint_txt.py -i ...`
- Clean up Python code: Use the agent skill `/coding.format`
- Render locally: `website/test.sh`
- Reference tutorials:
  - [`DATA605`](https://github.com/gpsaggese/gpsaggese.github.io/tree/master/data605/tutorials)
  - [`MSML610`](https://github.com/gpsaggese/gpsaggese.github.io/tree/master/msml610/tutorials)
