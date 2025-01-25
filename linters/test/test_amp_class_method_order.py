import helpers.hunit_test as hunitest
import linters.amp_class_method_order as laclmeor


class Test_correct_method_order(hunitest.TestCase):
    def test_1(self) -> None:
        """
        Test methods in incorrect order are re-ordered.
        """
        original = """
class Test:
    def test1():
        pass

    def __init__():
        pass

    def _test2():
        pass

    def test3():
        pass

    def __magic_test__():
        pass

"""
        expected = """
class Test:

    def __init__():
        pass

    def __magic_test__():
        pass

    def test1():
        pass

    def test3():
        pass

    def _test2():
        pass

"""
        self._helper(original, expected)

    def test_2(self) -> None:
        """
        Test methods in correct order aren't re-ordered.
        """
        original = expected = """
class Test:
    def __init__():
        pass

    def __magic_test__():
        pass

    def test1():
        pass

    def test3():
        pass

    def _test2():
        pass
"""
        self._helper(original, expected)

    def test_3(self) -> None:
        """
        Test methods with comments in incorrect order are re-ordered without
        losing information.
        """
        # pylint: disable=line-too-long
        original = """
class Test:
    def test1():
        # This is a test comment
        pass

    def __init__():
        # Another comment
        pass
"""
        expected = """
class Test:
    def __init__():
        # Another comment
        pass

    def test1():
        # This is a test comment
        pass
"""
        self._helper(original, expected)

    def test_4(self) -> None:
        """
        Test methods with docstrings in incorrect order are re-ordered without
        losing information.
        """
        original = '''
class Test:
    def test1():
        """This is a test docstring"""
        pass

    def __init__():
        """Another docstring"""
        pass
'''
        expected = '''
class Test:
    def __init__():
        """Another docstring"""
        pass

    def test1():
        """This is a test docstring"""
        pass
'''
        self._helper(original, expected)

    def test_5(self) -> None:
        """
        Test that static and regular methods are re-ordered correctly.
        """
        original = """
class Test:
    @staticmethod
    def test1():
        pass

    def __init__():
        pass

    @staticmethod
    def _test2():
        pass

    def test3():
        pass

    def _test4():
        pass

    def __magic_test__():
        pass

"""
        expected = """
class Test:

    def __init__():
        pass

    def __magic_test__():
        pass

    @staticmethod
    def test1():
        pass

    def test3():
        pass

    @staticmethod
    def _test2():
        pass

    def _test4():
        pass

"""
        self._helper(original, expected)

    def test_6(self) -> None:
        """
        Test re-ordering with different decorators.
        """
        original = """
@pytest.mark.skip("ABC")
class Test:

    def __init__():
        pass

    @pytest.mark.skip("DEF")
    def test1():
        pass

    @pytest.mark.slow()
    @umock.patch.object(imvcdeexcl.hdateti, "get_current_time")
    def _test2():
        pass

    def __magic_test__():
        pass

"""
        expected = """
@pytest.mark.skip("ABC")
class Test:

    def __init__():
        pass

    def __magic_test__():
        pass

    @pytest.mark.skip("DEF")
    def test1():
        pass

    @pytest.mark.slow()
    @umock.patch.object(imvcdeexcl.hdateti, "get_current_time")
    def _test2():
        pass

"""
        self._helper(original, expected)

    def _helper(self, txt: str, expected: str) -> None:
        actual = laclmeor.order_methods(txt)
        # Remove empty lines since they can create issues.
        actual = hunitest.filter_text(r"^\s*$", actual)
        expected = hunitest.filter_text(r"^\s*$", expected)
        self.assert_equal(actual, expected)
