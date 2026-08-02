<!-- toc -->

- [Editing `Txt` Files](#editing-txt-files)
  * [Format a Chunk of `Txt` File](#format-a-chunk-of-txt-file)
  * [List Possible LLM Transforms](#list-possible-llm-transforms)

<!-- tocstop -->

# Editing `Txt` Files

## Format a Chunk of `Txt` File

- In vim
  ```bash
  :'<,'>!helpers_root/dev_scripts_helpers/llms/llm_transform.py -i - -o - -t md_format
  ```

## List Possible LLM Transforms

- Use `llm_transform.py -t list`
  ```bash
  code_comment
  code_docstring
  code_type_hints
  code_unit_test
  code_1_unit_test
  md_rewrite
  md_format
  slide_improve
  slide_colorize
  ```
