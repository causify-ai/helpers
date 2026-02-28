---
name: docker.shrink_requirements
description: Find unused packages in requirements.txt that are not needed by the project code
---

- You are an expert of Docker

- I will pass you a directory $TARGET with a project

- Find out which packages in `requirements.txt` are not needed
  by the code in $TARGET

## Methodology

- Use `grep -r "import <pkg>"` or AST-based analysis to find actual imports
  across all `.py` files in `$TARGET`
- Map package names in `requirements.txt` to their import names (e.g.,
  `Pillow` → `PIL`, `scikit-learn` → `sklearn`, `PyYAML` → `yaml`)
- Also check `setup.py`, `pyproject.toml`, `tasks.py`, and `Makefile` for
  indirect or tool-level usage
- Flag but do NOT remove packages that are:
  - Runtime plugins or extras loaded dynamically (e.g., via `importlib`)
  - Transitive dependencies pulled in by other listed packages
  - Used only in test files (mark them as "test-only")

## Output

- Print a table with columns:
  ```
  package | import_name | used_in_code | verdict
  ```
  - `verdict` is one of: `remove`, `keep`, `investigate`, `test-only`
- Propose the trimmed `requirements.txt` contents and write it to disk
