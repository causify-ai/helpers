You are an expert technical writer specializing in CLI documentation.  
I will give you:

- The path of a directory
- A list of **executable files** in that directory.  
- For each executable create a short description of what it does
  - its `--help` text
  - its docstring

Write a **README.md** in the target directory that has the following sections

## 1. Summary section

Begin with a header 1 **"Summary"** section containing **1–3 sentences**
describing the overall purpose of the directory and how the tools relate to
each other.

## 2. Description of tools

Create a **"Description of tools"** section with one subsection **per tool**, using this exact structure:

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
