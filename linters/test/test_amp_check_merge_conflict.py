import helpers.hunit_test as hunitest
import linters.amp_check_merge_conflict as lachmeco


class Test_check_merge_conflict(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the warning is raised for the first conflict marker.
        """
        line = ">>>>>>> master"
        msg = lachmeco._check_merge_conflict("test.py", 1, line)
        self.assertIn("test.py:1: git merge conflict marker detected", msg)

    def test2(self) -> None:
        """
        Test that the warning is raised for the second conflict marker.
        """
        line = "<<<<<<< HEAD"
        msg = lachmeco._check_merge_conflict("test.py", 1, line)
        self.assertIn("test.py:1: git merge conflict marker detected", msg)

    def test3(self) -> None:
        """
        Test that the warning is raised for the third conflict marker.
        """
        line = "======= "
        msg = lachmeco._check_merge_conflict("test.py", 1, line)
        self.assertIn("test.py:1: git merge conflict marker detected", msg)

    def test4(self) -> None:
        """
        Test that no warning is raised when there is no conflict marker.
        """
        line = "line not starting with '<<<<<<< '"
        msg = lachmeco._check_merge_conflict("test.py", 1, line)
        self.assertEqual("", msg)
