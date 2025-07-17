"""
Import as:

import helpers.hmarkdown as hmarkdo
"""

import logging
import re
from typing import Dict, List

import helpers.hdbg as hdbg
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# TODO(gp): Add a decorator like in hprint to process both strings and lists
#  of strings.

# #############################################################################
# Rules processing.
# #############################################################################

# TODO(gp): -> hmarkdown_rules.py

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
    txt_tmp = "\n".join(txt)
    header_list = extract_headers_from_markdown(txt_tmp, max_level=5)
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
# Use `from ... import` to avoid potential import cycles.
# TODO(gp): Can we do `import helpers.hmarkdown_headers as ...` without
# creating problems?
from helpers.hmarkdown_headers import HeaderList, HeaderInfo

Guidelines = HeaderList


def convert_header_list_into_guidelines(
    header_list: HeaderList,
) -> Guidelines:
    """
    Convert the header list into a `Guidelines` object with only level 1
    headers and full hierarchy of the rules as description.

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
    r"""
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
            rule_part_out = r"(\S*)"
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


def extract_rules(
    guidelines: Guidelines, selection_rules: List[SelectionRule]
) -> Guidelines:
    """
    Extract the set of rules from the `guidelines` that match the rule regex.

    :param guidelines: The guidelines to extract the rules from.
    :param selection_rules: The selection rules to use to extract the
        rules.
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
    rule_regex_map: Dict[str, str] = {}
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
    _LOG.debug(
        "Selected %s sections:\n%s",
        len(rule_sections),
        "\n".join([r.description for r in rule_sections]),
    )
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


def extract_rules_from_section(txt: str, line_number: int) -> List[str]:
    """
    Extract rules from a section of a markdown file.

    :param txt: The markdown text to extract the rules from.
    :param line_number: The line number of the section to start
        extracting the rules from.
    :return: The extracted rules.
    """
    # Find the line number of the next header.
    i = line_number
    while True:
        hdbg.dassert_lt(i, len(txt))
        line = txt[i]
        if line.startswith("#"):
            break
        i += 1
    # Parse the markdown text into a list of bullet points.
    bullet_points = parse_rules_from_txt(txt)
    # Extract the rules from the bullet points.
    rules = []
    for bullet_point in bullet_points:
        rules.append(bullet_point)
    return rules
