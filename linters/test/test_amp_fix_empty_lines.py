import helpers.hunit_test as hunitest
import linters.amp_fix_empty_lines as lafiemli


# #############################################################################
# Test_fix_empty_lines
# #############################################################################


class Test_fix_empty_lines(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test cleaning empty lines in a single function.
        """
        text = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def func1(a:str)->str:
    """
    Print the string passed.

    :param a: String to be printed
    """
    print(a)

fun1("demo")

print("Outside function")'''
        expected = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def func1(a:str)->str:
    """
    Print the string passed.

    :param a: String to be printed
    """
    print(a)

fun1("demo")

print("Outside function")'''
        # Run.
        actual = lafiemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test cleaning empty lines in methods inside a class.
        """
        text = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def func1(a:str)->str:
    """
    docstring 1

    :param a: description
    """
    print("Inside fun1")
    print(a)

# #############################################################################
# TestDemo
# #############################################################################

class TestDemo():

    def func2(a: str) -> str:
        """
        docstring 2

        :param a: description
        : return: description
        """
        print("Inside fun2")
        return a


    def func3(a: str) -> str:
        """
        docstring 3

        :param a: description
        :return : description
        """
        print("Inside fun3")
        return a


fun1("demo")

print("Outside class")
'''
        expected = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def func1(a:str)->str:
    """
    docstring 1

    :param a: description
    """
    print("Inside fun1")
    print(a)

# #############################################################################
# TestDemo
# #############################################################################

class TestDemo():

    def func2(a: str) -> str:
        """
        docstring 2

        :param a: description
        : return: description
        """
        print("Inside fun2")
        return a


    def func3(a: str) -> str:
        """
        docstring 3

        :param a: description
        :return : description
        """
        print("Inside fun3")
        return a


fun1("demo")

print("Outside class")
'''
        # Run.
        actual = lafiemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)

    def test3(self) -> None:
        """
        Test cleaning empty lines in methods and functions.
        """
        text = '''import os
import numpy as np
import pandas as pd

a=11
b="demo"

def func1(a:str)->str:
    """
    docstring.

    :param a: description
    :return: description
    """
    print(a)
    return a


def func2(a:str)->str:
    """
    docstring

    :param a: description
    :return: description
    """
    return a


# #############################################################################
# TestDemo
# #############################################################################

class TestDemo():


    def func3(a: str) -> str:
        """
        docstring

        :param a: description
        :return: description
        """
        print(a)
        return a


    print("inside class")


    def func4(a: str) -> str:
        """
        docstring

        :param a: description
        :return: description
        """
        print(a)
        return a


def func5(a:str)->str:
    """
    docstring

    :param a: description
    :return: description
    """
    print(a)
    return a


print("Outside class")


def func6(a:str)->str:
    """
    docstring

    :param a: description
    :return: description
    """
    print(a)
    return a'''
        expected = '''import os
import numpy as np
import pandas as pd

a=11
b="demo"

def func1(a:str)->str:
    """
    docstring.

    :param a: description
    :return: description
    """
    print(a)
    return a


def func2(a:str)->str:
    """
    docstring

    :param a: description
    :return: description
    """
    return a


# #############################################################################
# TestDemo
# #############################################################################

class TestDemo():


    def func3(a: str) -> str:
        """
        docstring

        :param a: description
        :return: description
        """
        print(a)
        return a


    print("inside class")


    def func4(a: str) -> str:
        """
        docstring

        :param a: description
        :return: description
        """
        print(a)
        return a


def func5(a:str)->str:
    """
    docstring

    :param a: description
    :return: description
    """
    print(a)
    return a


print("Outside class")


def func6(a:str)->str:
    """
    docstring

    :param a: description
    :return: description
    """
    print(a)
    return a'''
        # Run.
        actual = lafiemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)
