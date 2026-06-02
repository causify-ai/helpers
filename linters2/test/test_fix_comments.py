import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import linters2.fix_comments as lficom


# #############################################################################
# Test_convert_single_line_docstrings
# #############################################################################


class Test_convert_single_line_docstrings(hunitest.TestCase):
    def helper(self, content: str, expected: str) -> None:
        """
        Transform input content and compare with expected output.

        :param content: Input Python code as a string with potential indentation
        :param expected: Expected output after applying docstring transformations
        """
        # Initialize the input file contents.
        content = hprint.dedent(content)
        # Run.
        actual = "\n".join(lficom.convert_single_line_docstrings(content))
        expected = hprint.dedent(expected)
        # Check.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test converting function docstring with double quotes.
        """
        content = '''
        def _is_mdformat_available() -> bool:
            """Check if mdformat package is available."""
        '''
        expected = '''
        def _is_mdformat_available() -> bool:
            """
            Check if mdformat package is available.
            """
        '''
        self.helper(content, expected)

    def test2(self) -> None:
        """
        Test converting class docstring with double quotes.
        """
        content = '''
        class Is_mdformat_available:
            """Check if mdformat package is available."""
        '''
        expected = '''
        class Is_mdformat_available:
            """
            Check if mdformat package is available.
            """
        '''
        self.helper(content, expected)

    def test3(self) -> None:
        """
        Test converting function with different indentation levels.
        """
        content = '''
        def func1():
            """Short docstring."""
            pass

        class MyClass:
            def method(self):
                """Method docstring."""
                pass
        '''
        expected = '''
        def func1():
            """
            Short docstring.
            """
            pass

        class MyClass:
            def method(self):
                """
                Method docstring.
                """
                pass
        '''
        self.helper(content, expected)

    def test4(self) -> None:
        """
        Test converting multiple functions in one file.
        """
        content = '''
        def func1():
            """First function."""
            pass

        def func2():
            """Second function."""
            pass
        '''
        expected = '''
        def func1():
            """
            First function.
            """
            pass

        def func2():
            """
            Second function.
            """
            pass
        '''
        self.helper(content, expected)

    def test5(self) -> None:
        """
        Test preserving already multi-line docstrings.
        """
        content = '''
        def func1():
            """
            Multi-line docstring.
            Already formatted correctly.
            """
            pass
        '''
        expected = content
        self.helper(content, expected)

    def test6(self) -> None:
        """
        Test converting docstring with single quotes.
        """
        content = """
        def func1():
            '''Single quote docstring.'''
            pass
        """
        expected = """
        def func1():
            '''
            Single quote docstring.
            '''
            pass
        """
        self.helper(content, expected)

    def test7(self) -> None:
        """
        Test handling module-level docstring.
        """
        content = '''
        """Module docstring."""

        def func1():
            """Function docstring."""
            pass
        '''
        expected = '''
        """
        Module docstring.
        """

        def func1():
            """
            Function docstring.
            """
            pass
        '''
        self.helper(content, expected)

    def test8(self) -> None:
        """
        Test converting docstring with special characters.
        """
        content = '''
        def func1():
            """Check if obj -> str conversion works."""
            pass
        '''
        expected = '''
        def func1():
            """
            Check if obj -> str conversion works.
            """
            pass
        '''
        self.helper(content, expected)

    def test9(self) -> None:
        """
        Test converting docstring with code examples.
        """
        content = '''
        def func1():
            """Return x=5, y=10."""
            pass
        '''
        expected = '''
        def func1():
            """
            Return x=5, y=10.
            """
            pass
        '''
        self.helper(content, expected)

    def test10(self) -> None:
        """
        Test file with mix of single and multi-line docstrings.
        """
        content = '''
        def func1():
            """Single line."""
            pass

        def func2():
            """
            Multi line.
            Already correct.
            """
            pass

        def func3():
            """Another single line."""
            pass
        '''
        expected = '''
        def func1():
            """
            Single line.
            """
            pass

        def func2():
            """
            Multi line.
            Already correct.
            """
            pass

        def func3():
            """
            Another single line.
            """
            pass
        '''
        self.helper(content, expected)

    def test11(self) -> None:
        """
        Test converting nested class methods.
        """
        content = '''
        class Outer:
            """Outer class."""

            class Inner:
                """Inner class."""

                def method(self):
                    """Method docstring."""
                    pass
        '''
        expected = '''
        class Outer:
            """
            Outer class.
            """

            class Inner:
                """
                Inner class.
                """

                def method(self):
                    """
                    Method docstring.
                    """
                    pass
        '''
        self.helper(content, expected)

    def test12(self) -> None:
        """
        Test file with no docstrings.
        """
        content = '''
        def func1():
            x = 1
            return x

        class MyClass:
            pass
        '''
        expected = content
        self.helper(content, expected)

    def test13(self) -> None:
        """
        Test docstring with newline character in content (escaped).
        """
        content = '''
        def func1():
            """Line1\\nLine2."""
            pass
        '''
        expected = '''
        def func1():
            """
            Line1\\nLine2.
            """
            pass
        '''
        self.helper(content, expected)

    def test14(self) -> None:
        """
        Test docstring with trailing whitespace (should be normalized).
        """
        content = '''
        def func1():
            """Docstring with trailing space.   """
            pass
        '''
        expected = '''
        def func1():
            """
            Docstring with trailing space.
            """
            pass
        '''
        self.helper(content, expected)

    def test15(self) -> None:
        """
        Test very long docstring that remains single-line.
        """
        content = '''
        def func1():
            """This is a very long docstring that explains something in great detail."""
            pass
        '''
        expected = '''
        def func1():
            """
            This is a very long docstring that explains something in great detail.
            """
            pass
        '''
        self.helper(content, expected)
