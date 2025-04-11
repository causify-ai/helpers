import os

import helpers.hio as hio
import helpers.hunit_test as hunitest
import linters.amp_remove_empty_lines as lareemli


# #############################################################################
# Test_remove_empty_lines
# #############################################################################


class Test_remove_empty_lines(hunitest.TestCase):

    def test1(self) -> None:
        """
        Test cleaning empty lines in a single function.
        """
        test_input_dir = self.get_input_dir()
        text_file_path = os.path.join(test_input_dir, "test.txt")
        text = hio.from_file(text_file_path)
        expected = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def add(a: int, b: int) -> int:
    """
    Return the sum of 2 numbers.

    :param a: first number
    :param b: second number
    :return: sum of 2 numbers
    """
    print("Inside function add()")
    return a + b


result = add(2, 3)

print("Result: ", result)
print("Outside function")'''
        # Run.
        actual = lareemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)

    def test2(self) -> None:
        """
        Test cleaning empty lines in methods inside a class.
        """
        test_input_dir = self.get_input_dir()
        text_file_path = os.path.join(test_input_dir, "test.txt")
        text = hio.from_file(text_file_path)
        expected = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple


# #############################################################################
# Calculator
# #############################################################################

class Calculator:

    def add(self, a: int, b: int) -> int:
        """
        Return the sum of 2 numbers.

        :param a: first number
        :param b: second number
        :return: sum of 2 numbers
        """
        print("Inside function add()")
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """
        Return the difference of 2 numbers.

        :param a: first number
        :param b: second number
        :return: difference of 2 numbers
        """
        print("Inside function subtract()")
        return a - b


calc = Calculator()

print(calc.add(10, 5))
print(calc.subtract(10, 5))'''
        # Run.
        actual = lareemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)

    def test3(self) -> None:
        """
        Test cleaning empty lines in methods and functions.
        """
        test_input_dir = self.get_input_dir()
        text_file_path = os.path.join(test_input_dir, "test.txt")
        text = hio.from_file(text_file_path)
        expected = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def check_largest(a: int, b: int) -> None:
    """
    Display largest among two numbers.

    :param a: first number to compare
    :param b: second number to compare
    """
    print("Inside check_largest()")
    if a > b:
        print(a, "is largest")
    elif b > a:
        print(b, "is largest")
    else:
        print("Both are same")

# #############################################################################
# Calculator
# #############################################################################

class Calculator:

    def add(self, a: int, b: int) -> int:
        """
        Return the sum of 2 numbers.

        :param a: first number
        :param b: second number
        :return: sum of 2 numbers
        """
        print("Inside function add()")
        return a + b

    def subtract(self, a: int, b: int) -> int:
        """
        Return the difference of 2 numbers.

        :param a: first number
        :param b: second number
        :return: difference of 2 numbers
        """
        print("Inside function subtract()")
        return a - b

a = 10
b = 5

check_largest(a, b)

calc = Calculator()
print(calc.add(a, b))
print(calc.subtract(a, b))'''
        # Run.
        actual = lareemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)

    def test4(self) -> None:
        """
        Test cleaning empty lines in methods and functions without any empty
        lines.
        """
        test_input_dir = self.get_input_dir()
        text_file_path = os.path.join(test_input_dir, "test.txt")
        text = hio.from_file(text_file_path)
        expected = '''import os
import numpy as np
import pandas as pd

from typing import List, Tuple

def add(a: int, b: int) -> int:
    """
    Return the sum of 2 numbers.

    :param a: first number
    :param b: second number
    :return: sum of 2 numbers
    """
    print("Inside function add()")
    return a + b


result = add(2, 3)

print("Result: ", result)
print("Outside function")'''
        # Run.
        actual = lareemli.update_function_blocks(text)
        # Check.
        self.assertEqual(expected, actual)
