import helpers.hunit_test as hunitest
import linters.amp_lint_md as lamlimd


class Test_check_readme_is_capitalized(hunitest.TestCase):
    def test1(self) -> None:
        """
        Incorrect README name: error.
        """
        file_name = "linter/readme.md"
        exp = f"{file_name}:1: All README files should be named README.md"
        msg = lamlimd._check_readme_is_capitalized(file_name)
        self.assertEqual(exp, msg)

    def test2(self) -> None:
        """
        Correct README name: no error.
        """
        file_name = "linter/README.md"
        msg = lamlimd._check_readme_is_capitalized(file_name)
        self.assertEqual("", msg)
