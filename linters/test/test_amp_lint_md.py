import helpers.hunit_test as hunitest
import linters.amp_lint_md as lamlimd


class Test_check_readme_is_capitalized(hunitest.TestCase):
    def test1(self) -> None:
        """
        Incorrect README name: error.
        """
        # Prepare inputs.
        file_name = "linter/readme.md"
        # Prepare outputs.
        expected = f"{file_name}:1: All README files should be named README.md"
        # Run test.
        msg = lamlimd._check_readme_is_capitalized(file_name)
        # Check outputs.
        self.assert_equal(expected, msg)

    def test2(self) -> None:
        """
        Correct README name: no error.
        """
        # Prepare inputs.
        file_name = "linter/README.md"
        # Prepare outputs.
        expected = ""
        # Run test.
        msg = lamlimd._check_readme_is_capitalized(file_name)
        # Check outputs.
        self.assert_equal(expected, msg)


class Test_check_repo_name_has_backticks(hunitest.TestCase):
    """
    Test Markdown repo-name backtick checks.
    """

    def helper(self, line: str, expected: str) -> None:
        """
        Test helper for `_check_repo_name_has_backticks()`.

        :param line: Markdown line to check
        :param expected: expected warning
        """
        # Prepare inputs.
        file_name = "docs/test.md"
        line_num = 3
        # Run test.
        actual = lamlimd._check_repo_name_has_backticks(
            file_name, line_num, line
        )
        # Check outputs.
        self.assert_equal(expected, actual)

    def test1(self) -> None:
        """
        Warn when a repo name is not enclosed in backticks.
        """
        # Prepare inputs.
        line = "Use //helpers as a submodule."
        # Prepare outputs.
        expected = (
            "docs/test.md:3: Repo name //helpers should be enclosed in "
            "backticks"
        )
        # Run test.
        self.helper(line, expected)

    def test2(self) -> None:
        """
        Do not warn when a repo name is enclosed in backticks.
        """
        # Prepare inputs.
        line = "Use `//helpers` as a submodule."
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(line, expected)

    def test3(self) -> None:
        """
        Do not warn for URLs.
        """
        # Prepare inputs.
        line = "See https://github.com/causify-ai/helpers."
        # Prepare outputs.
        expected = ""
        # Run test.
        self.helper(line, expected)
