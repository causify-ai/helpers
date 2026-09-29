Conventions for the tutorial proposal documents under
`class_project/project_descriptions/*/*.md`: their file naming, section
structure, and the `README.md` tracking table

- A proposal specifies a "Learn X in 60 Minutes" tutorial for one tool `X` and the
  class projects that use it
- The tutorial itself must follow `.claude/skills/tutorials_in_60_mins.rules.md`

# Directory Layout

## Files

- Each proposal is one file
  `class_project/project_descriptions/{MSML610,DATA605}/<Tool>_Project_Description.md`
  - `<Tool>` is the package name with its official capitalization
  - Use `_` instead of spaces, e.g., `Apache_Arrow` and not `Apache Arrow`
  - Keep the suffix `_Project_Description.md` exactly
- The shared template is `.claude/templates/tutorial_specs.template.md`
- The tracking index is `class_project/project_descriptions/README.md`
- The work of the students lands in
  `class_project/{msml610,data605}/<Session>/projects/`, where `<Session>` is the
  class session, e.g., `Fall2026`

## Status

- Track the status of a proposal only in the `README.md` tracking table

# Proposal Structure

## Sections

- A proposal has these sections, in this order:
  1. `# Description`: what the tool is, with a `## Technologies Used` subsection
     for the tool name and its key features
  2. `# Tutorial`: the spec of the tutorial of the current class session
  3. `# Project`: the projects, with one `## Project <N>: <Title>` subsection for
     `N` in 1, 2, 3
     - `Project 1` is the main project and has a `### Milestones` subsection
- Do not use `---` lines to separate blocks, separate them with a blank line
- Do not invent new sections; reuse the ones in the template

## Description

- Start the file with the level 1 heading `# Description`
- Write one paragraph that answers:
  - What is the tool?
  - What problem does it solve?
  - Why is it worth a 60-minute tutorial?
- Under `## Technologies Used`, write the tool name and 3-5 bullets of key features
  - The features are the checklist that the `<project>.API.ipynb` notebook must
    cover

## Session Scope

- Do not add a heading for the class session
- Write `# Tutorial` and the `### Milestones` subsection of `Project 1` for the
  current class session only
- When a new session starts, update these sections and leave the older text to the
  Git history
- Record the session in the `Session` column of the `README.md` tracking table
- Mark unfinished text with `TODO(ai_gp): <what to improve>`

## Tutorial Section

- The `# Tutorial` section is the spec of the "Learn X in 60 Minutes"
  tutorial for the current session
- Always state that the tutorial follows the usual "Learn X in 60 mins" approach,
  and link `.claude/skills/tutorials_in_60_mins.rules.md`
- Say where the work starts:
  - If `tutorials/<Tool>/` exists, improve it and do not restart from scratch
  - If it does not exist, create it with
    `.claude/skills/tutorials_in_60_mins.create/SKILL.md`
- Name a reference tutorial to imitate, e.g.,
  `msml610/tutorials/L03_knowledge_representation/`
- Point to the skills that automate part of the work, e.g.,
  `.claude/skills/notebook.*`, and ask the student to document how they used them
- Optionally name 1-3 related tools to compare with, and the aspect to compare
  - E.g., compare Polars with pandas from the functional point of view
  - E.g., compare CrewAI with LangChain, LangGraph, and Autogen
- List the three deliverables: `<tool>_utils.py`, `<tool>.API.ipynb`, and
  `<tool>.example.ipynb`
  - Write `<tool>` as the lowercase tool name that is a valid Python module name,
    e.g., `crewai_utils.py` and `semantic_kernel_utils.py`

## Milestones Subsection

- The `### Milestones` subsection lists, in order, the steps that deliver the
  tutorial and the project of the session
- Every milestone must be related to the project that contains it:
  - Name the project tasks that the milestone advances, using the task names of
    the project
  - Name the result that the milestone produces, e.g., a deliverable file, a
    table, or a plot
- Do not write generic milestones that fit any tool, e.g., "Read the
  documentation"
- Shape the milestones with the time split of
  `.claude/skills/tutorials_in_60_mins.rules.md`: setup, introduction, API
  notebook, example notebook
  - The API notebook milestone covers the features of the tool that the project
    tasks use
  - The example notebook milestone implements the project tasks end to end
- Write the project first and the milestones after, so the milestones follow from
  the project and not the reverse
- Use `TODO(ai_gp): Add milestones related to the project` while the project is
  not defined
- Do not add milestones to `Project 2` and `Project 3`, only to `Project 1`

## Projects

- Put the projects under the level 1 heading `# Project`
- Use the heading `## Project <N>: <Title>` for each project
- Give normally 3 projects
- Do not renumber a project when another project is removed
- `Project 1` is the main project: the one that is specified the most
  - Give it a `### Milestones` subsection
  - It should reuse the code in `<Tool>_utils.py`, so the example notebook
    orchestrates the code and does not duplicate it
- `Project 2` and `Project 3` are alternatives that are specified less and have
  no milestones
- Any project can have a difficulty, but write it only in the `**Difficulty**`
  bullet and never in the title
- Write each field as a top-level bullet, e.g., `- **Project Objective**: ...`, and
  nest the tasks under `- **Tasks**:`
- Use the fields in this order:
  1. `**Difficulty**: <N> (<Easy|Medium|Hard>)` (optional)
  2. `**Project Objective**`: one or two sentences with the goal to optimize
  3. `**Dataset Suggestions**`
  4. `**Tasks**`
  5. `**Bonus Ideas (Optional)**`
- Use this difficulty ladder for the `**Difficulty**` value:
  - `1 (Easy)`: one dataset, one model or one API path, basic use of the tool
  - `2 (Medium)`: feature engineering, comparing several models or methods, tuning
  - `3 (Hard)`: several data sources or an advanced feature of the tool, plus
    evaluation of uncertainty, robustness, or trade-offs

## Dataset Suggestions

- Give the name of the dataset and a link in the format `[<Name>](<URL>)`
- Use a public dataset with a stable link, e.g., Kaggle, UCI, or a GitHub repo
- Prefer real data to synthetic data
- Choose a dataset small enough to run end-to-end in the Docker container, because
  the notebooks must run after a kernel restart

## Tasks

- Write 4-6 tasks in the order of the workflow:
  1. Data ingestion and preprocessing
  2. Problem definition
  3. Use of the tool, naming the concrete class, model, or API
  4. Evaluation with named metrics
  5. Visualization and interpretation
- Format each task as `**<Verb Phrase>**: <one sentence>`
- Make each task produce an observable output, e.g., a table or a plot
- Name the features of the tool, so the project exercises the tool and not generic
  ML

## Bonus Ideas

- Give 1-3 optional extensions
- Always use the plural label `**Bonus Ideas (Optional)**`, even for one idea

# Writing Conventions

## Formatting

- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
- Wrap prose lines at 85 characters maximum, as required by
  `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  - Fenced code blocks are exempt from wrapping
- Do not use `---` lines as separators, use a blank line instead
- Use `-` bullets and a blank line after each heading
- Do not end lines with two spaces to force a line break

## Heading Levels

- Start the headers from level 1 and do not skip a level, as required by
  `.claude/skills/markdown.rules.md`
  - Use `#` for the main sections: description, tutorial, and project
  - Use `##` for the subsections: technologies used and each project
  - Use `###` for the milestones of `Project 1`
- Do not use `####` headers, so there are no level 4 headers
- Older proposals use `###` and `####` and have a heading per session: restructure
  them to the layout above when you edit them

## Template Usage

- Follow the template `.claude/templates/tutorial_specs.template.md` for the
  section structure of a proposal
- Do not invent new top-level sections

# README Tracking Table

## Table Columns

- The MSML610 table in `class_project/project_descriptions/README.md` is under the
  heading `## MSML610: Advanced Machine Learning`
- Use this column order:
  `| Project name | Status | Authors | GitHub Issue | Result | Session |`
- Sort rows alphabetically by `Project name`

## Cell Values

- `Project name`: the tool name, linked to `MSML610/<Tool>_Project_Description.md`
  - Encode spaces as `%20` in the link
- `Status`: `Ready`, `In_progress`, or `Done`
- `Authors`: the GitHub user of each student
- `GitHub Issue`: the issue used to do the work
- `Result`: the directory in `class_project/msml610/<Session>/projects/`
- `Session`: the class session taken from the `Result` directory, e.g., `Fall2026`
- Use `<br>` to put several values in one cell, one per result
- Use an empty `Status` and `—` in the other columns for a proposal that nobody
  has taken yet

## Adding a Proposal

- Add a row to the table when you add a new proposal file
- Update the row when the status, the authors, or the result change

# Tutorial Ecosystem

## Conventions

- `.claude/skills/tutorials_in_60_mins.rules.md`: main spec for a 60-minute
  tutorial
  - Time split: setup, intro, API notebook, example notebook
  - Deliverables: `<project>_utils.py`, `<project>.API.ipynb`,
    `<project>.example.ipynb`
- `.claude/skills/tutorials_in_30_mins.rules.md`: shorter 30-minute variant

## Skills

- `.claude/skills/tutorials_in_60_mins.create/SKILL.md`: create a new tutorial dir
- `.claude/skills/tutorials_in_60_mins.format/SKILL.md`: format a dir to follow the
  conventions
- `.claude/skills/tutorials_in_60_mins.merge_markdown/SKILL.md`: merge a markdown
  file into a notebook
- `.claude/skills/tutorials_in_60_mins.propagate_docker_changes/SKILL.md`: sync the
  Docker files with `project_template`
- `helpers_root/how_to.ai_workflows.md`: lists the `tutorials_in_60_mins` skill
  group

## Workflow

- `tutorials/README.gp.md`: steps to create a tutorial, from
  `class_project/create_project.py` to `/blog.write_tutorial_readme`
- `tutorials/tutorials_checklist.md`: onboarding checklist and quality principles
- `helpers_root/docs/blogging/all.write_blog.how_to_guide.md`: blog guide that
  points to the tutorial conventions

## Templates and Examples

- `tutorials/project_template/`: skeleton to copy (`template_utils.py`,
  `template.API.ipynb`, `template.example.ipynb`, Docker scripts)
- `tutorials/fastapi/`: complete example of the three deliverables
- `tutorials/<tool>/`: one dir per tool, e.g., `shap`, `lime`, `tsfresh`,
  `LangChain_LangGraph`, `TorchRL_MAC`
- `research/Causal_Analysis_of_Agent_Skill_And_Luck/all.learn_Causal_Analysis_of_Success_in_60_minutes.how_to_guide.md`:
  research-side tutorial

## Blog Posts

- `website/docs/blog/posts/in_60_mins.<Tool>.md`: published posts (`CausalML`,
  `Tensorflow`, `AutoGen`, `BambooAI`, `TorchRL_MAC`, `FastAPI`)
- `website/docs/blog/posts/draft.in_60_mins.GluonTS.md`: draft post
- `website/README.blog.md`: tracks blog posts and their status

# Examples

- `class_project/project_descriptions/MSML610/Ax_Project_Description.md`: a
  proposal with the three project options in the standard fields
- `class_project/project_descriptions/MSML610/CrewAI_Project_Description.md`: a
  proposal with a `Tutorial` section that has full specs
