import helpers.hunit_test as hunitest
import linters.amp_add_class_frames as laadclfr


class Test_add_class_frame(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test adding frames to classes, without extra complications.
        """
        # Initialize the input file contents.
        content = """
class FirstClass():
    pass

class SecondClass():
    pass
        """
        # Run.
        actual = "\n".join(laadclfr.update_class_frames(content))
        # Check.
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
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test adding frames to classes with lines that need to be skipped.

        Lines with decorators or comments that immediately precede class
        initialization need to be skipped.
        """
        # Initialize the input file contents.
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
        # Run.
        actual = "\n".join(laadclfr.update_class_frames(content))
        # Check.
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
        self.assertEqual(actual, expected)

    def test3(self) -> None:
        """
        Test adding a frame to a class in the middle of a file.
        """
        # Initialize the input file contents.
        content = """
def func1():
    pass

class FirstClass():
    pass
        """
        # Run.
        actual = "\n".join(laadclfr.update_class_frames(content))
        # Check.
        expected = """
def func1():
    pass

# #############################################################################
# FirstClass
# #############################################################################

class FirstClass():
    pass
        """
        self.assertEqual(actual, expected)

    def test4(self) -> None:
        """
        Test adding frames to classes when there are separating lines present.
        """
        # Initialize the input file contents.
        content = """
class FirstClass():
    pass

# #############################################################################

class SecondClass():
    pass
        """
        # Run.
        actual = "\n".join(laadclfr.update_class_frames(content))
        # Check.
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
        self.assertEqual(actual, expected)

    def test5(self) -> None:
        """
        Test adding frames to classes when there are already some present.

        Check that the existing frames are not changed when they contain
        class names.
        """
        # Initialize the input file contents.
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
        # Run.
        actual = "\n".join(laadclfr.update_class_frames(content))
        # Check.
        self.assertEqual(actual, content)

    def test6(self) -> None:
        """
        Test adding frames to classes when there are already some present.

        Check that the existing frames are removed when they do not
        contain class names, and new frames with class names are added.
        """
        # Initialize the input file contents.
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
        # Run.
        actual = "\n".join(laadclfr.update_class_frames(content))
        # Check.
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
        self.assertEqual(actual, expected)
