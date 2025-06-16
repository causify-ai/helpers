# The Bash Print Tree Workflow

## Introduction

- The `bash_print_tree` `invoke` workflow prints a filtered directory tree and optionally updates an existing Markdown file
- It is especially useful for maintaining structured file documentation with preserved inline comments
- The tree can be printed to standard output or embedded into a file between markers like `<!-- tree:start:{name} -->` and `<!-- tree:end -->`

## Workflow Explanation

- The task walks the specified directory up to a maximum depth
- By default, the tree includes all subdirectories and files (excluding Python and test files), and outputs to the terminal only
- You can configure whether to:
  - Include or exclude Python files
  - Include or exclude test files
  - Show only directories
  - Output to a file, while preserving existing inline comments
  - Clean untracked files
- If an output file is given and contains tree markers, the script:
  - Extracts inline comments from the existing tree
  - Preserves these comments while updating the tree section

## Usage Instructions

```bash
# Print the current directory tree
> i bash_print_tree

# Limit depth to 2 and include test files
> i bash_print_tree --path="devops" --depth=2 --include-tests

# Include only Python files
> i bash_print_tree --include-python

# Print only directory names
> i bash_print_tree --only-dirs

# Overwrite tree block in a Markdown file while preserving comments
> i bash_print_tree --path="devops" --output="README.md"

# Clean untracked files before generating the tree
> i bash_print_tree --clean
```

## Example



### Use Cases

- Documenting file structures in `README.md` or similar documentation
- Auditing the layout of codebases and shared folders
- Tracking structural changes over time via version control

### Known Limitations

- Inline comment preservation only works if the tree is wrapped with:

```bash
<!-- tree:start:{folder} -->
...
<!-- tree:end -->
```

- The function does not support excluding arbitrary file patterns beyond test or Python filters

### Future Improvements

- Add support for custom exclude or include glob patterns
- Support multiple tree blocks per file (e.g., for different directories)