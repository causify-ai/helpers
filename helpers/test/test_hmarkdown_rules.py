import logging
from typing import List, Tuple, cast

import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


def _to_header_list(data: List[Tuple[int, str]]) -> hmarkdo.HeaderList:
    res = [
        hmarkdo.HeaderInfo(level, text, 5 * i + 1)
        for i, (level, text) in enumerate(data)
    ]
    return res


def get_header_list6() -> hmarkdo.HeaderList:
    """
    - Spelling
      - All
        - LLM
        - Linter
    - Python
      - Naming
        - LLM
        - Linter
      - Docstrings
        - LLM
        - Linter
    - Unit_tests
      - All
        - LLM
        - Linter
    """
    data = [
        (1, "Spelling"),
        (2, "All"),
        (3, "LLM"),
        (3, "Linter"),
        (1, "Python"),
        (2, "Naming"),
        (3, "LLM"),
        (3, "Linter"),
        (2, "Docstrings"),
        (3, "LLM"),
        (3, "Linter"),
        (1, "Unit_tests"),
        (2, "All"),
        (3, "LLM"),
        (3, "Linter"),
    ]
    header_list = _to_header_list(data)
    return header_list


def get_guidelines_txt1() -> str:
    txt = r"""
    # General

    ## Spelling

    ### LLM

    ### Linter

    - Spell commands in lower case and programs with the first letter in upper case
    - E.g., `git` as a command, `Git` as a program
    - E.g., capitalize the first letter of `Python`
    - Capitalize `JSON`, `CSV`, `DB` and other abbreviations

    # Python

    ## Naming

    ### LLM

    - Name functions using verbs and verbs/actions
      - Good: `download_data()`, `process_input()`, `calculate_sum()`
      - Good: Python internal functions as `__repr__`, `__init__` are valid
      - Good: Functions names like `to_dict()`, `_parse()`, `_main()` are valid
    - Name classes using nouns
      - Good: `Downloader()`, `DataProcessor()`, `User()`
      - Bad: `DownloadStuff()`, `ProcessData()`, `UserActions()`

    ### Linter

    - Name executable Python scripts using verbs and actions
    - E.g., `download.py` and not `downloader.py`

    # Unit_tests

    ## Rules

    ### LLM

    - A test class should test only one function or class to help understanding
      test failures
    - A test method should only test a single case to ensures clarity and
      precision in testing
    - E.g., "for these inputs the function responds with this output"
    """
    txt = hprint.dedent(txt)
    txt = cast(str, txt)
    return txt


# #############################################################################
# Test_convert_header_list_into_guidelines1
# #############################################################################


class Test_convert_header_list_into_guidelines1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test converting a header list into guidelines.
        """
        # Prepare inputs.
        header_list = get_header_list6()
        # Call function.
        guidelines = hmarkdo.convert_header_list_into_guidelines(header_list)
        # Check output.
        act = "\n".join(map(str, guidelines))
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        HeaderInfo(1, 'Spelling:All:Linter', 16)
        HeaderInfo(1, 'Python:Naming:LLM', 31)
        HeaderInfo(1, 'Python:Naming:Linter', 36)
        HeaderInfo(1, 'Python:Docstrings:LLM', 46)
        HeaderInfo(1, 'Python:Docstrings:Linter', 51)
        HeaderInfo(1, 'Unit_tests:All:LLM', 66)
        HeaderInfo(1, 'Unit_tests:All:Linter', 71)
        """
        self.assert_equal(act, exp, dedent=True)


# #############################################################################
# Test_extract_rules1
# #############################################################################


class Test_extract_rules1(hunitest.TestCase):
    def helper(self, selection_rules: List[str], exp: str) -> None:
        """
        Test extracting rules from a markdown file.
        """
        # Prepare inputs.
        guidelines = get_header_list6()
        guidelines = hmarkdo.convert_header_list_into_guidelines(guidelines)
        # Call function.
        selected_guidelines = hmarkdo.extract_rules(guidelines, selection_rules)
        # Check output.
        act = "\n".join(map(str, selected_guidelines))
        self.assert_equal(act, exp, dedent=True)

    def test1(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:*:LLM"]
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        """
        self.helper(selection_rules, exp)

    def test2(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:NONE:LLM"]
        exp = """
        """
        self.helper(selection_rules, exp)

    def test3(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:All:*"]
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        HeaderInfo(1, 'Spelling:All:Linter', 16)
        """
        self.helper(selection_rules, exp)

    def test4(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["Spelling:All:*", "Python:*:*"]
        exp = """
        HeaderInfo(1, 'Spelling:All:LLM', 11)
        HeaderInfo(1, 'Spelling:All:Linter', 16)
        HeaderInfo(1, 'Python:Naming:LLM', 31)
        HeaderInfo(1, 'Python:Naming:Linter', 36)
        HeaderInfo(1, 'Python:Docstrings:LLM', 46)
        HeaderInfo(1, 'Python:Docstrings:Linter', 51)
        """
        self.helper(selection_rules, exp)


# #############################################################################
# Test_parse_rules_from_txt1
# #############################################################################


class Test_parse_rules_from_txt1(hunitest.TestCase):
    def helper(self, text: str, expected: List[str]) -> None:
        # Prepare inputs.
        text = hprint.dedent(text)
        # Call function.
        actual = hmarkdo.parse_rules_from_txt(text)
        # Check output.
        act = str(actual)
        expected = str(expected)
        self.assert_equal(act, expected, dedent=True)

    def test_basic_list1(self) -> None:
        """
        Test extracting simple first-level bullet points.
        """
        text = """
        - Item 1
        - Item 2
        - Item 3
        """
        expected = ['- Item 1', '- Item 2', '- Item 3']
        self.helper(text, expected)

    def test_nested_list1(self) -> None:
        """
        Test extracting bullet points with nested sub-items.
        """
        text = """
        - Item 1
        - Item 2
          - Sub-item 2.1
          - Sub-item 2.2
        - Item 3
        """
        expected = ['- Item 1', '- Item 2\n  - Sub-item 2.1\n  - Sub-item 2.2', '- Item 3']
        self.helper(text, expected)

    def test_empty_list1(self) -> None:
        """
        Test handling empty input.
        """
        text = ""
        expected = []
        self.helper(text, expected)


# #############################################################################
# Test_end_to_end_rules1
# #############################################################################


class Test_end_to_end_rules1(hunitest.TestCase):
    def test_get_header_list1(self) -> None:
        """
        Test extracting headers from a markdown file.
        """
        # Prepare inputs.
        txt = get_guidelines_txt1()
        max_level = 4
        # Run function.
        header_list = hmarkdo.extract_headers_from_markdown(txt, max_level)
        # Check output.
        act = "\n".join(map(str, header_list))
        exp = """
        HeaderInfo(1, 'General', 1)
        HeaderInfo(2, 'Spelling', 3)
        HeaderInfo(3, 'LLM', 5)
        HeaderInfo(3, 'Linter', 7)
        HeaderInfo(1, 'Python', 14)
        HeaderInfo(2, 'Naming', 16)
        HeaderInfo(3, 'LLM', 18)
        HeaderInfo(3, 'Linter', 28)
        HeaderInfo(1, 'Unit_tests', 33)
        HeaderInfo(2, 'Rules', 35)
        HeaderInfo(3, 'LLM', 37)
        """
        self.assert_equal(act, exp, dedent=True)
        # Run function.
        guidelines = hmarkdo.convert_header_list_into_guidelines(header_list)
        # Check output.
        act = "\n".join(map(str, guidelines))
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Python:Naming:Linter', 28)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.assert_equal(act, exp, dedent=True)

    def helper_extract_rules(self, selection_rules: List[str], exp: str) -> None:
        """
        Helper function to test extracting rules from a markdown file.
        """
        # Prepare inputs.
        txt = get_guidelines_txt1()
        max_level = 4
        header_list = hmarkdo.extract_headers_from_markdown(txt, max_level)
        guidelines = hmarkdo.convert_header_list_into_guidelines(header_list)
        # Call function.
        selected_guidelines = hmarkdo.extract_rules(guidelines, selection_rules)
        # Check output.
        act = "\n".join(map(str, selected_guidelines))
        self.assert_equal(act, exp, dedent=True)

    def test_extract_rules1(self) -> None:
        """
        Test extracting rules from a markdown file.
        """
        selection_rules = ["General:*:LLM"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules2(self) -> None:
        selection_rules = ["General:NONE:LLM"]
        exp = """
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules3(self) -> None:
        selection_rules = ["*:*:LLM"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules4(self) -> None:
        selection_rules = ["*:*:LLM", "General:*:*"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules5(self) -> None:
        selection_rules = ["*:*:*"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Python:Naming:Linter', 28)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)

    def test_extract_rules6(self) -> None:
        selection_rules = ["*:*:*", "General:*:*"]
        exp = """
        HeaderInfo(1, 'General:Spelling:LLM', 5)
        HeaderInfo(1, 'General:Spelling:Linter', 7)
        HeaderInfo(1, 'Python:Naming:LLM', 18)
        HeaderInfo(1, 'Python:Naming:Linter', 28)
        HeaderInfo(1, 'Unit_tests:Rules:LLM', 37)
        """
        self.helper_extract_rules(selection_rules, exp)
