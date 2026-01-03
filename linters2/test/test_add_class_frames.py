import helpers.hunit_test as hunitest
import helpers.hprint as hprint
import linters2.add_class_frames as ladclfra

# #############################################################################
# Test_add_class_frame
# #############################################################################

class Test_add_class_frame(hunitest.TestCase):
    def helper(self, content: str, expected: str) -> None:
        # Initialize the input file contents.
        content = hprint.dedent(content)
        # Run.
        actual = "\n".join(ladclfra.update_class_frames(content))
        expected = hprint.dedent(expected)
        # Check.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test adding frames to classes, without extra complications.
        """
        content = """
        class FirstClass():
            pass

        class SecondClass():
            pass
        """
        expected = """
        # #############################################################################
        # FirstClass
        # #############################################################################

        class FirstClass():
            pass

        # #############################################################################
        # SecondClass
        # #############################################################################

        class SecondClass():
            pass
        """
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test adding frames to classes with lines that need to be skipped.

        Lines with decorators or comments that immediately precede class
        initialization need to be skipped.
        """
        content = """
        # Comment.
        class FirstClass():
            pass

        # Comment.
        @decorator
        class SecondClass():
            pass

        @mult_line_decorator(
            note="..."
        )
        class ThirdClass():
            pass
        """
        expected = """
        # #############################################################################
        # FirstClass
        # #############################################################################

        # Comment.
        class FirstClass():
            pass

        # #############################################################################
        # SecondClass
        # #############################################################################

        # Comment.
        @decorator
        class SecondClass():
            pass

        # #############################################################################
        # ThirdClass
        # #############################################################################

        @mult_line_decorator(
            note="..."
        )
        class ThirdClass():
            pass
        """
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test adding a frame to a class in the middle of a file.
        """
        content = """
        def func1():
            pass

        class FirstClass():
            pass
        """
        expected = """
        def func1():
            pass

        # #############################################################################
        # FirstClass
        # #############################################################################

        class FirstClass():
            pass
        """
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test adding frames to classes when there are separating lines present.
        """
        content = """
        class FirstClass():
            pass

        # #############################################################################

        class SecondClass():
            pass
        """
        expected = """
        # #############################################################################
        # FirstClass
        # #############################################################################

        class FirstClass():
            pass

        # #############################################################################

        # #############################################################################
        # SecondClass
        # #############################################################################

        class SecondClass():
            pass
        """
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test adding frames to classes when there are already some present.

        Check that the existing frames are not changed when they contain
        class names.
        """
        content = """
        def func1():
            pass

        # #############################################################################
        # FirstClass
        # #############################################################################

        class FirstClass():
            pass

        # #############################################################################
        # SecondClass
        # #############################################################################

        @decorator1
        @decorator2
        class SecondClass():
            pass
        """
        expected = content
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test adding frames to classes when there are already some present.

        Check that the existing frames are removed when they do not
        contain class names, and new frames with class names are added.
        """
        content = """
        def func1():
            pass

        # #############################################################################
        # Some text
        # #############################################################################

        class FirstClass():
            pass

        # #############################################################################
        # Other text
        # #############################################################################

        @decorator1
        @decorator2
        class SecondClass():
            pass
        """
        expected = """
        def func1():
            pass

        # #############################################################################
        # FirstClass
        # #############################################################################

        class FirstClass():
            pass

        # #############################################################################
        # SecondClass
        # #############################################################################

        @decorator1
        @decorator2
        class SecondClass():
            pass
        """
        self.helper(content, expected)
