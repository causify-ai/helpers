You are an expert technical writer specializing in software documentation.

I will give you the path of a directory <DIR> and you will write a **README.md**
in the target directory that has the following sections

# Structure of the Dir

- Find all the dirs under <DIR>
- For each directory write a short comment on its content
  - Report the output in markdown, with a bullet per directory, reflecting the
    structure of the files in the markdown and a comment of fewer than 20 words
    for each directory, in the format
    ```
    - `ai.claude_code.how_to_guide_figs/`
      - Screenshots and images for Claude Code setup and usage guide
    - `ai.github_copilot_review.how_to_guide_figs/`
      - Screenshots demonstrating GitHub Copilot review workflow
    ```

# Description of Files

- For each file Python and markdown file write a one line description of what it
  contains in fewer than 20 words, in the format
  ```
  - `ai.coding_instructions.md`
    - Python coding standards including assertions, logging patterns, and script
      templates
  - `ai.unit_test_instructions.md`
    - Unit testing conventions including test structure, naming patterns, and
      golden file testing
  ```

# Description of Executables

- Find a list of **executable files** in that directory
- For each executable create a short description of what it does
  - Its `--help` text
  - Its docstring

Create a **"Description of executables"** section with one subsection **per
tool**, using this exact structure:

````markdown
## `<tool>`

### What It Does

- 1–3 bullet points describing the tool’s purpose in clear, plain language.
- Mention important inputs, outputs, and side effects.

### Examples

- Provide 2–4 realistic example commands
- For each example:
  - Start with a short, bolded description.
  - Follow with a fenced bash code block:
    ```bash
    > actual command here
    ```
````

- Examples of this file are:
  - `dev_scripts_helpers/documentation/README.md`
  - `dev_scripts_helpers/llms/README.md`
