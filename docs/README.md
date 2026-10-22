# Documentation

Comprehensive documentation system for software components, development
processes, and team workflows. Organized by functionality, component, and team
with active review tracking and executable documentation validation.

## How to organize the docs

- Documentation can be organized in multiple ways:
  - By software component
  - By functionality (e.g., infra, backtesting)
  - By team (e.g., trading ops)

- We have decided that
  - For each software component there should be a corresponding documentation
  - We have documentation for each functionality and team

- Processes
  - `onboarding`
  - `work_organization`
  - `tools`
  - `coding`
  - ...

- Software components
  - `build`
  - `kaizenflow`
  - `datapull`
  - `dataflow`
  - `trade_execution`
  - `infra`
  - ...

### Dir vs no-dirs

- Directories make it difficult to navigate the docs
- We use “name spaces” until we have enough objects to create a dir

### Tracking reviews and improvements

- Doc needs to be reviewed "actively", e.g., by making sure someone checks them
  in the field
- Somebody should verify that is "executable"

- There is a
  [Master Documentation Gdoc](https://docs.google.com/document/d/1sEG5vGkaNIuMEkCHgkpENTUYxDgw1kZXb92vCw53hO4)
  that contains a list of tasks related to documentation, including what needs
  to be reviewed

- For small action items we add a markdown TODO like we do for the code
  ```
  <!-- TODO(gp): ... -->
  ```

- To track the last revision we use a tag at the end of the document like:
  ```markdown
  Last review: GP on 2024-04-20, ...
  ```

### How to search the documentation

- Be patient and assume that the documentation is there, but you can't find it
  because you are not familiar with it and not because you think the
  documentation is poorly done or not organized

- Use AI agents to find docs by asking "what are the documents about XYZ?"
- Look for files that contain words related to what you are looking for
  - E.g., `ffind XYZ`
- Grep in the documentation looking for words related to what you are looking
  for
  - E.g., `jackmd trading`
- Scan through the content of the references
  - E.g., `all.code_organization.reference.md`
- Grep for the name of a tool in the documentation

## File description

- Invariants:
  - Files are organized by directory (e.g., `docs`, `docs/tools`)
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
  - Contains this README and topic directories with guides, references, and
    explanations for development, processes, and tools.
- `docs/build_system/`
  - Documents CI tools like Gitleaks, Semgrep, linters, and Pytest-Allure
    integrations for the build process.
- `docs/coding/`
  - Provides detailed how-to guides for writing clean, maintainable, and
    review-ready code with AI productivity tips.
- `docs/documentation_meta/`
  - Explains documentation frameworks, diagrams, and tooling for producing
    technical and reproducible docs. Includes the Diataxis file templates.
- `docs/onboarding/`
  - Comprehensive onboarding guides and checklists for developers, interns, and
    contractors. Also includes foundational references like abbreviations and
    curated reading materials.
- `docs/planning/`
  - How to plan work: end-to-end plan of a project, PR loop, progress log, and PR
    description template.
- `docs/tools/`
  - Guides for general-purpose development and infrastructure tools, grouped by
    topic. Holds the guide on evaluating external tools.
  - `docs/tools/ai/`
    - AI-assisted work with Claude Code: skills and rules hub, creating a PR with
      Claude Code, `auto_task`, AI review flows, and code review tools.
  - `docs/tools/codebase/`
    - Codebase hygiene: clean-up scripts, import checks, and how to organize
      imports and packages.
  - `docs/tools/data/`
    - Data formats and acquisition: Parquet with `pyarrow` and web crawling with
      Selenium.
  - `docs/tools/dev_system/`
    - Focused on local development setup, environment configuration, dependency
      management, and repo orchestration.
  - `docs/tools/docker/`
    - Docker usage guides for development workflows, including sibling
      containers, DockerHub, and helper containers.
  - `docs/tools/git/`
    - Git and GitHub usage and automation, including hooks, Gitleaks, repo
      integration, and the manual PR flow.
  - `docs/tools/helpers/`
    - Small helper modules and utilities, like caching, playback, dataframes, and
      interactive grids.
  - `docs/tools/ide/`
    - Setup and usage of PyCharm and Visual Studio Code.
  - `docs/tools/invoke/`
    - Invoke task workflows, including printing a bash tree and copying a Git
      branch.
  - `docs/tools/linter/`
    - Development and customization of linters and link fixers for markdown
      content.
  - `docs/tools/notebooks/`
    - Guides for managing and plotting data in Jupyter notebooks, including
      pandas and publishing.
  - `docs/tools/security/`
    - Secure access and storage: SSH usage and VeraCrypt encrypted volumes.
  - `docs/tools/testing_profiling/`
    - Test coverage with Codecov and subprocess/Docker coverage, plus profiling
      Python code.
  - `docs/tools/thin_environment/`
    - Documentation of lightweight Python environments for GitHub and CI/CD
      pipelines.
- `docs/work_organization/`
  - Team process documentation: roles, workflows, feedback, issue tracking, and
    collaboration practices like Scrum and Kaizen.
