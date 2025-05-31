"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import dataclasses
import logging
import re
from typing import Generator, List, Optional, Tuple, cast

import dev_scripts_helpers.documentation.lint_notes as dshdlino
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

_TRACE = False

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.


# #############################################################################
# Utils
# #############################################################################


def is_markdown_line_separator(line: str, min_repeats: int = 5) -> bool:
    """
    Check if the given line is a Markdown separator.

    This function determines if a line consists of repeated characters (`#`,
    `/`, `-`, `=`) that would indicate a markdown separator.

    :param line: the current line of text being processed
    :param min_repeats: the minimum number of times the characters have to be
        repeated to be considered a separator, e.g., if `min_repeats` = 2, then
        `##`, `###`, `//` are considered to be line separators, but `#`, `/` are
        not
    :return: true if the line is a separator
    """
    separator_pattern = rf"""
    # Allow optional leading `#` and whitespace.
    \#*\s*
    # Capture a character, then repeat it (`min_repeats` - 1) times.
    ([#/=\-])\1{{{min_repeats - 1},}}
    # Match only whitespace characters until the end of the line.
    \s*$
    """
    res = bool(re.match(separator_pattern, line, re.VERBOSE))
    return res


def is_header(line: str) -> Tuple[bool, int, str]:
    """
    Check if the given line is a Markdown header.

    :return: A tuple containing:
        - A boolean indicating if the line is a header
        - The level of the header (0 if not a header)
        - The title of the header (empty string if not a header)
    """
    # hdbg.dassert(not is_markdown_line_separator(line), "line='%s'", line)
    m = re.match(r"(#+)\s+(.*)", line)
    is_header_ = bool(m)
    if m:
        level = len(m.group(1))
        title = m.group(2)
    else:
        level = 0
        title = ""
    return is_header_, level, title


def process_comment_block(line: str, in_skip_block: bool) -> Tuple[bool, bool]:
    """
    Process lines of text to identify blocks that start with '<!--' or '/*' and
    end with '-->' or '*/'.

    :param line: The current line of text being processed.
    :param in_skip_block: A flag indicating if the function is currently
        inside a comment block.
    :return: A tuple
        - do_continue: whether to continue processing the current line or skip
          it
        - in_skip_block: a boolean indicating whether the function is currently
          inside a comment block
    """
    do_continue = False
    if line.startswith(r"<!--") or re.search(r"^\s*\/\*", line):
        hdbg.dassert(not in_skip_block)
        # Start skipping comments.
        in_skip_block = True
    if in_skip_block:
        if line.endswith(r"-->") or re.search(r"^\s*\*\/", line):
            # End skipping comments.
            in_skip_block = False
        # Skip comment.
        _LOG.debug("  -> skip")
        do_continue = True
    return do_continue, in_skip_block


def process_code_block(
    line: str, in_code_block: bool, i: int, lines: List[str]
) -> Tuple[bool, bool, List[str]]:
    """
    Process lines of text to handle code blocks that start and end with '```'.

    The transformation is to:
    - add an empty line before the start/end of the code
    - indent the code block with four spaces
    - replace '//' with '# ' to comment out lines in Python code

    :param line: The current line of text being processed.
    :param in_code_block: A flag indicating if the function is currently
        inside a code block.
    :param i: The index of the current line in the list of lines.
    :param lines: the lines of text to process
    :return: A tuple
        - do_continue: whether to continue processing the current line or skip
          it
        - in_code_block: a boolean indicating whether the function is currently
          inside a code block
        - a list of processed lines of text
    """
    out: List[str] = []
    do_continue = False
    # Look for a code block.
    if re.match(r"^(\s*)```", line):
        _LOG.debug("  -> code block")
        in_code_block = not in_code_block
        # Add empty line before the start of the code block.
        if (
            in_code_block
            and (i + 1 < len(lines))
            and re.match(r"\s*", lines[i + 1])
        ):
            out.append("\n")
        out.append("    " + line)
        if (
            not in_code_block
            and (i + 1 < len(lines))
            and re.match(r"\s*", lines[i + 1])
        ):
            out.append("\n")
        do_continue = True
        return do_continue, in_code_block, out
    if in_code_block:
        line = line.replace("// ", "# ")
        out.append("    " + line)
        # We don't do any of the other post-processing.
        do_continue = True
        return do_continue, in_code_block, out
    return do_continue, in_code_block, out


def process_single_line_comment(line: str) -> bool:
    """
    Handle single line comment.

    We need to do it after the // in code blocks have been handled.
    """
    do_continue = False
    if line.startswith(r"%%") or line.startswith(r"//"):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Skip frame.
    if is_markdown_line_separator(line):
        do_continue = True
        _LOG.debug("  -> do_continue=True")
        return do_continue
    # Nothing to do.
    return do_continue


def process_lines(lines: List[str]) -> Generator[Tuple[int, str], None, None]:
    """
    Process lines of text to handle comment blocks, code blocks, and single
    line comments.

    :param lines: The list of all the lines of text being processed.
    :return: A list of processed lines of text.
    """
    out: List[str] = []
    in_skip_block = False
    in_code_block = False
    for i, line in enumerate(lines):
        _LOG.debug("%s:line=%s", i, line)
        # 1) Remove comment block.
        if _TRACE:
            _LOG.debug("# 1) Process comment block.")
        do_continue, in_skip_block = process_comment_block(line, in_skip_block)
        if do_continue:
            continue
        # 2) Remove code block.
        if _TRACE:
            _LOG.debug("# 2) Process code block.")
        do_continue, in_code_block, out_tmp = process_code_block(
            line, in_code_block, i, lines
        )
        out.extend(out_tmp)
        if do_continue:
            continue
        # 3) Remove single line comment.
        if _TRACE:
            _LOG.debug("# 3) Process single line comment.")
        do_continue = process_single_line_comment(line)
        if do_continue:
            continue
        out.append(line)
    #
    yield from enumerate(out)


def remove_end_of_line_periods(txt: str) -> str:
    """
    Remove periods at the end of each line in the given text.

    :param txt: The input text to process
    :return: The text with end-of-line periods removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line.rstrip(".") for line in txt.split("\n")]
    txt_out = "\n".join(txt_out)
    return txt_out


def remove_empty_lines(txt: str) -> str:
    """
    Remove empty lines from the given text.

    :param txt: The input text to process
    :return: The text with empty lines removed
    """
    hdbg.dassert_isinstance(txt, str)
    txt_out = [line for line in txt.split("\n") if line != ""]
    txt_out = "\n".join(txt_out)
    return txt_out


# TODO(gp): Add tests.
def remove_code_delimiters(txt: str) -> str:
    """
    Remove ```python and ``` delimiters from a given text.

    :param text: The input text containing code delimiters.
    :return: The text with the code delimiters removed.
    """
    # Replace the ```python and ``` delimiters with empty strings.
    txt_out = txt.replace("```python", "").replace("```", "")
    txt_out = txt_out.strip()
    # Remove the numbers at the beginning of the line, if needed
    # E.g., `3: """` -> `"""`.
    txt_out = re.sub(r"(^\d+: )", "", txt_out, flags=re.MULTILINE)
    return txt_out


def add_line_numbers(txt: str) -> str:
    """
    Add line numbers to each line of text.
    """
    lines = txt.split("\n")
    numbered_lines = []
    for i, line in enumerate(lines, 1):
        numbered_lines.append(f"{i}: {line}")
    txt_out = "\n".join(numbered_lines)
    return txt_out


def remove_formatting(txt: str) -> str:
    # Replace bold markdown syntax with plain text.
    txt = re.sub(r"\*\*(.*?)\*\*", r"\1", txt)
    # Replace italic markdown syntax with plain text.
    txt = re.sub(r"\*(.*?)\*", r"\1", txt)
    # Remove \textcolor{red}{ ... }.
    txt = re.sub(r"\\textcolor\{(.*?)\}\{(.*?)\}", r"\2", txt)
    # Remove \red{ ... }.
    txt = re.sub(r"\\\S+\{(.*?)\}", r"\1", txt)
    return txt


def md_clean_up(txt: str) -> str:
    # Replace \( ... \) math syntax with $ ... $.
    txt = re.sub(r"\\\(\s*(.*?)\s*\\\)", r"$\1$", txt)
    # Replace \[ ... \] math syntax with $$ ... $$, handling multiline equations.
    txt = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", txt, flags=re.DOTALL)
    # Replace `P(.)`` with `\Pr(.)`.
    txt = re.sub(r"P\((.*?)\)", r"\\Pr(\1)", txt)
    # Replace \left[, \right].
    txt = re.sub(r"\\left\[", r"[", txt)
    txt = re.sub(r"\\right\]", r"]", txt)
    # Replace \mid with `|`.
    txt = re.sub(r"\\mid", r"|", txt)
    # E.g.,``  • Description Logics (DLs) are a family``
    # Replace `•` with `-`
    txt = re.sub(r"•\s+", r"- ", txt)
    # Replace `\t` with 2 spaces
    txt = re.sub(r"\t", r"  ", txt)
    # Remove `⸻`.
    txt = re.sub(r"⸻", r"", txt)
    # “
    txt = re.sub(r"“", r'"', txt)
    # ”
    txt = re.sub(r"”", r'"', txt)
    # ’
    txt = re.sub(r"’", r"'", txt)
    # →
    txt = re.sub(r"→", r"$\\rightarrow$", txt)
    # Remove empty spaces at beginning / end of Latex equations $...$.
    # E.g., $ \text{Student} $ becomes $\text{Student}$
    # txt = re.sub(r"\$\s+(.*?)\s\$", r"$\1$", txt)
    # Remove dot at the end of each line.
    txt = re.sub(r"\.\s*$", "", txt, flags=re.MULTILINE)
    # Transform `Example: Training a deep` into `E.g., training a deep`,
    # converting the word after `Example:` to lower case.
    txt = re.sub(r"\bExample:", "E.g.,", txt)
    txt = re.sub(r"\bE.g.,\s+(\w)", lambda m: "E.g., " + m.group(1).lower(), txt)
    # Replace \mid with `|`.
    txt = re.sub(r"\\mid", r"|", txt)
    return txt


# #############################################################################
# Header processing
# #############################################################################


# TODO(gp): This could be done with `HeaderList`.
def extract_section_from_markdown(content: str, header_name: str) -> str:
    """
    Extract a section of text from a Markdown document based on the header
    name.

    The function identifies a section by locating the specified header
    and captures all lines until encountering another header of the same
    or higher level. Headers are identified by the '#' prefix, and their
    level is determined by the number of '#' characters.

    :param content: The markdown content as a single string.
    :param header_name: The exact header name to extract (excluding '#'
        symbols).
    :return: The extracted section as a string, including the header
        line itself and all lines until the next header of the same or
        higher level.
    """
    lines = content.splitlines()
    _LOG.debug(hprint.to_str("lines"))
    extracted_lines = []
    # Level of the current header being processed.
    current_level: Optional[int] = None
    # Flag to indicate if we're inside the desired section.
    inside_section: bool = False
    found = False
    # Process each line in the markdown content.
    for line in lines:
        _LOG.debug(hprint.to_str("line"))
        # Check if the line is a markdown header.
        if line.strip().startswith("#"):
            # Determine the level of the header by counting leading '#'
            # characters.
            header_level = len(line) - len(line.lstrip("#"))
            # Extract the actual header text by stripping '#' and surrounding
            # whitespace.
            header_text = line.strip("#").strip()
            _LOG.debug(hprint.to_str("header_level, header_text"))
            # Handle the end of the desired section when encountering another
            # header.
            if inside_section:
                hdbg.dassert_is_not(current_level, None)
                current_level = cast(int, current_level)
                if header_level <= current_level:
                    break
            # Check if the current line is the desired header.
            if header_text == header_name:
                found = True
                # Set the level of the matched header.
                current_level = header_level
                # Mark that we are now inside the desired section.
                inside_section = True
        # Add the line to the output if inside the desired section.
        if inside_section:
            extracted_lines.append(line)
            _LOG.debug(hprint.to_str("extracted_lines"))
    if not found:
        raise ValueError(f"Header '{header_name}' not found")
    return "\n".join(extracted_lines)


# #############################################################################
# HeaderInfo
# #############################################################################


@dataclasses.dataclass
class HeaderInfo:
    """
    Store the header level, the description, and the line number in the
    original file.

    E.g., `(1, "Chapter 1", 5)` and `(2, "Section 1.1", 10)`
    """

    level: int
    description: str
    line_number: int

    def __init__(self, level: int, description: str, line_number: int):
        hdbg.dassert_isinstance(level, int)
        hdbg.dassert_lte(1, level)
        self.level = level
        #
        hdbg.dassert_isinstance(description, str)
        hdbg.dassert_ne(description, "")
        self.description = description
        #
        hdbg.dassert_isinstance(line_number, int)
        hdbg.dassert_lte(1, line_number)
        self.line_number = line_number
        #
        self.children: List[HeaderInfo] = []

    def __repr__(self) -> str:
        return (
            f"HeaderInfo({self.level}, '{self.description}', {self.line_number})"
        )

    def as_tuple(self) -> Tuple[int, str, int]:
        return (self.level, self.description, self.line_number)


HeaderList = List[HeaderInfo]


def sanity_check_header_list(header_list: HeaderList) -> None:
    """
    Check that the header list is valid.

    1) The first header should be level 1.
    2) All level 1 headers are unique.
    3) Check that consecutive elements in the header list only increase by at
       most one level at a time (even if it can decrease by multiple levels).
       - E.g., the following is valid:
         ```
         # Header 1
         # Header 2
         ## Header 2.1
         ## Header 2.2
         # Header 3
         ```
       - E.g., the following is valid:
         ```
         # Header1
         ## Header 1.1
         ### Header 1.1.1
         # Header 2
         ```
       - E.g., the following is not valid:
         ```
         # Header 1
         ### Header 1.0.1
         # Header 2
         ```
    """
    # 1) The first header should be level 1.
    if header_list and header_list[0].level > 1:
        _LOG.warning(
            "First header '%s' at line %s is not level 1, but %s",
            header_list[0].description,
            header_list[0].line_number,
            header_list[0].level,
        )
    # 2) All level 1 headers are unique.
    level_1_headers = [
        header.description for header in header_list if header.level == 1
    ]
    hdbg.dassert_no_duplicates(level_1_headers)
    # 3) Check that consecutive elements in the header list only increase by at
    #    most one level at a time (even if it can decrease by multiple levels).
    if len(header_list) > 1:
        for i in range(1, len(header_list)):
            hdbg.dassert_isinstance(header_list[i - 1], HeaderInfo)
            hdbg.dassert_isinstance(header_list[i], HeaderInfo)
            if header_list[i].level - header_list[i - 1].level > 1:
                msg = []
                msg.append("Consecutive headers increase by more than one level:")
                msg.append(f"  {header_list[i - 1]}")
                msg.append(f"  {header_list[i]}")
                msg = "\n".join(msg)
                raise ValueError(msg)


# TODO(gp): Move sanity check outside?
def extract_headers_from_markdown(
    txt: str, max_level: int, *, sanity_check: bool = True
) -> HeaderList:
    """
    Extract headers from Markdown file and return an `HeaderList`.

    :param txt: content of the input Markdown file.
    :param max_level: Maximum header levels to parse (e.g., 3 parses all levels
        included `###`, but not `####`)
    :param sanity_check: If True, check that the header list is valid.
    :return: the generated `HeaderList`, e.g.,
        ```
        [
            (1, "Chapter 1", 5),
            (2, "Section 1.1", 10), ...]
        ```
    """
    hdbg.dassert_isinstance(txt, str)
    hdbg.dassert_lte(1, max_level)
    header_list: HeaderList = []
    # Process the input file to extract headers.
    for line_number, line in enumerate(txt.splitlines(), start=1):
        # TODO(gp): Use the iterator.
        # Skip the visual separators.
        if is_markdown_line_separator(line):
            continue
        # Get the header level and title.
        is_header_, level, title = is_header(line)
        if is_header_ and level <= max_level:
            header_info = HeaderInfo(level, title, line_number)
            header_list.append(header_info)
    # Check the header list.
    if sanity_check:
        sanity_check_header_list(header_list)
    else:
        _LOG.debug("Skipping sanity check")
    return header_list


def header_list_to_vim_cfile(markdown_file: str, header_list: HeaderList) -> str:
    """
    Convert a list of headers into a Vim cfile format.

    Use the generated file in Vim as:
        `:cfile <output_file>`
        Use `:cnext` and `:cprev` to navigate between headers.

    :param markdown_file: Path to the input Markdown file.
    :param header_list: List of headers, where each header is a tuple containing
        the line number, level, and title.
    :return: The generated cfile content as a string in the format:
        ```
        ...
        <file path>:<line number>:<header title>
        ...
        ```
    """
    hdbg.dassert_isinstance(header_list, list)
    _LOG.debug(hprint.to_str("markdown_file header_list"))
    output_lines = [
        f"{markdown_file}:{header_info.line_number}:{header_info.description}"
        for header_info in header_list
    ]
    output_content = "\n".join(output_lines)
    return output_content


def header_list_to_markdown(header_list: HeaderList, mode: str) -> str:
    """
    Convert a list of headers into a Markdown format.

    :param header_list: List of headers, where each header is a tuple
        containing the level, title, and line number.
    :param mode: Specifies the format of the output.
        - "list": Indents headers to create a nested list.
        - "headers": Uses Markdown header syntax (e.g., #, ##, ###).
    :return: The generated Markdown content as a string.
    """
    hdbg.dassert_isinstance(header_list, list)
    _LOG.debug(hprint.to_str("header_list mode"))
    output_lines = []
    for header_info in header_list:
        level, title, line_number = header_info.as_tuple()
        _ = line_number
        if mode == "list":
            header_prefix = "  " * (level - 1) + "-"
        elif mode == "headers":
            header_prefix = "#" * level
        else:
            raise ValueError(f"Invalid mode '{mode}'")
        output_lines.append(f"{header_prefix} {title}")
    output_content = "\n".join(output_lines)
    return output_content


# #############################################################################
# Rules processing.
# #############################################################################

# Rules are organized in 4 levels of a markdown file:
#
# 1) Rule sets (level 1)
#    - E.g., `General`, `Python`, `Notebooks`, `Markdown`
#    - Level 1 is a set of rules determined mainly by the type of the file we
#      are processing
#    - Several sets of rules can be applied to a given file type
#      - E.g., rules in `Python` and `Notebooks` apply to all Python files
# 2) Sections (level 2)
#    - E.g., `Naming`, `Comments`, `Code_design`, `Imports`, `Type_annotations`
# 3) Targets (level 3)
#    - E.g., LLM vs Linter
# 4) Atomic rules (level 4)
#    - This is the set of rules that are applied to the file
#    ```
#    - Spell commands in lower case and programs with the first letter in upper case
#      - E.g., `git` as a command, `Git` as a program
#      - E.g., capitalize the first letter of `Python`
#    ```

# Extract the rules from the markdown file:
# ```
# > extract_headers_from_markdown.py -i docs/code_guidelines/all.coding_style_guidelines.reference.md --max_level 2
# - General
#   - Spelling
#     - LLM
#     - Linter
# - Python
#   - Naming
#     - LLM
#     - Linter
#   - Docstrings
#     - ...
#   - Comments
#   - Code_implementation
#   - Code_design
#   - Imports
#   - Type_annotations
#   - Functions
#   - Scripts
#   - Logging
#   - Misc
# - Unit_tests
#   - All
# - Notebooks
#   - General
#   - Plotting
#   - Jupytext
# - Markdown
#   - Naming
#   - General
# ```

# - The rules to apply to a Python file are automatically extractedas:
#   `([`General:*`, `Python:*`], `LLM`)`
# - The rules to apply to a Notebook file are automatically extracted as:
#   `([`General:*`, `Python:*`, `Notebooks:*`], `LLM`)`
# - A user can specify to apply a subset of rules like
#   `([`General:*`, `Python:Naming,Docstrings`], `LLM,Linter`)`
# - Atomic rules are the first-level bullets of the markdown file, e.g.,
#   ```
#   - Spell commands in lower case and programs with the first letter in upper case
#     - E.g., `git` as a command, `Git` as a program
#     - E.g., capitalize the first letter of `Python`
#   ```


def sanity_check_rules(txt: List[str]) -> None:
    """
    Sanity check the rules.
    """
    header_list = extract_headers_from_markdown(txt, max_level=5)
    # 1) Start with level 1 headers.
    # 2) All level 1 headers are unique.
    # 3) Header levels are increasing / decreasing by at most 1.
    sanity_check_header_list(header_list)
    # 4) Level 3 headers are always `LLM` or `Linter`.
    # for header in header_list:
    #     if header.level != 3:
    #         hdbg.dassert_in(header.description, ["LLM", "Linter"])
    # TODO(gp): Implement this.
    # 5) All headers have no spaces.
    # TODO(gp): Implement this.


# A `Rule` is a string separated by `:` characters, where each part can be:
# - `*` (which means "match any string")
# - a `string` (e.g., `Spelling`)
# - a list of strings separated by `|` (e.g., `LLM|Linter`)
#
# E.g., valid rules are:
# - `General:*:LLM`, `*:*:Linter|LLM`, `General|Python:*:LLM`, `Python:*:Linter`
# - For a Python file -> `General|Python:*:LLM`
# - For a Notebook file -> `General|Python|Notebooks:*:LLM`
# - `Python:Naming|Docstrings|Comments:LLM`
SelectionRule = str


# A `Guidelines`` is a header list with only level 1 headers storing the full
# hierarchy of the rules as a description, e.g.,
# `(1, "Spelling:All:LLM", xyz)`
# TODO(gp): Make Guidelines descend from HeaderList.
Guidelines = HeaderList


def convert_header_list_into_guidelines(header_list: HeaderList) -> Guidelines:
    """
    Convert the header list into a `Guidelines` object with only level 1 headers
    and full hierarchy of the rules as description.

    Expand a header list like:
    ```
    - General
      - Spelling
        - LLM
        - Linter
    - Python
      - Naming
        - LLM
        - Linter
    ```
    represented internally as:
    ```
        (1, "General", xyz),
        (2, "Spelling", xyz),
        (3, "LLM", xyz),
        (3, "Linter", xyz),
        (1, "Python", xyz),
        (2, "Naming", xyz),
        (3, "LLM", xyz),
        (3, "Linter", xyz),
    ```
    into:
    ```
    [
        (1, "Spelling:All:LLM", xyz),
        (1, "Spelling:All:Linter", xyz),
        (1, "Python:Naming:LLM", xyz),
        (1, "Python:Naming:Linter", xyz),
    ]
    ```
    """
    hdbg.dassert_isinstance(header_list, list)
    # Store the last level headers.
    level_1 = ""
    level_2 = ""
    # Accumulate the last level headers.
    level_3_headers = []
    # Scan the header list.
    for header_info in header_list:
        level, description, line_number = header_info.as_tuple()
        # Store the headers found at each level.
        if level == 1:
            level_1 = description
        elif level == 2:
            level_2 = description
        elif level == 3:
            # Store the level 3 header.
            hdbg.dassert_ne(level_1, "")
            hdbg.dassert_ne(level_2, "")
            full_level_3 = f"{level_1}:{level_2}:{description}"
            header_info_tmp = HeaderInfo(1, full_level_3, line_number)
            level_3_headers.append(header_info_tmp)
        else:
            raise ValueError(f"Invalid header info={header_info}")
    return level_3_headers


def _convert_rule_into_regex(selection_rule: SelectionRule) -> str:
    """
    Convert a rule into an actual regular expression.

    E.g., 
    - `Spelling:*:LLM` -> `Spelling:(\S*):LLM`
    - `*:*:Linter|LLM` -> `(\S*):(\S*):(Linter|LLM)`
    - `Spelling|Python:*:LLM` -> `Spelling|Python:(\S*):LLM`
    - `Python:*:Linter` -> `Python:(\S*):Linter`
    """
    hdbg.dassert_isinstance(selection_rule, SelectionRule)
    # Parse the rule into tokens.
    selection_rule_parts = selection_rule.split(":")
    hdbg.dassert_eq(len(selection_rule_parts), 3)
    # Process each part of the rule regex.
    rule_parts_out = []
    for rule_part_in in selection_rule_parts:
        hdbg.dassert_not_in(" ", rule_part_in)
        if rule_part_in == "*":
            # Convert `*` into `\S*`.
            rule_part_out = "(\S*)"
        elif "|" in rule_part_in:
            # Convert `LLM|Linter` into `(LLM|Linter)`.
            rule_part_out = "(" + rule_part_in + ")"
        else:
            # Keep the string as is.
            rule_part_out = rule_part_in
        rule_parts_out.append(rule_part_out)
    # Join the parts of the rule back together.
    rule_out = ":".join(rule_parts_out)
    return rule_out


def extract_rules(guidelines: Guidelines, selection_rules: List[SelectionRule]) -> Guidelines:
    """
    Extract the set of rules from the `guidelines` that match the rule regex.

    :param guidelines: The guidelines to extract the rules from.
    :param selection_rules: The selection rules to use to extract the rules.
    :return: The extracted rules.
    """
    hdbg.dassert_isinstance(guidelines, list)
    hdbg.dassert_isinstance(selection_rules, list)
    # A rule regex is a string separated by `:` characters, where each part is
    # - `*` (meaning "any string")
    # - a `string` (e.g., `Spelling`)
    # - a list of strings separated by `|` (e.g., `LLM|Linter`)
    # E.g., `Spelling:*:LLM`, `*:*:Linter|LLM`, `Spelling|Python:*:LLM`.
    # Convert each rule regex into a regular expression.
    rule_regex_map = {}
    for rule_regex_str in selection_rules:
        hdbg.dassert_isinstance(rule_regex_str, SelectionRule)
        regex = _convert_rule_into_regex(rule_regex_str)
        _LOG.debug(hprint.to_str("rule_regex_str regex"))
        hdbg.dassert_not_in(rule_regex_str, rule_regex_map)
        rule_regex_map[rule_regex_str] = regex
    # Extract the set of rules from the `guidelines` that match the rule regex.
    rule_sections = []
    for guideline in guidelines:
        # A guideline description is a string separated by `:` characters, where each part is
        # (1, "Python:Naming:Linter", xyz),
        for k, v in rule_regex_map.items():
            if re.match(v, guideline.description):
                _LOG.debug("%s matches %s", k, guideline.description)
                if guideline not in rule_sections:
                    rule_sections.append(guideline)
    # Select the rules.
    _LOG.debug("Selected %s sections:\n%s", len(rule_sections), "\n".join([r.description for r in rule_sections]))
    return rule_sections


def parse_rules_from_txt(txt: str) -> List[str]:
    """
    Parse rules from a chunk of markdown text.

    - Extract first-level bullet point list items from text until the next one.
    - Sub-lists nested under first-level items are extracted together with the
      first-level items. 

    :param txt: text to process
        ```
        - Item 1
        - Item 2
           - Item 3
        - Item 4
        ```
    :return: extracted bullet points, e.g.,
        ```
        [
            "- Item 1",
            '''
            - Item 2
               - Item 3
            ''',
            "- Item 4",
        ]
        ```
    """
    lines = txt.split("\n")
    # Store the first-level bullet points.
    bullet_points = []
    # Store the current item including the first level bullet point and all
    # its sub-items.
    current_item = ""
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
        if re.match(r"^- ", line):
            # Match first-level bullet point item.
            if current_item:
                # Store the previous item, if any.
                bullet_points.append(current_item)
            # Start a new first-level bullet point item.
            current_item = line
        elif re.match(r"^\s+- ", line):
            # Match a sub-item (non first-level bullet point item).
            # Append a sub-item to the current item.
            current_item += "\n" + line
        elif len(line.strip()) != 0 and current_item:
            # Append a line to the current item.
            current_item += "\n" + line
    # Add the last item if there is one.
    if current_item:
        bullet_points.append(current_item)
    return bullet_points


# #############################################################################
# Process headers.
# #############################################################################


def format_headers(in_file_name: str, out_file_name: str, max_lev: int) -> None:
    """
    Format the headers in the input file and write the formatted text to the
    output file.

    :param in_file_name: The name of the input file to read
    :param out_file_name: The name of the output file to write the
        formatted text to
    :param max_lev: The maximum level of headings to include in the
        formatted text
    """
    txt = hparser.read_file(in_file_name)
    #
    for line in txt:
        m = re.search(r"max_level=(\d+)", line)
        if m:
            max_lev = int(m.group(1))
            _LOG.warning("Inferred max_level=%s", max_lev)
            break
    hdbg.dassert_lte(1, max_lev)
    # Remove all headings.
    txt_tmp = []
    for line in txt:
        # Keep the comments.
        if not is_markdown_line_separator(line):
            txt_tmp.append(line)
    txt = txt_tmp[:]
    # Add proper heading of the correct length.
    txt_tmp = []
    for line in txt:
        # Keep comments.
        found = False
        for i in range(1, max_lev + 1):
            if line.startswith("#" * i + " "):
                row = "#" * i + " " + "#" * (79 - 1 - i)
                txt_tmp.append(row)
                txt_tmp.append(line)
                txt_tmp.append(row)
                found = True
        if not found:
            txt_tmp.append(line)
    # TODO(gp): Remove all empty lines after a heading.
    # TODO(gp): Format title (first line capital and then small).
    hparser.write_file(txt_tmp, out_file_name)


def modify_header_level(in_file_name: str, out_file_name: str, mode: str) -> None:
    """
    Increase or decrease the level of headings by one for text in stdin.

    :param in_file_name: the name of the input file to read
    :param out_file_name: the name of the output file to write the
        modified text to
    :param mode: indicates the increase or decrease of the header level
    """
    txt = hparser.read_file(in_file_name)
    #
    txt_tmp = []
    if mode == "increase":
        mode_level = 1
    elif mode == "decrease":
        mode_level = -1
    else:
        raise ValueError(f"Unsupported mode='{mode}'")
    for line in txt:
        # TODO(gp): Use the iterator.
        line = line.rstrip(r"\n")
        is_header_, level, title = is_header(line)
        if is_header_:
            modified_level = level + mode_level
            if (mode_level == 1 and level > 4) or (
                mode_level == -1 and level == 1
            ):
                # Handle edge cases for reducing (1 hash) and increasing (5 hashes)
                # heading levels.
                modified_level = level
            line = "#" * modified_level + " " + title
        txt_tmp.append(line)
    #
    hparser.write_file(txt_tmp, out_file_name)


# #############################################################################
# _HeaderTreeNode
# #############################################################################


# This is a different representation of the data than the one in `HeaderList`
# because it is a tree structure. So we use a different type hint.
_HeaderTree = List[HeaderInfo]


def build_header_tree(header_list: HeaderList) -> _HeaderTree:
    """
    Build a tree (list of Node objects) from the flat list.

    We assume that the level changes never jump by more than 1.
    """
    tree: _HeaderTree = []
    stack: _HeaderTree = []
    for node in header_list:
        if node.level == 1:
            tree.append(node)
            stack = [node]
        else:
            # Pop until we find the proper parent: one with level < current
            # level.
            while stack and stack[-1].level >= node.level:
                stack.pop()
            if stack:
                stack[-1].children.append(node)
            else:
                tree.append(node)
            stack.append(node)
    # hdbg.dassert_eq(len(header_list), len(tree))
    # hdbg.dassert_eq(len(stack), 0)
    return tree


def _find_header_tree_ancestry(
    tree: _HeaderTree, level: int, description: str
) -> Optional[_HeaderTree]:
    """
    Recursively search for the node matching (level, description).

    If found, return the ancestry as a list from the root down to that
    node. Otherwise return None.
    """
    for node in tree:
        if node.level == level and node.description == description:
            return [node]
        result = _find_header_tree_ancestry(node.children, level, description)
        if result:
            return [node] + result
    return None


def header_tree_to_str(
    tree: _HeaderTree,
    ancestry: Optional[_HeaderTree],
    *,
    open_modifier: str = "**",
    close_modifier: str = "**",
    indent: int = 0,
) -> str:
    """
    Return the tree as a string.

    Only expand (i.e. recursively include children) for a node if it is part of
    the ancestry of the selected node.

    :param tree: The tree to convert to a string.
    :param ancestry: The ancestry of the selected node.
    :param open_modifier: The modifier to use for the open of the selected node.
    :param close_modifier: The modifier to use for the close of the selected node.
    :param indent: The indent of the tree.

    - Nodes not in the ancestry are included on one line (even if they have
      children).
    - The selected node (last in the ancestry) is included highlighted.
    """
    prefix = "  " * indent + "- "
    result = []
    for node in tree:
        _LOG.debug(hprint.to_str("node"))
        # Check if this node is the next expected one in the ancestry branch.
        if ancestry and node is ancestry[0]:
            # If this is the last in the ancestry, it is the selected node.
            val = prefix
            if len(ancestry) == 1:
                val += open_modifier + node.description + close_modifier
            else:
                val += node.description
            _LOG.debug("-> %s", hprint.to_str("val"))
            if val:
                result.append(val)
            # Expand this node’s children using the rest of the ancestry.
            val = header_tree_to_str(
                node.children,
                ancestry[1:],
                indent=indent + 1,
                open_modifier=open_modifier,
                close_modifier=close_modifier,
            )
        else:
            # For nodes not on the selected branch, include them without
            # expanding.
            val = prefix + node.description
        _LOG.debug("-> %s", hprint.to_str("val"))
        if val:
            result.append(val)
    return "\n".join(result)


def selected_navigation_to_str(
    tree: _HeaderTree,
    level: int,
    description: str,
    *,
    open_modifier: str = "**",
    close_modifier: str = "**",
) -> str:
    """
    Given a level and description for the selected node, print the navigation.
    """
    ancestry = _find_header_tree_ancestry(tree, level, description)
    hdbg.dassert_ne(
        ancestry,
        None,
        "Node (%s, '%s') not found",
        level,
        description,
    )
    _LOG.debug(hprint.to_str("ancestry"))
    txt = header_tree_to_str(
        tree, ancestry, open_modifier=open_modifier, close_modifier=close_modifier
    )
    return txt


# #############################################################################


def inject_todos_from_cfile(
    cfile_txt: str, todo_user: str, comment_prefix: str
) -> None:
    """
    Inject the TODOs from a cfile in the corresponding files.

    Given a cfile with the following content:
    ```
    dev_scripts_helpers/github/dockerized_sync_gh_repo_settings.py:101: The logic ...
    ```
    the function will inject the TODO in the corresponding file and line

    :param cfile_txt: The content of the cfile.
    :param todo_user: The user to use in the TODO.
    :param comment_prefix: The prefix to use for the comment (e.g., "#")
    """
    # For each file, store
    #   - the current file content
    #   - the offset (i.e., how many lines we inserted in the file so far, so
    #     we can inject the TODO at the correct line number)
    #   - the index of the last line modified to make sure the TODOs are for
    #     increasing line numbers.
    file_content = {}
    for todo_line in cfile_txt.split("\n"):
        _LOG.debug("\n%s", hprint.frame("todo line='%s'" % todo_line))
        if todo_line.strip() == "":
            continue
        # dev_scripts_helpers/github/dockerized_sync_gh_repo_settings.py:101: The logic for extracting required status checks and pull request reviews is repeated. Consider creating a helper function to handle this extraction to reduce redundancy.
        m = re.match(r"^\s*(\S+):(\d+):\s*(.*)$", todo_line)
        if not m:
            _LOG.warning("Can't parse line='%s': skipping", todo_line)
            continue
        file_name, todo_line_number, todo = m.groups()
        todo_line_number = int(todo_line_number)
        _LOG.debug(hprint.to_str("file_name todo_line_number todo"))
        # Update the state if needed.
        if file_name not in file_content:
            _LOG.debug("Reading %s", file_name)
            hdbg.dassert_path_exists(file_name)
            txt = hio.from_file(file_name).split("\n")
            offset = 0
            last_line_modified = 0
            file_content[file_name] = (txt, offset, last_line_modified)
        # Extract the info for the file to process.
        txt, offset, last_line_modified = file_content[file_name]
        _LOG.debug(hprint.to_str("offset last_line_modified"))
        hdbg.dassert_lt(
            last_line_modified,
            todo_line_number,
            "The TODOs don't look like they are increasing line numbers: "
            "TODO at line %d is before the last line modified %d",
            todo_line_number,
            last_line_modified,
        )
        # We subtract 1 from the line number since TODOs count from 1, while
        # Python arrays count from 0.
        act_line_number = todo_line_number - 1 + offset
        hdbg.dassert_lte(0, act_line_number)
        hdbg.dassert_lt(act_line_number, len(txt))
        insert_line = txt[act_line_number]
        _LOG.debug(hprint.to_str("act_line_number insert_line"))
        # Extract how many spaces there are at place where the line to insert
        # the TODO.
        m = re.match(r"^(\s*)\S", insert_line)
        hdbg.dassert(m, "Can't parse insert_line='%s'", insert_line)
        spaces = len(m.group(1)) * " "
        # Build the new line to insert.
        new_line = spaces + f"{comment_prefix} TODO({todo_user}): {todo}"
        _LOG.debug(hprint.to_str("new_line"))
        # Insert the new line in txt at the correct position.
        txt = txt[:act_line_number] + [new_line] + txt[act_line_number:]
        # Update the state.
        offset += 1
        file_content[file_name] = (txt, offset, todo_line_number)
    # Write updated files back.
    for file_name, (txt, offset, last_line_modified) in file_content.items():
        _ = last_line_modified
        _LOG.info("Writing %d lines in %s", offset, file_name)
        txt = "\n".join(txt)
        hio.to_file(file_name, txt)


# #############################################################################
# Formatting markdown
# #############################################################################


def capitalize_first_level_bullets(markdown_text: str) -> str:
    """
    Make first-level bullets bold in markdown text.

    :param markdown_text: Input markdown text
    :return: Formatted markdown text with first-level bullets in bold
    """
    # **Subject-Matter Experts (SMEs)** -> **Subject-Matter Experts (SMEs)**
    # Business Strategists -> Business strategists
    # Establish a Phased, Collaborative Approach -> Establish a phased, collaborative approach
    lines = markdown_text.split("\n")
    result = []
    for line in lines:
        # Check if this is a first-level bullet point.
        if re.match(r"^\s*- ", line):
            # Check if the line has bold text it in it.
            if not re.search(r"\*\*", line):
                # Bold first-level bullets.
                indentation = len(line) - len(line.lstrip())
                if indentation == 0:
                    # First-level bullet, add bold markers.
                    line = re.sub(r"^(\s*-\s+)(.*)", r"\1**\2**", line)
            result.append(line)
        else:
            result.append(line)
    return "\n".join(result)


# These are the colors that are supported by Latex / markdown, are readable on
# white, and form an equidistant color palette.
_ALL_COLORS = [
    "red",
    "orange",
    "brown",
    "olive",
    "green",
    "teal",
    "cyan",
    "blue",
    "violet",
    "darkgray",
    "gray",
]


def bold_first_level_bullets(markdown_text: str, *, max_length: int = 30) -> str:
    """
    Make first-level bullets bold in markdown text.

    :param markdown_text: Input markdown text
    :param max_length: Max length of the bullet text to be bolded. -1
        means no limit.
    :return: Formatted markdown text with first-level bullets in bold
    """
    lines = markdown_text.split("\n")
    result = []
    for line in lines:
        # Check if this is a first-level bullet point.
        if re.match(r"^\s*- ", line):
            # Check if the line has already bold text it in it.
            if not re.search(r"\*\*", line):
                # Bold first-level bullets.
                indentation = len(line) - len(line.lstrip())
                if indentation == 0:
                    # First-level bullet, add bold markers.
                    m = re.match(r"^(\s*-\s+)(.*)", line)
                    hdbg.dassert(m, "Can't parse line='%s'", line)
                    bullet_text = m.group(2)
                    if max_length > -1 and len(bullet_text) <= max_length:
                        line = m.group(1) + "**" + bullet_text + "**"
        result.append(line)
    return "\n".join(result)


def colorize_bold_text(
    markdown_text: str, *, use_abbreviations: bool = True
) -> str:
    r"""
    Add colors to bold text in markdown using equidistant colors from an array.

    The function finds all bold text (enclosed in ** or __) and adds
    LaTeX color commands while preserving the rest of the markdown
    unchanged.

    :param markdown_text: Input markdown text
    :param use_abbreviations: Use LaTeX abbreviations for colors,
        `\red{text}` instead of `\textcolor{red}{text}`
    :return: Markdown text with colored bold sections
    """
    # Remove any existing color formatting.
    # Remove \color{text} format.
    markdown_text = re.sub(r"\\[a-z]+\{([^}]+)\}", r"\1", markdown_text)
    # Remove \textcolor{color}{text} format.
    markdown_text = re.sub(
        r"\\textcolor\{[^}]+\}\{([^}]+)\}", r"\1", markdown_text
    )
    # Find all bold text (both ** and __ formats).
    bold_pattern = r"\*\*(.*?)\*\*|__(.*?)__"
    # matches will look like:
    # For **text**: group(1)='text', group(2)=None.
    # For __text__: group(1)=None, group(2)='text'.
    matches = list(re.finditer(bold_pattern, markdown_text))
    if not matches:
        return markdown_text
    result = markdown_text
    # Calculate color spacing to use equidistant colors.
    color_step = len(_ALL_COLORS) / len(matches)
    # Process matches in reverse to not mess up string indices.
    for i, match in enumerate(reversed(matches)):
        # Get the matched bold text (either ** or __ format).
        bold_text = match.group(1) or match.group(2)
        # Calculate `color_idx` using equidistant spacing.
        color_idx = int((len(matches) - 1 - i) * color_step) % len(_ALL_COLORS)
        color = _ALL_COLORS[color_idx]
        # Create the colored version.
        if use_abbreviations:
            # E.g., \red{text}
            colored_text = f"\\{color}{{{bold_text}}}"
        else:
            # E.g., \textcolor{red}{text}
            colored_text = f"\\textcolor{{{color}}}{{{bold_text}}}"
        # Apply bold.
        colored_text = f"**{colored_text}**"
        # Replace in the original text.
        result = result[: match.start()] + colored_text + result[match.end() :]
    return result


def format_first_level_bullets(markdown_text: str) -> str:
    """
    Add empty lines only before first level bullets and remove all empty lines
    from markdown text.

    :param markdown_text: Input markdown text
    :return: Formatted markdown text
    """
    # Split into lines and remove empty ones.
    lines = [line for line in markdown_text.split("\n") if line.strip()]
    # Add empty lines only before first level bullets.
    result = []
    for i, line in enumerate(lines):
        # Check if current line is a first level bullet (no indentation).
        if re.match(r"^- ", line):
            # Add empty line before first level bullet if not at start.
            if i > 0:
                result.append("")
        result.append(line)
    return "\n".join(result)


def remove_empty_lines_from_markdown(markdown_text: str) -> str:
    """
    Remove all empty lines from markdown text.

    :param markdown_text: Input markdown text
    :return: Formatted markdown text
    """
    # Split into lines and remove empty ones.
    result = [line for line in markdown_text.split("\n") if line.strip()]
    return "\n".join(result)


def prettier_markdown(txt: str) -> str:
    """
    Format markdown text using `prettier`.
    """
    file_type = "md"
    txt = dshdlino.prettier_on_str(txt, file_type)
    return txt


def format_markdown(txt: str) -> str:
    """
    Format markdown text.
    """
    file_type = "md"
    txt = dshdlino.prettier_on_str(txt, file_type)
    txt = remove_empty_lines_from_markdown(txt)
    return txt


def format_markdown_slide(txt: str) -> str:
    """
    Format markdown text for a slide.
    """
    # Split the text into title and body.
    txt = bold_first_level_bullets(txt)
    file_type = "md"
    txt = dshdlino.prettier_on_str(txt, file_type)
    txt = format_first_level_bullets(txt)
    # txt = capitalize_slide_titles(txt)
    return txt


def format_latex(txt: str) -> str:
    file_type = "tex"
    txt = dshdlino.prettier_on_str(txt, file_type)
    return txt
