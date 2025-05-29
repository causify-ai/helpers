# Operations

- There are several operations we want to perform
  - Apply a precise transformation to a chunk of text
    - E.g., create a unit test
  - Extract comments and lints in the form of a `cfile`
    - E.g., lint or AI review based on certain criteria
  - Apply a set of transformations (e.g., styling / formatting code) to an entire
    file
  - Apply modifications from a `cfile` (e.g., from linter and AI review) to a
    file
  - Add TODOs from a `cfile` to Python or markdown files 
  - Rewrite an entire markdown to fix English mistakes without changing its
    structure
  - Reformat an entire markdown or Python using LLMs or code

# Use templates
- We use templates for code and documentation to show and describe how a document
  or code should look like, e.g.,
  - `template_code.py` shows our coding style
  - `template_unit_test.py` shows how our unit tests look like
  - `template_doc.how_to_guide.md` shows how a Diataxis how to guide should be
    structured and look like
  - `template_doc.reference.md` shows how an Diataxis how to guide should be
    structured and look like

- The same template can have multiple applications for:
  - Humans:
    - Understand how to write documentation and code
    - As boilerplate (e.g., "copy the template and customize it to achieve a
      certain goal")
  - LLMs:
    - As reference style to apply transforms
    - To report violations of coding styles
    - As boilerplate (e.g., "explain this piece of code using this template")

# Tools

## llm_transform.py
- There are several classes of transforms
  - `code_*`: transform Python code
    - `code_fix_*`: fix a specific chunk of code according to a prompt
    - `code_transform_*`: apply a series of transformations
    - `code_write_*`: write from scratch
  - `doc_*`: process free form (not markdown) text
    - TODO(gp): Is it worth it, or should be merged with `md_*` targets
  - `latex_*`: process Latex code
  - `md_*`: process markdown `md` text and `txt` notes
    - TODO(gp): 
  - `review_*`: process Python code to extract reviews
  - `scratch_*`: misc
  - `slide_*`: process markdown slides in `txt` format

- You can list the available transformations with:
  ```
  > llm_transform.py -p list
  # Available prompt tags:
  code_fix_by_using_f_strings
  code_fix_by_using_perc_strings
  code_fix_code
  code_fix_comments
  code_fix_complex_assignments
  code_fix_docstrings
  code_fix_from_imports
  code_fix_function_type_hints
  code_fix_log_string
  code_fix_logging_statements
  code_fix_star_before_optional_parameters
  code_fix_unit_test
  code_transform_apply_csfy_style
  code_transform_apply_linter_instructions
  code_transform_remove_redundancy
  code_write_1_unit_test
  code_write_unit_test
  doc_create_bullets
  doc_rewrite
  doc_summarize_short
  latex_rewrite
  md_clean_up_how_to_guide
  md_convert_table_to_bullet_points
  md_convert_text_to_bullet_points
  md_expand
  md_format
  md_remove_formatting
  md_rewrite
  md_summarize_short
  review_correctness
  review_linter
  review_llm
  review_refactoring
  scratch_categorize_topics
  slide_add_figure
  slide_bold
  slide_expand
  slide_reduce
  slide_reduce_bullets
  slide_smart_colorize
  slide_to_bullet_points
  test
  text_rephrase
  ```

## `transform_notes.py`

- These transformations don't need LLMs and are implemented as code

- You can see the available transforms
  ```
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

# Causify flow

## Editing workflows

- Use `llm_transform.py` to
  - Edit files manually applying specific transformations to chunks of code
  - Apply transforms to an entire file

- 
There are 3 types of transforms / review
llm: executed by an LLM since they are difficult to implement otherwise
linter_llm: exected by an LLM but they should be moved to the linter (mainly formatting)
linter: linter

ai_review.py to generate TODOs
inject_todos.py to add TODOs
apply_todos.py to execute TODOs

There is detecting the problems and fixing the problems

## A reviewer workflow

- This can be used by the author of the code or by a reviewer

- Go to the Git branch with the code
- Check which files are modified
  ```
  > i git_branch_diff_with -t base --only-print-files
  ```
- Run `ai_review.py` on each file to generate a list of comments on the code
  - This is equivalent to running a `review` target with `llm_transform.py` 
    (e.g., `llm_transform.py -p review_*`) but it is a separated flow for clarify
- This generates a `cfile` with a list of comments comments
