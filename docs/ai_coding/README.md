<!-- toc -->

- [AI Coding Documentation](#ai-coding-documentation)
- [Structure of the Dir](#structure-of-the-dir)
- [Description of Files](#description-of-files)
  * [Instructions and Guidelines](#instructions-and-guidelines)
  * [Templates](#templates)
  * [Tool Guides](#tool-guides)
  * [Reference and Examples](#reference-and-examples)
- [Description of Executables](#description-of-executables)

<!-- tocstop -->

# AI Coding Documentation

This directory contains comprehensive documentation and templates for
AI-assisted software development, covering coding standards, testing patterns,
documentation guidelines, and guides for various AI coding tools.

# Structure of the Dir

- `ai.claude_code.how_to_guide_figs/`: Screenshots and images for Claude Code
  setup and usage guide
- `ai.github_copilot_review.how_to_guide_figs/`: Screenshots demonstrating
  GitHub Copilot review workflow

# Description of Files

## Instructions and Guidelines

- `ai.coding_instructions.md`: Python coding standards including assertions,
  logging patterns, and script templates
- `ai.unit_test_instructions.md`: Unit testing conventions including test
  structure, naming patterns, and golden file testing
- `ai.md_instructions.md`: Style guide for writing structured bullet-point notes
  optimized for AI and human readability
- `ai.blog_instructions.md`: Markdown formatting guidelines for writing blog
  posts with proper structure and metadata
- `ai.paper_instructions.md`: Academic writing guidelines for formal, objective
  computer science papers
- `ai.instruction_template.md`: Workflow template for creating Python scripts
  with tests, documentation, and planning steps

## Templates

- `code_template.py`: Template demonstrating Causify coding style with logging,
  docstrings, REST comments, and helper patterns
- `unit_test_template.py`: Template showing unit test structure with helper
  methods, test cases, and assertion patterns
- `notebook_template.py`: Jupyter notebook template in py:percent format with
  standard setup cells and imports
- `notebook_template.ipynb`: Jupyter notebook template in ipynb format
- `ai.readme_template.md`: Template and instructions for generating README files
  for directories with tool descriptions

## Tool Guides

- `all.claude_code.how_to_guide.md`: Comprehensive guide covering Claude Code
  usage, workflows, AI development tools, and best practices
- `ai.claude_code.how_to_guide.md`: Quick start guide for using Claude Code CLI
  on dev servers with authentication setup
- `ai.claude_code_workflows.reference.md`: Reference document with practical
  Claude Code workflow examples and commands
- `ai.claude_skills.how_to_guide.md`: Guide on creating and using Claude Skills
  for specialized, reusable AI workflows
- `ai.github_copilot_review.how_to_guide.md`: Guide for requesting and using
  GitHub Copilot code reviews on pull requests
- `all.claude_artifacts.how_to_guide.md`: Tutorial on creating and editing
  interactive Claude Artifacts
- `all.llm_cli.how_to_guide.md`: Installation and usage guide for the llm CLI
  tool by Simon Willison

## Reference and Examples

- `all.summarizing_example.reference.md`: Example demonstrating transformation
  from prose to structured bullet-point notes
- `ai.gp_blog_prompt.md`: Prompt template for rewriting blog posts in Matt
  Levine and Scott Galloway style

# Description of Executables

This directory contains no executable files. All tools referenced in the
documentation are located in other directories such as
`dev_scripts_helpers/llms/` and `dev_scripts_helpers/documentation/`.