<!-- toc -->

- [Operations](#operations)
- [Use templates](#use-templates)
- [Tools](#tools)
  * [`llm_transform.py`](#llm_transformpy)
  * [`transform_notes.py`](#transform_notespy)
  * [`ai_review.py`](#ai_reviewpy)
  * [`inject_todos.py`](#inject_todospy)
  * [`apply_todos.py`](#apply_todospy)
- [Some typical workflows](#some-typical-workflows)
  * [A transform workflow](#a-transform-workflow)
  * [An editing workflow](#an-editing-workflow)
  * [A reviewer workflow](#a-reviewer-workflow)
    + [Example](#example)
  * [How to improve the reviewing tools while reviewing](#how-to-improve-the-reviewing-tools-while-reviewing)

<!-- tocstop -->

# Operations

- There are several operations we want to perform using LLMs:
  - Apply a transformation to a chunk of text
    - E.g., create a unit test
  - Create comments and lints in the form of a `cfile`
    - E.g., lint or AI review based on certain criteria
  - Apply modifications from a `cfile` to a set of files
    - E.g., from linter and AI review
  - Add TODOs from a `cfile` to Python or markdown files
  - Apply a set of transformations to an entire Python file
    - E.g., styling / formatting code
  - Rewrite an entire markdown to fix English mistakes without changing its
    structure
    - E.g., styling / formatting a markdown

- You should always commit your code before applying automatic transforms, in the
  same way that we run the `linter` on a clean tree
  - In this way, modifying a file is a separate commit and it's easy to review

# Use templates

- We use templates for code and documentation to show and describe how a document
  or code should look like, e.g.,
  - `code_template.py` shows our coding style
  - `unit_test_template.py` shows how our unit tests look like
  - `all.how_to_guide_template_doc.md` shows how a Diataxis how to guide should
    be structured and look like (same for `explanation`, `tutorial`, `reference`)

- The same templates can have multiple applications for:
  - Humans:
    - Understand how to write documentation and code
    - As boilerplate
      - E.g., "copy the template and customize it to achieve a certain goal"
  - LLMs:
    - As reference style to apply transforms
    - To report violations of coding styles
    - As boilerplate
      - E.g., "explain this piece of code using this template"

# Tools

## `llm_transform.py`

- There are several classes of transforms:
  - `code_*`: transform Python code
    - `code_fix_*`: fix a specific chunk of code according to a prompt
    - `code_transform_*`: apply a series of transformations
    - `code_write_*`: write from scratch
  - `latex_*`: process Latex code
  - `md_*`: process markdown `md` text and `txt` notes
  - `review_*`: process Python code to extract reviews
  - `scratch_*`: misc and one-off transforms
  - `slide_*`: process markdown slides in `txt` format
  - `text_*`: process free form (not markdown) text

- You can list the available transformations with:

  ```bash
  > llm_transform.py -p list
  # Available prompt tags:
  code_fix_by_using_f_strings
  code_fix_by_using_perc_strings
  code_fix_code
  code_fix_comments
  code_fix_complex_assignments
  code_fix_docstrings
  ...
  ```

## `transform_notes.py`

- Some transformations don't need LLMs and are implemented as code

- You can see the available transforms with:

  ```bash
  > transform_notes.py -a list
  test: compute the hash of a string to test the flow
  format_headers: format the headers
  increase_headers_level: increase the level of the headers
  md_list_to_latex: convert a markdown list to a latex list
  md_remove_formatting: remove the formatting
  md_clean_up: clean up removing all weird characters
  md_only_format: reflow the markdown
  md_colorize_bold_text: colorize the bold text
  md_format: reflow the markdown and colorize the bold text
  ```

## `ai_review.py`

- The rules for AI are saved in the file
  ./docs/code_guidelines/all.coding_style_guidelines.reference.md
- This file has a special structure:
  ```bash
  > extract_headers_from_markdown.py -i ./docs/code_guidelines/all.coding_style_guidelines.reference.md --max_level 2
  - All Style Guide
    - Summary
  - General
    - Spelling
  - Python
    - Naming
    - Docstrings
    - Comments
    - Code Implementation
    - Code Design
    - Imports
    - Type Annotations
    - Functions
    - Scripts
    - Logging
    - Misc
  - Unit Tests
    - Rules
  - Notebooks
    - General
    - Plotting
    - Jupytext
  - Markdown
    - General
    - Headers
    - Text
  ```
  - The first level represents the target language (e.g. `General`, `Python`)
  - The second level represents a rule topic (e.g., `Imports`, `Functions`)
  - The third level represents instructions for an LLM vs Linter, since some
    instructions:
    - Are easier to enforce by an LLM
    - While others should be enforced by the `linter` (even if they are temporary not
      enforced by the `linter` but by LLM or by humans)

## `inject_todos.py`

## `apply_todos.py`

# Some typical workflows

## A transform workflow

- There are 3 types of transforms and review tasks
  - `llm`: executed by an LLM since they are difficult to implement otherwise
    - E.g., "apply this style to a certain file"
  - `linter_llm`: executed by an LLM for now to get something in place, even if
    they should be moved to code / linter
    - E.g., mainly formatting tasks
  - `linter`: executed by the Linter using code and regex

## An editing workflow

- Use `llm_transform.py` to:
  - Edit files manually applying specific transformations to chunks of code
  - Apply transforms to an entire file
  - Read and apply a list of transforms (from a `cfile`) and apply them
  - Format the style of a template to a file

## A reviewer workflow

- This workflow can be used by the author of the code directly or by a reviewer
  - Initially, reviewers use these tools as part of dogfooding of the workflows
  - The goal is to make these tools robust enough so that they can be used
    directly by the author and potentially integrated in the `linter` flow
    itself

- Go to the Git branch with the code to review

- Check which files are modified

  ```bash
  > invoke git_branch_diff_with -t base --only-print-files
  ```

- Run `ai_review.py` on each file to generate a list of comments on the code
  - This is equivalent to running a `review` target with `llm_transform.py`
    (e.g., `llm_transform.py -p review_*`) but it is a separated flow for
    clarify
  - It generates a `cfile` with a list of comments

- Review the TODOs using cfile to jump around files:

  ```bash
  > vim -c "cfile cfile"
  ```
  - You can fix the code according to the TODOs directly
  - Discard a TODO as a false positive or not important

- Run `inject_todos.py` to add TODOs to the files for someone (human or LLM)
  else to fix it later
  - E.g., in a code review you want to ask the author to perform that task

- Run `apply_todos.py` to automatically apply the TODOs using an LLM
  - This can be a risky move

### Example

- There are multiple targets for the `ai_review.py`

  ```bash
  # Specify the target prompt for ai_review.py.
  > PROMPT=review_llm
  > PROMPT=review_correctness
  > PROMPT=review_linter
  > PROMPT=review_architecture

  # Specify the target file.
  > FILE=dev_scripts_helpers/github/dockerized_sync_gh_repo_settings.py
  ```

- Run the `ai_review.py` tool:
  ```bash
  # Run.
  > ai_review.py -i $FILE -p $PROMPT
  ```

- Sometimes you want to edit the tools in a different client while running it on
  a different client:
  ```bash
  # To copy all the reviewer code.
  > \cp -f /Users/saggese/src/helpers1/helpers/lib_tasks_lint.py helpers && \
    i lint_sync_code && ai_review.py -i $FILE -p $PROMPT
  ```

- Review and apply the changes:
  ```bash
  > vi -c "cfile cfile"

  > inject_todos.py --cfile cfile

  > llm_transform.py -i $FILE -p code_fix_code
  ```

## How to improve the reviewing tools while reviewing

- **Problem**: we often want to improve one of our tools (e.g., `linter.py`,
  `ai_review.py`) while reviewing somebody's else code

- There are two use cases
  1. When the code to review is in a different repo than `//helpers`
     - **Solution**:
       - Create a branch in `//helpers`
       - Modify the code for the tools in place
  2. When the code to review is in the repo `//helpers`
     - **Solution**:
       - Use a different Git client to develop and edit the tools
       - Automatically copy `linter.py` / `ai_review.py` code from the client we
         are developing in to the one we are reviewing
         ```bash
         > \cp -f /Users/saggese/src/helpers1/helpers/lib_tasks_lint.py helpers && i lint_sync_code
         ```
       - Run the tools in the different client
       - Before committing the review, we then revert the
         `linter.py / ai_review.py` code
         ```bash
         > i lint_sync_code -r
         ```
