<!-- toc -->

- [Synopsis](#synopsis)
- [Run from stdin stdout](#run-from-stdin-stdout)
- [Basic Usage](#basic-usage)
- [List of transforms](#list-of-transforms)
- [Code Fixes](#code-fixes)
  * [Code fix by using f strings](#code-fix-by-using-f-strings)
    + [Example](#example)
  * [Code fix by using perc strings](#code-fix-by-using-perc-strings)
    + [Example](#example)
  * [Code fix csfy style](#code-fix-csfy-style)
    + [Example](#example)
  * [Code fix docstrings](#code-fix-docstrings)
    + [Example](#example)
  * [Code fix by existing comments](#code-fix-by-existing-comments)
    + [Example](#example)
  * [Code fix from imports](#code-fix-from-imports)
    + [Example](#example)
  * [Code fix improve comments](#code-fix-improve-comments)
    + [Example](#example)
  * [Code fix log string](#code-fix-log-string)
    + [Example](#example)
  * [Code fix logging statements](#code-fix-logging-statements)
    + [Example](#example)
  * [Code fix star before optional parameters](#code-fix-star-before-optional-parameters)
    + [Example](#example)
  * [Code fix type hints](#code-fix-type-hints)
    + [Example](#example)
- [Code review and refactoring](#code-review-and-refactoring)
  * [Code review correctness](#code-review-correctness)
  * [Code review refactoring](#code-review-refactoring)
- [Markdown Processing](#markdown-processing)
  * [Md clean up how to guide](#md-clean-up-how-to-guide)
  * [Md summarize short](#md-summarize-short)

<!-- tocstop -->

# Run from stdin stdout

```bash
> llm_transform.py -i - -o - <prompt-tag>
```
There is no need to even specify '-' as by default the input and output are 
stdin and stdout respectively.

# Synopsis

The script is capable of performing certain transformations using LLM like 
OpenAI on the input text or the stdin. The transformed output is then stored in 
the output file or the stdout depending upon the arguments passed by the user.

# Basic Usage

```bash
> llm_transform.py -i input.txt -o output.txt -p uppercase
```
The script will produce output from a llm based on the prompt tage provided by 
the user and the transformation takes place on the input file.

# List of transforms

The above line will generate a list of available prompt tags that a user can 
select to transform the input file.

```bash
> llm_transform.py  -p list
# Available prompt tags:
code_fix_by_using_f_strings
code_fix_by_using_perc_strings
code_fix_csfy_style
code_fix_docstrings
code_fix_existing_comments
code_fix_from_imports
code_fix_improve_comments
code_fix_log_string
code_fix_logging_statements
code_fix_star_before_optional_parameters
code_fix_type_hints
code_fix_unit_test
code_review_correctness
code_review_refactoring
code_transform_apply_csfy_style
code_transform_apply_linter_instructions
code_transform_remove_redundancy
code_write_1_unit_test
code_write_unit_test
md_clean_up_how_to_guide
md_rewrite
md_summarize_short
scratch_categorize_topics
slide_bold
slide_elaborate
slide_improve
slide_improve2
slide_reduce
test
```

# Code Fixes

## Code fix by using f strings

It fixes the code to use f-string insted of conventional string formatting. It a
lso uses a post transformation of removal of code delimiter.

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_by_using_f_strings
  ```
- Suppose input.txt contains the following:
  ```python 
      "Hello, %s. You are %d years old." % (name, age)
     ...
  ```
- Expect the following output in output.txt
  ```python
     "Hello, {name}. You are {age} years old." 
     ....
  ```

## Code fix by using perc strings

This is exactly opposite to the 'code_fix_by_using_f_string' where the 
transformation is to use %formatting instead of f-strings. 

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_by_using_perc_strings
  ```
- Suppose input.py contains the following:
  ```python 
     "Hello, {name}. You are {age} years old." 
     ...
  ``` 
- Expect the following output in output.py
  ```python
     "Hello, %s. You are %d years old." % (name, age)
     ....
  ```

## Code fix csfy style

Apply all the transformations required to write code according to the
Causify conventions.

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_csfy_style
  ```

## Code fix docstrings

Ensures each function has a properly structured REST-style docstring. It adds 
missing docstrings or complete partial ones according to the best practice.

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_docstrings
  ```
- Suppose input.py contains the following:
  ```python 
     def format_greeting(name: str, *, greeting: str = "Hello") -> str:
     ...
  ``` 
- Expect the following output in output.py
  ```python
        def format_greeting(name: str, *, greeting: str = "Hello") -> str:
        """
        Format a greeting message with the given name.

        :param name: the name to include in the greeting (e.g., "John")
        :param greeting: the base greeting message to use (e.g., "Ciao")
        :return: formatted greeting (e.g., "Hello John")
        """
     ....
  ```

## Code fix by existing comments

Fix the already existing comments in the Python code.

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_by_existing_comments
  ```

## Code fix from imports

Fix code to use imports instead of "from import" statements.

### Example

- Command:
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_from_imports
  ```
- Suppose input.py contains the following:
  ```python 
     from X import Y
     ...
  ``` 
- Expect the following output in output.py
  ```python
     import X.Y
     ....
  ``` 

## Code fix improve comments

Add comments to python code.

### Example

- Command:
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_improve_comments
  ```
- Suppose input.txt contains the following:
  ```python 
     import pandas
     import numpy 
     import scipy
     ...
  ``` 
- Expect the following output in output.txt
  ```python
     # Import libraries
     import pandas
     import numpy
     import scipy
     ....
  ``` 

## Code fix log string

Fix logging statements and dassert statements by using % formatting instead
of f-strings (formatted string literals)

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_log_string
  ```
- Suppose input.py contains the following:
  ```python 
     _LOG.info(f"env_var='{str(env_var)}' is not in env_vars=\
                                      '{str(os.environ.keys())}'")
  ``` 
- Expect the following output in output.py
  ```python
     _LOG.info("env_var='%s' is not in env_vars='%s'", env_var, \
                                          str(os.environ.keys()))
  ```  

## Code fix logging statements

Add logging statements to Python code.

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_logging_statements
  ```
- Suppose input.py contains the following:
  ```python 
      def get_text_report(self) -> str:
          """
          Generate a text report listing each module's dependencies.

          :return: Text report of dependencies, one per line.
          """
  ``` 
- Expect the following output in output.py
  ```python
      def get_text_report(self) -> str:
          """
          Generate a text report listing each module's dependencies.

          :return: Text report of dependencies, one per line.
          """
          _LOG.debug(hprint.func_signature_to_str())
  ```  

## Code fix star before optional parameters

Fix code missing the star before optional parameters.

### Example

- Command:,
  ```bash
     > llm_transform.py -i input.py -o output.py
     -p code_fix_star_before_optional_parameters
  ```
- Suppose input.py contains the following:
  ```python 
      def format_greeting(name: str, greeting: str = "Hello") -> str:
     ...
  ``` 
- Expect the following output in output.py
  ```python
      def format_greeting(name: str, *, greeting: str = "Hello") -> str:
     ...
  ```  

## Code fix type hints

Add type hints to the Python code passed.

### Example

- Command:
  ```bash
     > llm_transform.py -i input.py -o output.py -p code_fix_type_hints
  ```
- Suppose input.py contains the following:
  ```python 
      def process_data(data, threshold=0.5):
        results = []
        for item in data:
            if item > threshold:
                results.append(item)
        return results
  ``` 
- Expect the following output in output.py
  ```python
        def process_data(data: List[float], *, \
                         threshold: float = 0.5) -> List[float]:
        results: List[float] = []
        for item in data:
            if item > threshold:
                results.append(item)
        return results
  ```  

# Code review and refactoring

## Code review correctness

Designed to review a Python script for correctness and quality, then output 
line-numbered suggestions using a structured format.

- Command:,
  ```bash
     > llm_transform.py -i input.py -o cfile -p code_review_correctness
  ```

## Code review refactoring

Review the code for refactoring opportunities.

- Command:,
  ```bash
     > llm_transform.py -i input.py -o cfile -p code_review_refactoring
  ```

# Markdown Processing

## Md clean up how to guide

Format the text to rewrite as a how_to_guide and contain the sections like 
  - Goal / Use Case
  - Assumptions / Requirements
  - Step-by-Step Instructions
  - Alternatives or Optional Steps
  - Troubleshooting

- Command:,
  ```bash
     > llm_transform.py -i input.md -o output.md -p md_clean_up_how_to_guide
  ```

## Md rewrite

  Rewrite the text passed in a technical document style to
  increase clarity and readability.

- Command:,
  ```bash
     > llm_transform.py -i input.md -o output.md -p md_rewrite
  ```

## Md summarize short

  Summarize the text in less than 30 words.

- Command:,
  ```bash
     > llm_transform.py -i input.md -o output.md -p md_summarize_short
  ```

 