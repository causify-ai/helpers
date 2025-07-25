import abc
import logging
from typing import Any, Callable, List, Optional

import pandas as pd

import helpers.hdbg as hdbg
import helpers.hobject as hobject
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_purification as huntepur

_LOG = logging.getLogger(__name__)


# #############################################################################
# _Obj_to_str_TestCase
# #############################################################################


# Note that we can't derive this class from `hunitest.TestCase` otherwise the
# unit test framework will try to run the tests in this class.
class _Obj_to_str_TestCase(abc.ABC):
    """
    Test case for testing `obj_to_str()` and `obj_to_repr()`.
    """

    @abc.abstractmethod
    def get_object(self) -> Any:
        """
        Build object to test.
        """
        ...

    def helper(self, *, expected: Optional[str] = None, **kwargs: Any) -> None:
        obj = self.get_object()
        hdbg.dassert_is_not(obj, None)
        #
        txt: List[str] = []
        # Get `str()`.
        txt.append(hprint.frame("str:"))
        txt.append(hobject.obj_to_str(obj, **kwargs))
        # Get `repr()`.
        txt.append(hprint.frame("repr:"))
        txt.append(hobject.obj_to_repr(obj, **kwargs))
        # Concat.
        txt = "\n".join(txt)
        # Check.
        if expected is None:
            self.check_string(txt, purify_text=True)
        else:
            hdbg.dassert_isinstance(expected, str)
            self.assert_equal(txt, expected, purify_text=True, fuzzy_match=True)

    def test1(self, expected: str) -> None:
        """
        Use `__dict__` to extract the attributes.
        """
        self.helper(expected=expected, attr_mode="__dict__")

    def test2(self, expected: str) -> None:
        """
        Use `dir` to extract the attributes.
        """
        self.helper(expected=expected, attr_mode="dir")

    def test3(self, expected: str) -> None:
        """
        Use `__dict__` and print the type of the attributes.
        """
        self.helper(expected=expected, print_type=True)

    def test4(self) -> None:
        """
        Print only callable attributes.
        """
        self.helper(callable_mode="all")

    def test5(self) -> None:
        """
        Print only private attributes.
        """
        self.helper(private_mode="all")

    def test6(self) -> None:
        """
        Print only dunder attributes.
        """
        self.helper(dunder_mode="all")


# #############################################################################
# _Object1
# #############################################################################


class _Object1:
    """
    Object storing only scalar members and not other nested objects.
    """

    def __init__(self) -> None:
        self.a = False
        self.b = "hello"
        self.c = 3.14
        self._hello = "under"
        self.__hello = "double_dunder"
        self.hello = lambda x: x + 1


# #############################################################################
# Test_obj_to_str1
# #############################################################################


class Test_obj_to_str1(hunitest.TestCase, _Obj_to_str_TestCase):
    def get_object(self) -> Any:
        obj = _Object1()
        return obj

    def test1(self) -> None:
        expected = r"""
        ################################################################################
        str:
        ################################################################################
        _Object1 at 0x=(a=False, b=hello, c=3.14)
        ################################################################################
        repr:
        ################################################################################
        <helpers.test.test_hobject._Object1 at 0x>:
          a='False'
          b='hello'
          c='3.14'
        """
        super().test1(expected)

    def test2(self) -> None:
        expected = r"""
        ################################################################################
        str:
        ################################################################################
        _Object1 at 0x=(a=False, b=hello, c=3.14)
        ################################################################################
        repr:
        ################################################################################
        <helpers.test.test_hobject._Object1 at 0x>:
          a='False'
          b='hello'
          c='3.14'
        """
        super().test2(expected)

    def test3(self) -> None:
        expected = r"""
        ################################################################################
        str:
        ################################################################################
        _Object1 at 0x=(a=False <bool>, b=hello <str>, c=3.14 <float>)
        ################################################################################
        repr:
        ################################################################################
        <helpers.test.test_hobject._Object1 at 0x>:
          a='False' <bool>
          b='hello' <str>
          c='3.14' <float>
        """
        super().test3(expected)


# #############################################################################
# _Object2
# #############################################################################


class _Object2:
    """
    Object using a `obj_to_str()` as repr.
    """

    def __init__(self) -> None:
        self.x = True
        self.y = "world"
        self.z = 6.28
        self._hello = "under"
        self.__hello = "double_dunder"
        self.hello = lambda x: x + 1

    def __repr__(self) -> str:
        return hobject.obj_to_str(self)


# #############################################################################
# _Object3
# #############################################################################


class _Object3:
    """
    Object storing another object.
    """

    def __init__(self) -> None:
        self.p = "p"
        self.q = "q"
        self.object2 = _Object2()


# #############################################################################
# Test_obj_to_str2
# #############################################################################


class Test_obj_to_str2(hunitest.TestCase, _Obj_to_str_TestCase):
    def get_object(self) -> Any:
        obj = _Object3()
        return obj

    def test1(self) -> None:
        # TODO(gp): object2 in repr should be printed recursively as repr, but
        # it's not.
        expected = r"""
        ################################################################################
        str:
        ################################################################################
        _Object3 at 0x=(p=p, q=q, object2=_Object2 at 0x=(x=True, y=world, z=6.28))
        ################################################################################
        repr:
        ################################################################################
        <helpers.test.test_hobject._Object3 at 0x>:
          p='p'
          q='q'
          object2='_Object2 at 0x=(x=True, y=world, z=6.28)'
        """
        super().test1(expected)

    def test2(self) -> None:
        expected = r"""
        ################################################################################
        str:
        ################################################################################
        _Object3 at 0x=(object2=_Object2 at 0x=(x=True, y=world, z=6.28), p=p, q=q)
        ################################################################################
        repr:
        ################################################################################
        <helpers.test.test_hobject._Object3 at 0x>:
          object2='_Object2 at 0x=(x=True, y=world, z=6.28)'
          p='p'
          q='q'
        """
        super().test2(expected)

    def test3(self) -> None:
        expected = r"""
        ################################################################################
        str:
        ################################################################################
        _Object3 at 0x=(p=p <str>, q=q <str>, object2=_Object2 at 0x=(x=True, y=world, z=6.28) <helpers.test.test_hobject._Object2>)
        ################################################################################
        repr:
        ################################################################################
        <helpers.test.test_hobject._Object3 at 0x>:
          p='p' <str>
          q='q' <str>
          object2='_Object2 at 0x=(x=True, y=world, z=6.28)' <helpers.test.test_hobject._Object2>
        """
        super().test3(expected)


# #############################################################################
# _Abstract_ClassA
# #############################################################################


class _Abstract_ClassA(abc.ABC, hobject.PrintableMixin):
    """
    Abstract class descending from `PrintableMixin`.
    """

    def __init__(self) -> None:
        self._arg0 = 0
        self._arg1 = "one"
        self._arg2 = 2

    @staticmethod
    def get_config_attributes() -> List[str]:
        return ["_arg1", "_arg2"]


# #############################################################################
# _ClassB
# #############################################################################


class _ClassB(hobject.PrintableMixin):
    """
    Class descending from `PrintableMixin`.
    """

    def __init__(self, get_wall_clock_time: Callable) -> None:
        self._arg5 = {"key1": "five", "key2": 5}
        self._arg6 = "abc"
        self._get_wall_clock_time = get_wall_clock_time

    @staticmethod
    def get_config_attributes() -> List[str]:
        return ["_arg5", "_get_wall_clock_time"]

    def get_wall_clock_time(self) -> pd.Timestamp:
        """
        Return wall clock time in the timezone specified in the ctor.

        Initially wall clock time can be in any timezone, but cannot be
        timezone-naive.
        """
        wall_clock_time = self._get_wall_clock_time()
        return wall_clock_time


# #############################################################################
# _ClassA
# #############################################################################


class _ClassA(_Abstract_ClassA):
    """
    Class descending from `_AbstractClassA` and embedding `_ClassB`.
    """

    def __init__(self) -> None:
        super().__init__()
        self._arg3 = [3, 3, 3]
        get_wall_clock_time = lambda: pd.Timestamp(
            "2022-04-23", tz="America/New_York"
        )
        helper_class = _ClassB(get_wall_clock_time)
        self._arg4 = helper_class
        self._arg10 = {
            "key": 1,
            "get_wall_clock_time": helper_class.get_wall_clock_time,
        }

    def get_config_attributes(self) -> List[str]:
        config_attributes = super().get_config_attributes()
        child_class_attributes = ["_arg3", "_arg4", "_arg10"]
        config_attributes.extend(child_class_attributes)
        return config_attributes


# #############################################################################
# Test_PrintableMixin_to_config_str
# #############################################################################


class Test_PrintableMixin_to_config_str(hunitest.TestCase):
    def check_test_class_str(self, test_class: Any, expected: str) -> None:
        actual = test_class.to_config_str()
        text_purifier = huntepur.TextPurifier()
        actual = text_purifier.purify_txt_from_client(actual)
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test1(self) -> None:
        """
        Print `_Abstract_ClassA`.
        """
        test_class = _Abstract_ClassA()
        expected = r"""
        <helpers.test.test_hobject._Abstract_ClassA at 0x>:
            _arg1='one' <str>
            _arg2='2' <int>
        """
        self.check_test_class_str(test_class, expected)

    def test2(self) -> None:
        """
        Print `_ClassA`.
        """
        test_class = _ClassA()
        expected = r"""
        <helpers.test.test_hobject._ClassA at 0x>:
            _arg1='one' <str>
            _arg2='2' <int>
            _arg3='[3, 3, 3]' <list>
            _arg4=<helpers.test.test_hobject._ClassB at 0x>:
                _arg5='{'key1': 'five', 'key2': 5}' <dict>
                _get_wall_clock_time='<function _ClassA.__init__.<locals>.<lambda> at 0x>' <function>
            _arg10= <dict>
                {'get_wall_clock_time': <bound method _ClassB.get_wall_clock_time of <helpers.test.test_hobject._ClassB at 0x>:
                    _arg5='{'key1': 'five', 'key2': 5}' <dict>
                    _arg6='abc' <str>>,
                    'key': 1}
        """
        self.check_test_class_str(test_class, expected)
