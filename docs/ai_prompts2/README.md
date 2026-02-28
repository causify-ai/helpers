# AI Prompts Documentation

This directory contains LLM prompt templates for code formatting, documentation
generation, writing improvement, and content transformation workflows.

# Structure of the Dir

This directory contains no subdirectories. All prompt templates are stored at
the root level.

# Description of Files

## Coding and Development

- `coding.format_rules.md`
  - Python coding standards including assertions, logging patterns, and script
    formatting rules
- `coding.improve_comments.md`
  - Prompt template for improving code comments clarity and conciseness
- `coding.update_comments.md`
  - Prompt template for updating outdated comments to match current code
    implementation
- `coding.update_expected_vars.md`
  - Prompt for updating expected variable names in test files to match code
    changes
- `coding.factor_common_code.md`
  - Prompt for identifying and refactoring duplicated or near-duplicated code
    blocks into shared functions
- `coding.fix_gh_issue.md`
  - Prompt for analyzing and fixing GitHub issues
- `coding.fix_param_use.md`
  - Prompt for fixing parameter usage issues in Python code
- `coding.find_doc.md`
  - Prompt for finding documentation for files, classes, or functions
- `coding.lint.md`
  - Prompt for improving code appearance by applying formatting rules from
    `coding.format_rules.md` and `testing.format_rules.md`
- `coding.rename.md`
  - Prompt for renaming files, functions, and variables across a codebase with
    proper reference updates
- `coding.review.md`
  - Prompt for reviewing Python code, finding bugs, and providing fixes with
    minimal changes
- `coding.todoai_gp.md`
  - Prompt for implementing TODO(ai_gp) comments in code files
- `coding.update_dir_readme.md`
  - Prompt for creating or updating README.md for a given directory
- `coding.update_file_readme.md`
  - Prompt for creating or updating README.md for a given file
- `coding.make_function_private.md`
  - Prompt for identifying functions not called by other files and making them
    private by prepending underscore

## Testing

- `testing.format_rules.md`
  - Unit testing conventions including test structure, naming patterns, golden
    file testing, and pytest usage
- `testing.fix_unit_tests.md`
  - Prompt for refactoring test code by aligning strings, renaming test methods
    as test1/test2, and factoring out common code into helper functions
- `testing.move_test_code.md`
  - Prompt for moving test code from one file to another using
    `split_in_files.py`
- `testing.reach_coverage.md`
  - Prompt for increasing unit test coverage to approach 100% for a given
    function with structured 4-step process

## Notebooks

- `notebooks.format_rules.md`
  - Jupyter notebook formatting conventions including cell structure, Jupytext
    pairing, widget patterns, and plotting standards
- `notebooks.create_visual_script.md`
  - Prompt for creating markdown descriptions of Jupyter notebook cells with
    visualizations and interactive widgets for educational content
- `notebooks.implement_script.md`
  - Prompt for implementing Jupyter notebook cells from script descriptions with
    utils library integration and widget conventions
- `notebooks.create_animation.md`
  - Prompt for creating video animations from interactive widget functions using
    generate_animation template
- `notebooks.lint.md`
  - Prompt for improving Jupyter notebook appearance using format rules without
    changing behavior
- `notebooks.lint_numbered_cells.md`
  - Prompt for renaming markdown cells with numbered format and reorganizing
    utils code to match cell order
- `notebooks.move_to_lib.md`
  - Prompt for moving Jupyter notebook functions to utils library files while
    keeping only caller code in notebooks
- `notebooks.plots.md`
  - Guidelines for creating plots with pandas/seaborn, adding information
    directly to plots, and styling theoretical vs empirical data
- `notebooks.split_cells.md`
  - Instructions for splitting Jupyter cells so each contains only one concept
    or example with proper commenting structure
- `notebooks.utils_library.md`
  - Guidelines for organizing notebook utility files with proper structure
    following notebook flow with separators

## Documentation and Writing

- `markdown.format_rules.md`
  - Style guide for writing structured bullet-point markdown optimized for AI
    and human readability
- `readme.create.md`
  - Prompt template for generating comprehensive README files with directory
    structure and executable documentation
- `readme.format.md`
  - Formatting guidelines for README files with proper command block structure
    and descriptions
- `text.humanize.md`
  - Guidelines for avoiding AI-style writing patterns and creating natural,
    human-sounding text

## Blog Content

- `blog.create_tldr.md`
  - Prompt for creating three catchy and controversial TLDRs under 20 words
- `blog.format_rules.md`
  - Markdown formatting guidelines for writing blog posts with proper structure
    and metadata
- `blog.add_figures.md`
  - Prompt for adding images, diagrams, and visuals to blog posts using
    graphviz, TikZ, or graphic images

## Academic Papers

- `paper.use_style.md`
  - Academic writing guidelines for formal, objective computer science papers
    with reference checking
- `paper.improve_bibliography.md`
  - Prompt template for improving bibliography formatting and citation accuracy
- `paper.suggest_improvements.md`
  - Prompt for suggesting improvements to academic paper content and structure
- `paper.fix_figures.md`
  - Prompt for fixing figures in academic papers

## Demo and Presentations

- `demo.create_script.md`
  - Prompt for creating 15-slide presentation storyboards for narrated explainer
    videos targeting non-technical audiences
- `demo.create_pictures.md`
  - Prompt for creating visual assets for demonstrations and presentations

## Graphviz and Visualization

- `graphviz.causal_kg_style.md`
  - Style guide for creating causal knowledge graphs using graphviz with
    consistent formatting
- `graphviz.convert_image.md`
  - Prompt for converting images to graphviz dot format by iteratively tweaking
    until matching the original
- `graphviz.generate_legend.md`
  - Prompt for generating legend diagrams for graphviz visualizations

## Slides and Presentations

- `slides.format_rules.md`
  - Guidelines for creating executive-level presentation slides with clear
    structure, bullet points, and image suggestions in markdown format
