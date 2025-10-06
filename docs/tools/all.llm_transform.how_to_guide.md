<!-- toc -->

- [`llm_transform.py` - How-to Guide](#llm_transformpy---how-to-guide)
  * [Goal / Use Case](#goal--use-case)
  * [Assumptions / Requirements](#assumptions--requirements)
  * [Step-by-Step Instructions](#step-by-step-instructions)
  * [Examples](#examples)
    + [Using an Input File](#using-an-input-file)
    + [Using `stdin`](#using-stdin)
    + [Using Vim](#using-vim)
  * [Prompts](#prompts)

<!-- tocstop -->

# `llm_transform.py` - How-to Guide

## Goal / Use Case

- This guide explains how to use `llm_transform.py` on code and text files
  - This tool focuses on improving code quality, documentation, and formatting
    through various transformations (such as code fixes, reviews, and markdown
    processing) using LLMs and Python code

## Assumptions / Requirements

- Docker is installed and properly configured on your system.
- An OpenAI API key is available in your environment variables.

## Step-by-Step Instructions

- Run the transformation command:
  ```bash
  > llm_transform.py -i <input-file> -o <output-file> -p <prompt-tag>
  ```

- You can use an input file or `stdin`

### Using an Input File

- **Input file:** `research_amp/causal_kg/scrape_fred_metadata.py`

  - Example content:
    ```python
    from utils import parser
    from helpers import hopenai
    ```

- **Output file:** `research_amp/causal_kg/scrape_fred_metadata_new.py`

- **Command:**

  ```bash
  > llm_transform.py -i research_amp/causal_kg/scrape_fred_metadata.py -o research_amp/causal_kg/scrape_fred_metadata_new.py -p code_fix_from_imports
  ```

- **Resulting output:**

  ```python
  import utils.parser
  import helpers.hopenai
  ```

### Using `stdin`

- **Command:**

  ```bash
  llm_transform.py -i - -o - -p code_fix_from_imports
  # input:
  from utils import parser
  from helpers import hopenai
  # press Ctrl + D
  ```

- **Resulting output:**

  ```python
  import parser.utils
  import helpers.hopenai
  ```

- You can transform selected lines directly within **Vim**:
  ```vim
  :'<,'>!llm_transform.py -p summarize -i - -o -
  ```

- This command pipes the current visual selection (denoted by `'<,'>`) to
  `llm_transform.py` with the `summarize` prompt and replaces the selection with
  the transformed text.

## Prompts

- Different transformation types are selected by specifying a `<prompt-tag>`
  value
  - Available tags include transformations for code fixes, code reviews, markdown
    processing, and more, as detailed in the reference documentation.

- You can get the current list with:
  ```
  > llm_transform.py -p list
  # Available prompt tags:
  code_apply_cfile
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
  latex_check
  latex_rewrite
  ...
  ```
