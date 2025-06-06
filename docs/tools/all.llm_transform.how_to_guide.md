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

This guide explains how to use `llm_transform.py` on code and text files. The
tool focuses on improving code quality, documentation, and formatting through
various transformations such as code fixes, reviews, and markdown processing.

## Assumptions / Requirements

* Docker is installed and properly configured on your system.
* An OpenAI API key is available in your environment variables.

## Step-by-Step Instructions

1. **Choose the Input File**

* Locate the Python or text file you want to transform.
* Alternatively, you can use `stdin` to input the code manually.

2. **Specify the Output File**

* Provide a path to save the transformed output.
* Example path: `research_amp/causal_kg/scrape_fred_metadata.new`

3. **Run the Transformation Command**

* Open a terminal and execute:

  ```bash
  llm_transform.py -i <input-file> -o <output-file> -p <prompt-tag>
  ```

4. **Verify the Result**

* The transformed output is saved to the specified output file.

## Examples

### Using an Input File

* **Input file:** `research_amp/causal_kg/scrape_fred_metadata.py`

  Example content:

  ```python
  from utils import parser
  from helpers import hopenai
  ```

* **Output file:** `research_amp/causal_kg/scrape_fred_metadata_new.py`

* **Command:**

  ```bash
  llm_transform.py -i research_amp/causal_kg/scrape_fred_metadata.py -o research_amp/causal_kg/scrape_fred_metadata_new.py -p code_fix_from_imports
  ```

* **Resulting output:**

  ```python
  import utils.parser
  import helpers.hopenai
  ```

### Using `stdin`

* **Input:** `stdin`

* **Output:** `stdout`

* **Command:**

  ```bash
  llm_transform.py -i - -o - -p code_fix_from_imports
  # input:
  from utils import parser
  from helpers import hopenai
  # press Ctrl + D
  ```

* **Resulting output:**

  ```python
  import parser.utils
  import helpers.hopenai
  ```

### Using Vim

Transform selected lines directly within **Vim**:

```vim
:'<,'>!llm_transform.py -p summarize -i - -o -
```

This command pipes the current visual selection (denoted by `'<,'>`) to
`llm_transform.py` with the `summarize` prompt and replaces the selection with
the transformed text.

## Prompts

Different transformation types are selected by specifying a `<prompt-tag>`
value. Available tags include transformations for code fixes, code reviews,
markdown processing, and more, as detailed in the reference documentation.
