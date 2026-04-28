import helpers.hunit_test as hunitest
import linters.amp_lint_md as lamlimd


class Test_check_repo_names_are_backticked(hunitest.TestCase):
    def test1(self) -> None:
        """
        Bare repo names are reported.
        """
        file_name = self.get_scratch_space() + "/test.md"
        self.write_file(file_name, "Use //cmamp in examples.\n")
        actual = lamlimd._check_repo_names_are_backticked(file_name)
        expected = [
            f"{file_name}:1: Repo name '//cmamp' should be wrapped in backticks"
        ]
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Backticked repo names are accepted.
        """
        file_name = self.get_scratch_space() + "/test.md"
        self.write_file(file_name, "Use `//cmamp` in examples.\n")
        actual = lamlimd._check_repo_names_are_backticked(file_name)
        self.assertEqual(actual, [])

    def test3(self) -> None:
        """
        URLs are not treated as repo names.
        """
        file_name = self.get_scratch_space() + "/test.md"
        self.write_file(file_name, "See https://github.com/causify-ai/helpers.\n")
        actual = lamlimd._check_repo_names_are_backticked(file_name)
        self.assertEqual(actual, [])


class Test_check_readme_is_capitalized(hunitest.TestCase):
    def test1(self) -> None:
        """
        Incorrect README name: error.
        """
        file_name = "linter/readme.md"
        expected = f"{file_name}:1: All README files should be named README.md"
        msg = lamlimd._check_readme_is_capitalized(file_name)
        self.assertEqual(expected, msg)

    def test2(self) -> None:
        """
        Correct README name: no error.
        """
        file_name = "linter/README.md"
        msg = lamlimd._check_readme_is_capitalized(file_name)
        self.assertEqual("", msg)
