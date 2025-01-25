<!-- toc -->

- [Linter](#linter)
  * [Structure of a Linter script](#structure-of-a-linter-script)
  * [How to introduce a new Linter step](#how-to-introduce-a-new-linter-step)
  * [List of Linter scripts](#list-of-linter-scripts)
    + [Bringing the files in accordance with our rules (modifying)](#bringing-the-files-in-accordance-with-our-rules-modifying)
    + [Checking if the files are in accordance with our rules (non-modifying)](#checking-if-the-files-are-in-accordance-with-our-rules-non-modifying)

<!-- tocstop -->

# Linter

- Linter enforces coding rules we aim to follow
- It is a set of Python scripts that check and possibly modify the code to
  improve its readability and style, detect bugs and other technical issues

## Structure of a Linter script

- Each Linter script contains a `linters.action.Action` class
  - It has the following implemented interface methods:
    - `_execute(self, file_name: str, pedantic: int) -> List[str])` --- returns
      a list of lines where the script detected a failure, along with the
      failure description
    - `check_if_possible(self) -> bool` --- returns True if it is possible to
      execute an action in the current environment
  - It accepts a list of files as an argument for the `run()` method
  - Executing a script is running the `_execute()` method on all the files from
    the list of files passed to `run()`
- Normally, a Linter script checks whether the input files conform to certain
  conventions and (optionally) modifies them if they do not
- For an example of how a Linter script should look like, refer to any of the
  existing ones in `linters/`

## How to introduce a new Linter step

- Create a Python script with the new functionality in `linters/`
  - Regarding the style and structure of the code, follow the example of the
    existing Linter scripts

- Add the new Action to the list of actions in
  [`/linters/base.py`](/linters/base.py)
  - Add to `_MODIFYING_ACTIONS` if it is supposed to modify the files it runs on
    (e.g., fix mistakes, remove or add code)
  - Add to `_NON_MODIFYING_ACTIONS` if it only checks the files and reports the
    results (e.g., warns about incorrect formatting)
  - Specify the name of the action (usually the name of the script without the
    "amp\_" prefix and without the extension), a short description of what it
    does and a reference to the action class
- Unit test the new code in `linters/test/`
  - Add a specific test file for the new code (follow the example of the
    existing test files)
  - (Optional) Add some lines that you expect to trigger and not to trigger the
    new Linter step to the string in
    `Test_linter_py1._get_horrible_python_code1()` in
    [`/linters/test/test_amp_dev_scripts.py`](/linters/test/test_amp_dev_scripts.py),
    and verify that your expectations are correct by updating the golden
    outcomes of the tests in this test file
- Add the new Linter script with a short description to the list below (in
  alphabetical order)

## List of Linter scripts

### Bringing the files in accordance with our rules (modifying)

- `add_python_init_files.py`
  - Adds missing `__init__.py` files to directories

- `amp_add_class_frames.py`
  - Adds frames with class names before the classes are initialized

- `amp_add_toc_to_notebook.py`
  - Adds a table of contents to the first cell of an IPython notebook

- `amp_autoflake.py`
  - A wrapper around [`autoflake`](https://pypi.org/project/autoflake/)
  - Removes unused imports and variables

- `amp_black.py`
  - A wrapper around [`black`](https://black.readthedocs.io)

- `amp_check_md_toc_headers.py`
  - Checks that there is no content before TOC and ensures header levels are
    following hierarchical order without skipping levels.

- `amp_class_method_order.py`
  - Sorts methods in classes so that they are in the order of
    - Init
    - Magic
    - Public static
    - Public regular
    - Private static
    - Private regular

- `amp_doc_formatter.py`
  - A wrapper around [`docformatter`](https://pypi.org/project/docformatter) and
    [`pydocstyle`](http://www.pydocstyle.org)

- `amp_fix_comments.py`
  - Reflows, capitalizes and adds punctuation to comment lines
  - NB! Currently disabled due to instability.

- `amp_fix_md_links.py`
  - Regularizes the format of links to files (incl. figure pointers) in Markdown
    and checks if the files referenced by the links exist

- `amp_fix_whitespaces.py`
  - Standardizes the use of whitespace characters (spaces, tabs, newlines, etc.)

- `amp_format_separating_line.py`
  - Normalizes separating lines in the code

- `amp_isort.py`
  - A wrapper around [`isort`](https://pycqa.github.io/isort/)

- `amp_lint_md.py`
  - A wrapper around [`prettier`](https://prettier.io/).
  - Cleans up Markdown files and updates the table of contents

- `amp_normalize_import.py`
  - Normalizes imports in the code and in the docstring according to our
    conventions

- `amp_processjupytext.py`
  - A wrapper around [`jupytext`](https://jupytext.readthedocs.io)
  - Keeps paired `.ipynb` and `.py` files synchronized

### Checking if the files are in accordance with our rules (non-modifying)

- `amp_check_file_size.py`
  - Checks that files do not exceed the maximum size

- `amp_check_filename.py`
  - Checks that test files and notebooks are located in `test`/`notebooks` dirs
    respectively
  - Checks that the names of non-Master notebooks contain a reference to a task

- `amp_check_import.py`
  - Checks that the `from ... import ...` pattern is used only for the `typing`
    package
  - Confirms that the short import length in `import ... as ...` is no longer
    than 8 symbols

- `amp_check_md_reference.py`
  - Checks if the markdown file is referenced in README.md

- `amp_check_merge_conflict.py`
  - Checks the file for git merge conflict markers (e.g. "<<<<<<< ")

- `amp_check_shebang.py`
  - Check that all and only executable Python files start with a shebang
  - NB! Currently disabled, see DevToolsTask97.

- `amp_flake8.py`
  - A wrapper around [`flake8`](https://flake8.pycqa.org/en/latest/)

- `amp_mypy.py`
  - A wrapper around [`mypy`](https://mypy.readthedocs.io/en/stable/)

- `amp_pylint.py`
  - A wrapper around [`pylint`](https://www.pylint.org/)

- `amp_warn_incorrectly_formatted_todo.py`
  - Checks that TODO comments follow the `# TODO(assignee): task.` format
