

<!-- toc -->

- [Readme](#readme)
  * [File description](#file-description)

<!-- tocstop -->

# Readme

- This file is the entrypoint of all the documentation and describes all the
  documentation files in the `docs` directory

## File description

- Invariants:
  - Files are organized by directory (e.g., `docs`, `docs/work_tools`)
  - Each file name uses the Diataxis naming convention
  - Each file name should be linked to the corresponding file as always
  - Files are organized in alphabetical order to make it easy to add more files
    and see which file is missing
  - Each file has a bullet lists summarizing its content using imperative mode

## Dir structure

- **Prompt**: For each directory write a short comment on its content, based on
  the names of the files contained. Report the output in markdown, with a bullet
  per directory, reflecting the structure of the files in the markdown and a
  comment of fewer than 30 words for each directory
  ```bash
  > find docs -name "*\.md" -d | sort
  ```

- `docs/`
  - Contains top-level references and guides for documentation, workflows, and
    software components.
- `docs/build_system/`
  - Documents CI tools like Gitleaks, Semgrep, linters, and Pytest-Allure
    integrations for the build process.
- `docs/code_guidelines/`
  - Provides detailed how-to guides for writing clean, maintainable, and
    review-ready code with AI productivity tips.
- `docs/documentation_meta/`
  - Explains documentation frameworks, diagrams, and tooling for producing
    technical and reproducible docs.
- `docs/general_background/`
  - Offers foundational references like glossaries, abbreviations, and curated
    reading materials.
- `docs/onboarding/`
  - Comprehensive onboarding guides and checklists for developers, interns, and
    contractors.
- `docs/tools/`
  - Guides for general-purpose development and infrastructure tools, including
    code hygiene, IDEs, and APIs.
  - `docs/tools/dev_system/`
    - Focused on local development setup, environment configuration, dependency
      management, and repo orchestration.
  - `docs/tools/docker/`
    - Docker usage guides for development workflows, including sibling
      containers, DockerHub, and helper containers.
  - `docs/tools/documentation_toolchain/`
    - Covers the pipeline for rendering images, LaTeX integration, and notebook
      asset extraction for docs.
  - `docs/tools/git/`
    - Git usage and automation guides, including hooks and helper integrations.
  - `docs/tools/helpers/`
    - Small helper modules and utilities, like caching, playback, dataframes, and
      interactive grids.
  - `docs/tools/jupyter_notebooks/`
    - Jupyter-specific enhancements, including TOC creation, Jupytext usage, and
      markdown publishing.
  - `docs/tools/linter/`
    - Development and customization of linters and link fixers for markdown
      content.
  - `docs/tools/notebooks/`
    - Guides for managing and plotting data in Jupyter notebooks, including
      pandas and publishing.
  - `docs/tools/thin_environment/`
    - Documentation of lightweight Python environments for GitHub and CI/CD
      pipelines.
  - `docs/tools/unit_test/`
    - Unit testing practices: writing, structuring, and executing tests
      effectively.
- `docs/work_organization/`
  - Team process documentation: roles, workflows, feedback, issue tracking, and
    collaboration practices like Scrum and Kaizen.
