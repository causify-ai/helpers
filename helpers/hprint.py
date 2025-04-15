"""
Import as:

import helpers.hprint as hprint
"""

import functools
import inspect
import logging
import pprint
import re
import sys
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Match,
    Optional,
    Tuple,
    Union,
    cast,
)

import helpers.hdbg as hdbg

# This module can depend only on:
# - Python standard modules
# - a few helpers as described in `helpers/dependencies.txt`


_LOG = logging.getLogger(__name__)

# Mute this module unless we want to debug it.
_LOG.setLevel(logging.INFO)


# #############################################################################
# Debug output
# #############################################################################

_COLOR_MAP = {
    "blue": 94,
    "green": 92,
    "white": 0,
    "purple": 95,
    "red": 91,
    "yellow": 33,
    # Blu.
    "DEBUG": 34,
    # Cyan.
    "INFO": 36,
    # Yellow.
    "WARNING": 33,
    # Red.
    "ERROR": 31,
    # White on red background.
    "CRITICAL": 41,
}


def color_highlight(text: str, color: str) -> str:
    """
    Return a colored string.
    """
    prefix = "\033["
    suffix = "\033[0m"
    hdbg.dassert_in(color, _COLOR_MAP)
    color_code = _COLOR_MAP[color]
    txt = f"{prefix}{color_code}m{text}{suffix}"
    return txt


def clear_screen() -> None:
    print((chr(27) + "[2J"))


def line(char: Optional[str] = None, num_chars: Optional[int] = None) -> str:
    """
    Return a line with the desired character.
    """
    char = "#" if char is None else char
    num_chars = 80 if num_chars is None else num_chars
    return char * num_chars


def pprint_pformat(obj: Any, *, sort_dicts: bool = False) -> str:
    """
    Pretty-print in color.
    """
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import PythonLexer

    txt = pprint.pformat(obj, sort_dicts=sort_dicts)
    txt = highlight(txt, PythonLexer(), Terminal256Formatter())
    txt = txt.rstrip()
    return txt


def pprint_color(obj: Any, *, tag: Optional[str] = None, sep: str = "") -> None:
    """
    Pretty-print in color.
    """
    txt = ""
    if tag is not None:
        txt += tag + "= " + sep
    txt += pprint_pformat(obj)
    print(txt)


# TODO(gp): -> Use *args instead of forcing to build a string to simplify the caller.
def frame(
    message: str,
    *,
    char1: Optional[str] = None,
    num_chars: Optional[int] = None,
    char2: Optional[str] = None,
    thickness: int = 1,
    level: int = 0,
) -> str:
    """
    Print a frame around a message.

    :param message: message to print
    :param char1: char for top line of the frame
    :param num_chars: how many chars in each line (by default 80 chars)
    :param char2: char for bottom line of the frame
    :param thickness: how many overlapping lines
        - E.g., thickness = 2
        ```
        # #######...
        # #######...
        # hello
        # #######...
        # #######...
        ```
    :param level:  level of framing indent based on `#` char:
        - E.g., level = 0
        ```
        #######...
        hello
        #######...
        ```
        - E.g., level = 1
        ```
        # #######...
        # hello
        # #######...
        ```
    """
    # Fill in the default values.
    if char1 is None:
        # User didn't specify any char.
        char1 = char2 = "#"
    elif char1 is not None and char2 is None:
        # User specified only one char.
        char2 = char1
    elif char1 is None and char2 is not None:
        # User specified the second char, but not the first one.
        hdbg.dfatal(f"Invalid char1='{char1}' char2='{char2}'")
    else:
        # User specified both chars. Nothing to do.
        pass
    num_chars = 80 if num_chars is None else num_chars
    # Sanity check.
    hdbg.dassert_eq(len(char1), 1)
    hdbg.dassert_lte(1, num_chars)
    hdbg.dassert_eq(len(char2), 1)
    hdbg.dassert_lte(1, thickness)
    hdbg.dassert_lte(0, level)
    # Build the return value.
    prefix = ""
    if level:
        prefix = "#" * level + " "
    ret = (
        (prefix + (line(char1, num_chars) + "\n") * thickness)
        + (prefix + message + "\n")
        + (prefix + (line(char2, num_chars) + "\n") * thickness)
    ).rstrip("\n")
    return ret


def prepend(txt: str, prefix: str) -> str:
    """
    Add `prefix` before each line of the string `txt`.
    """
    lines = [prefix + curr_line for curr_line in txt.split("\n")]
    res = "\n".join(lines)
    return res


def indent(txt: Optional[str], *, num_spaces: int = 2) -> str:
    """
    Add `num_spaces` spaces before each line of the passed string.
    """
    if txt is None:
        return ""
    hdbg.dassert_isinstance(txt, str)
    hdbg.dassert_isinstance(num_spaces, int)
    hdbg.dassert_lte(0, num_spaces)
    spaces = " " * num_spaces
    txt_out = []
    for curr_line in txt.split("\n"):
        if curr_line.lstrip().rstrip() == "":
            # Do not prepend any space to a line with only white characters.
            txt_out.append("")
            continue
        txt_out.append(spaces + curr_line)
    res = "\n".join(txt_out)
    return res


def strict_split(text: str, max_length: int) -> str:
    """
    Split a string into chunks of `max_length` characters.
    """
    hdbg.dassert_lte(1, max_length)
    lines = [text[i : i + max_length] for i in range(0, len(text), max_length)]
    out = "\n".join(lines)
    return out


StrOrList = Union[str, List[str]]


# TODO(gp): Use this everywhere in the codebase to avoid back-and-forth
#  transforms between strings and lists of strings.
def split_lines(func: Callable) -> Callable:
    """
    A decorator that splits a string input into lines before passing it to the
    decorated function.
    """

    @functools.wraps(func)
    def wrapper(txt: StrOrList, *args: Any, **kwargs: Any) -> StrOrList:
        if isinstance(txt, str):
            # Split the txt into lines.
            lines = txt.splitlines()
            is_str = True
        else:
            # The txt is already a list of lines.
            hdbg.dassert_isinstance(txt, list)
            lines = txt
            is_str = False
        # Call the function.
        lines = func(lines, *args, **kwargs)
        if is_str:
            # Join the lines back together.
            out = "\n".join(lines)
        else:
            # The output is already a list of lines.
            out = lines
        return out

    return wrapper


@split_lines
def remove_lead_trail_empty_lines(lines: StrOrList) -> StrOrList:
    """
    Remove consecutive empty lines only at the beginning / end of a string.
    """
    # Remove leading empty lines.
    while lines and not lines[0].strip():
        lines.pop(0)
    # Remove trailing empty lines.
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def dedent(txt: str, *, remove_lead_trail_empty_lines_: bool = True) -> str:
    """
    Remove from each line the minimum number of spaces to align the text on the
    left.

    It is the opposite of `indent()`.

    :param txt: multi-line string
    :param txt: multi-line string
    :param remove_lead_trail_empty_lines_: if True, remove all the empty
        lines at the beginning and at the end
    """
    if remove_lead_trail_empty_lines_:
        txt = remove_lead_trail_empty_lines(txt)
    # Find the minimum number of leading spaces.
    min_num_spaces = None
    for curr_line in txt.split("\n"):
        _LOG.debug("min_num_spaces=%s: curr_line='%s'", min_num_spaces, curr_line)
        # Skip empty lines.
        if curr_line.lstrip().rstrip() == "":
            _LOG.debug("  -> Skipping empty line")
            continue
        m = re.search(r"^(\s*)", curr_line)
        hdbg.dassert(m)
        m: Match[Any]
        curr_num_spaces = len(m.group(1))
        _LOG.debug("  -> curr_num_spaces=%s", curr_num_spaces)
        if min_num_spaces is None or curr_num_spaces < min_num_spaces:
            min_num_spaces = curr_num_spaces
    _LOG.debug("min_num_spaces=%s", min_num_spaces)
    #
    txt_out = []
    for curr_line in txt.split("\n"):
        _LOG.debug("curr_line='%s'", curr_line)
        # Skip empty lines.
        if curr_line.lstrip().rstrip() == "":
            txt_out.append("")
            continue
        hdbg.dassert_lte(min_num_spaces, len(curr_line))
        txt_out.append(curr_line[min_num_spaces:])
    res = "\n".join(txt_out)
    return res


def align_on_left(txt: str) -> str:
    """
    Remove all leading/trailing spaces for each line.
    """
    txt_out = []
    for curr_line in txt.split("\n"):
        curr_line = curr_line.rstrip(" ").lstrip(" ")
        txt_out.append(curr_line)
    res = "\n".join(txt_out)
    return res


# TODO(gp): Is this used? It looks very thin.
def remove_empty_lines_from_string_list(arr: List[str]) -> List[str]:
    """
    Remove empty lines from a list of strings.
    """
    arr = [line for line in arr if line.rstrip().lstrip()]
    return arr


# TODO(gp): It would be nice to have a decorator to go from / to array of
#  strings.
def remove_empty_lines(txt: str) -> str:
    """
    Remove empty lines from a multi-line string.
    """
    hdbg.dassert_isinstance(txt, str)
    arr = txt.split("\n")
    arr = remove_empty_lines_from_string_list(arr)
    txt = "\n".join(arr)
    return txt


def vars_to_debug_string(vars_as_str: List[str], locals_: Dict[str, Any]) -> str:
    """
    Create a string with var name -> var value.

    E.g., ["var1", "var2"] is converted into: ``` var1=... var2=... ```
    """
    txt = []
    for var in vars_as_str:
        txt.append(var + "=")
        txt.append(indent(str(locals_[var])))
    return "\n".join(txt)


# #############################################################################
# Pretty print data structures.
# #############################################################################


def to_object_str(obj: Any) -> str:
    return "%s at %s" % (
        obj.__class__.__name__,
        hex(id(obj)),
    )


def to_object_repr(obj: Any) -> str:
    return "<%s.%s at %s>" % (
        obj.__class__.__module__,
        obj.__class__.__name__,
        hex(id(obj)),
    )


def thousand_separator(v: float) -> str:
    v = "{0:,}".format(v)
    return v


# TODO(gp): -> to_percentage
def perc(
    a: float,
    b: float,
    *,
    invert: bool = False,
    num_digits: int = 2,
    only_perc: bool = False,
    use_float: bool = False,
    only_fraction: bool = False,
    use_thousands_separator: bool = False,
) -> Union[str, float]:
    """
    Calculate percentage a / b as a string.

    Asserts 0 <= a <= b. If true, returns a/b to `num_digits` decimal places.

    :param a: numerator
    :param b: denominator
    :param invert: assume the fraction is (b - a) / b
        This is useful when we want to compute the complement of a count.
    :param num_digits: number of digits to represent the percentage
    :param only_perc: return only the percentage, without the fraction
        - E.g., "50.00%" vs "10 / 20 = 50.00%"
    :param use_float: return the percentage as a float. It requires
        `only_perc = True`
    :param only_fraction: return only the fraction, without the percentage
        - E.g., "10 / 20" vs "10 / 20 = 50.00%"
    :param use_thousands_separator: report the numbers using thousands separator
    :return: string with a/b
    """
    hdbg.dassert_lte(0, a)
    hdbg.dassert_lte(a, b)
    if invert:
        a = b - a
    if use_thousands_separator:
        a_str = str("{0:,}".format(a))
        b_str = str("{0:,}".format(b))
    else:
        a_str = str(a)
        b_str = str(b)
    #
    hdbg.dassert_lte(0, num_digits)
    if only_perc:
        fmt = "%." + str(num_digits) + "f"
        ret = fmt % (float(a) / b * 100.0)
        if use_float:
            # 57.27
            ret = float(ret)
        else:
            # 57.27%
            hdbg.dassert_isinstance(ret, str)
            ret += "%"
    elif only_fraction:
        # 4225 / 7377
        ret = "%s / %s" % (a_str, b_str)
    else:
        # 4225 / 7377 = 57.27%
        fmt = "%s / %s = %." + str(num_digits) + "f%%"
        ret = fmt % (a_str, b_str, float(a) / b * 100.0)
    return ret


def round_digits(
    v: float, *, num_digits: int = 2, use_thousands_separator: bool = False
) -> str:
    """
    Round digit returning a string representing the formatted number.

    :param v: value to convert
    :param num_digits: number of digits to represent v on None is
        (Default value = 2)
    :param use_thousands_separator: use "," to separate thousands
        (Default value = False)
    :returns: str with formatted value
    """
    if (num_digits is not None) and isinstance(v, float):
        fmt = "%0." + str(num_digits) + "f"
        res = float(fmt % v)
    else:
        res = v
    if use_thousands_separator:
        res = "{0:,}".format(res)  # type: ignore
    res_as_str = str(res)
    return res_as_str


# #############################################################################
# Logging helpers
# #############################################################################


# TODO(gp): Move this to hdbg.hlogging, but there are dependencies from this file.

# https://stackoverflow.com/questions/2749796 has some solutions to find the
# name of variables from the caller.


_VarNamesType = Optional[Union[str, List[str]]]


def _to_var_list(expression: _VarNamesType) -> List[str]:
    if isinstance(expression, List):
        return expression
    hdbg.dassert_isinstance(expression, str)
    # If expression is a list of space-separated expressions, convert each in a
    # string.
    exprs = [v.lstrip().rstrip() for v in expression.split(" ")]
    # Remove empty var names.
    exprs = [v for v in exprs if v.strip().rstrip() != ""]
    hdbg.dassert_isinstance(exprs, list)
    hdbg.dassert_lte(1, len(exprs))
    return exprs


def to_str(
    expression: str,
    *,
    frame_level: int = 1,
    print_lhs: bool = True,
    char_separator: str = ",",
    mode: str = "repr",
) -> str:
    """
    Return a string with the value of a variable / expression / multiple
    variables.

    If expression is a space-separated compound expression, convert it into
    `exp1=val1, exp2=val2, ...`.

    This is similar to Python 3.8 f-string syntax `f"{foo=} {bar=}"`.
    We don't want to force to use Python 3.8 just for this feature.
    ```
    > x = 1
    > to_str("x+1")
    x+1=2
    ```

    :param expression: the variable / expression to evaluate and print.
        E.g., `to_str("exp1")` is converted into `exp1=val1`.
        If expression is a space-separated compound expression, e.g.,
        `to_str("exp1 exp2 ...")`, it is converted into `exp1=val1, exp2=val2, ...`
    :param frame_level: level of the frame to inspect
    :param print_lhs: whether we want to print the left hand side (i.e., `exp1`)
    :param char_separator: separator between the values of the expressions
        when printed (e.g., `,`)
    :param mode: select how to print the value of the expressions (e.g., `str`,
        `repr`, `pprint`, `pprint_color`)
    """
    # TODO(gp): If we pass an object it would be nice to find the name of it.
    # E.g., https://github.com/pwwang/python-varname
    hdbg.dassert_isinstance(expression, str)
    if " " in expression:
        exprs = _to_var_list(expression)
        # Convert each expression into a value.
        _to_str = lambda x: to_str(x, frame_level=frame_level + 2)
        values = list(map(_to_str, exprs))
        # Assemble in a return value.
        hdbg.dassert_lte(len(char_separator), 1)
        sep = char_separator + " "
        txt = sep.join(values)
        return txt
    # Certain expressions are evaluated as literals.
    if expression in ("", "->", ":", "=", "\n"):
        return expression
    # Evaluate the expression.
    frame_ = sys._getframe(frame_level)  # pylint: disable=protected-access
    ret = ""
    if print_lhs:
        ret += expression + "="
    try:
        eval_ = eval(expression, frame_.f_globals, frame_.f_locals)
    except Exception as e:
        print("expression=''", expression)
        raise e
    if mode == "str":
        ret += str(eval_)
    elif mode == "repr":
        ret += repr(eval_)
    elif mode == "pprint":
        ret += "\n" + indent(pprint.pformat(eval_))
    elif mode == "pprint_color":
        ret += "\n" + indent(pprint_pformat(eval_))
    else:
        raise ValueError(f"Invalid mode='{mode}'")
    return ret


# TODO(gp): Extend this to work on class methods, static and not.
def _func_signature_to_str(
    skip_vars: _VarNamesType,
    assert_on_skip_vars_error: bool,
    frame_level: int,
) -> Tuple[str, str]:
    """
    Return the variables of the caller function as a string.

    Same params as `func_signature_to_str()`.
    :return: function name and string with the variables of the caller function
        as `var1 var2 ...`
    """
    if skip_vars is not None:
        skip_vars = _to_var_list(skip_vars)
    # Get the caller's frame (i.e., the function that called this function).
    caller_frame = inspect.currentframe()
    for _ in range(frame_level):
        caller_frame = caller_frame.f_back
    caller_function_name = caller_frame.f_code.co_name
    # _LOG.debug("caller_function_name=%s", caller_function_name)
    # Retrieve the function object from the caller's frame.
    caller_function = caller_frame.f_globals.get(caller_function_name, None)
    if caller_function:
        # Get the function's signature
        sig = inspect.signature(caller_function)
        var_names = list(sig.parameters.keys())
        if skip_vars:
            if assert_on_skip_vars_error:
                hdbg.dassert_is_subset(skip_vars, var_names)
            var_names = [
                var_name for var_name in var_names if var_name not in skip_vars
            ]
        vars_str = " ".join(var_names)
    else:
        raise ValueError("Unable to determine caller function")
    return caller_function_name, vars_str


def func_signature_to_str(
    # We don't use * since we want to keep it simple to call this function.
    skip_vars: _VarNamesType = None,
    *,
    assert_on_skip_vars_error: bool = True,
    frame_level: int = 2,
) -> str:
    r"""
    Return the variables of the caller function as a string.

    Use like:
    ```
    _LOG.debug("\n%s", hprint.func_signature_to_str())
    ```

    :param skip_vars: list of variables to skip
    :param assert_on_skip_vars_error: whether to assert if the variables to skip
        are not found in the function signature
    :param frame_level: level of the frame to inspect. By default we need to
        access the frame of the caller of the caller, so frame_level = 2
    """
    # Get the variables.
    func_name, func_signature = _func_signature_to_str(
        skip_vars,
        assert_on_skip_vars_error,
        frame_level,
    )
    # Get the value of the variables.
    val = to_str(func_signature, frame_level=frame_level)
    val = f"# {func_name}: {val}"
    return val


# #############################################################################


def log(logger: logging.Logger, verbosity: int, *vals: Any) -> None:
    """
    Log at a certain verbosity.

    `log(_LOG, logging.DEBUG, "ticker", "exchange")`

    is equivalent to statements like:

    ```
    _LOG.debug("%s, %s", to_str("ticker"), to_str("exchange"))
    _LOG.debug("ticker=%s, exchange=%s", ticker, exchange)
    ```
    """
    logger_verbosity = hdbg.get_logger_verbosity()
    # print("verbosity=%s logger_verbosity=%s" % (verbosity, logger_verbosity))
    # We want to avoid the overhead of converting strings, so we evaluate the
    # expressions only if we are going to print.
    if verbosity >= logger_verbosity:
        # We need to increment frame_lev since we are 2 levels deeper in the stack.
        _to_str = lambda x: to_str(x, frame_level=3)
        num_vals = len(vals)
        if num_vals == 1:
            fstring = "%s"
            vals = _to_str(vals[0])  # type: ignore
        else:
            fstring = ", ".join(["%s"] * num_vals)
            vals = list(map(_to_str, vals))  # type: ignore
        logger.log(verbosity, fstring, vals)


# TODO(gp): Replace calls to `_LOG.debug("\n%s", hprint.frame(...)` with this.
# TODO(gp): Consider changing the signature from
#  _log_frame(_LOG, "hello", verbosity=logger.INFO))
# to
#  _log_frame(_LOG.info, "hello", ...)
# by using the first element as a Callable
def log_frame(
    logger: logging.Logger,
    fstring: str,
    *args: Any,
    level: int = 1,
    char: str = "#",
    verbosity: int = logging.DEBUG,
) -> None:
    """
    Log using a frame around the text with different number of leading `#` (or
    `char`) to organize the log visually.

    The logging output looks like:
    _log_frame(_LOG, "hello", verbosity=logger.INFO))
    ```
    07:44:51       printing            : log_frame                     : 390 :
    # #########################################################################
    # hello
    # #########################################################################
    ```

    :param txt: text to print in a frame
    :param level: number of `#` (or `char`) to prepend the logged text
    :param char: char to prepend the logged text with
    :param verbosity: logging verbosity
    """
    hdbg.dassert_isinstance(logger, logging.Logger)
    hdbg.dassert_isinstance(fstring, str)
    msg = fstring % args
    msg = msg.rstrip().lstrip()
    msg = frame(msg)
    # Prepend a `# `, if needed.
    if level > 0:
        prefix = level * char + " "
        msg = prepend(msg, prefix=prefix)
    # Add an empty space.
    msg = "\n" + msg
    logger.log(verbosity, "%s", msg)


# #############################################################################


def type_to_string(type_as_str: str) -> str:
    """
    Return a short string representing the type of an object, e.g.,
    "dataflow.Node" (instead of "class <'dataflow.Node'>")
    """
    if isinstance(type_as_str, type):
        type_as_str = str(type_as_str)
    hdbg.dassert_isinstance(type_as_str, str)
    # Remove the extra string from:
    #   <class 'dataflow.Zscore'>
    prefix = "<class '"
    hdbg.dassert(type_as_str.startswith(prefix), type_as_str)
    suffix = "'>"
    hdbg.dassert(type_as_str.endswith(suffix), type_as_str)
    type_as_str = type_as_str[len(prefix) : -len(suffix)]
    return type_as_str


def type_obj_to_str(obj: Any) -> str:
    ret = f"({type(obj)}) {obj}"
    return ret


# #############################################################################


def format_list(
    list_: List[Any],
    *,
    sep: str = " ",
    max_n: Optional[int] = None,
    tag: Optional[str] = None,
) -> str:
    # sep = ", "
    if max_n is None:
        max_n = 10
    max_n = cast(int, max_n)
    hdbg.dassert_lte(1, max_n)
    n = len(list_)
    txt = ""
    if tag is not None:
        txt += f"{tag}: "
    txt += f"({n}) "
    if n < max_n:
        txt += sep.join(map(str, list_))
    else:
        num_elems = int(max_n / 2)
        hdbg.dassert_lte(1, num_elems)
        txt += sep.join(map(str, list_[:num_elems]))
        txt += " ... "
        # pylint: disable=invalid-unary-operand-type
        txt += sep.join(map(str, list_[-num_elems:]))
    return txt


# TODO(gp): Use format_list().
def list_to_str(
    list_: List,
    *,
    tag: str = "",
    sort: bool = False,
    axis: int = 0,
    to_string: bool = False,
) -> str:
    """
    Print list / index horizontally or vertically.
    """
    # TODO(gp): Fix this.
    _ = to_string
    txt = ""
    if axis == 0:
        if list_ is None:
            txt += f"{tag}: (0) None\n"
        else:
            # hdbg.dassert_in(type(l), (list, pd.Index, pd.Int64Index))
            vals = list(map(str, list_))
            if sort:
                vals = sorted(vals)
            txt += f"{tag}: ({len(list_)}) {' '.join(vals)}\n"
    elif axis == 1:
        txt += f"{tag} ({len(list_)}):\n"
        vals = list(map(str, list_))
        if sort:
            vals = sorted(vals)
        txt += "\n".join(vals) + "\n"
    else:
        raise ValueError(f"Invalid axis='{axis}'")
    return txt


def set_diff_to_str(
    obj1: Iterable,
    obj2: Iterable,
    *,
    obj1_name: str = "obj1",
    obj2_name: str = "obj2",
    sep_char: str = " ",
    add_space: bool = False,
) -> str:
    """
    Compute the difference between two sequences of data and return a formatted
    string.

    :param obj1: The first iterable object.
    :param obj2: The second iterable object.
    :param obj1_name: The name to use for the first object in the output string.
    :param obj2_name: The name to use for the second object in the output string.
    :param sep_char: The character to use for separating elements in the output
        string.
    :param add_space: Whether to add empty lines to make the output more readable.
    :return: A formatted string showing the differences between the two objects.

    Example:
    ```
    >>> obj1 = [1, 2, 3, 4]
    >>> obj2 = [3, 4, 5, 6]
    >>> set_diff_to_str(obj1, obj2, obj1_name="list1", obj2_name="list2")
    * list1: (4) 1 2 3 4
    * list2: (4) 3 4 5 6
    * intersect=(2) 3 4
    * list1-list2=(2) 1 2
    * list2-list1=(2) 5 6
    ```
    """

    def _to_string(obj: Iterable) -> str:
        obj = sorted(list(obj))
        if sep_char == "\n":
            txt = indent("\n" + sep_char.join(map(str, obj)))
        else:
            txt = sep_char.join(map(str, obj))
        return txt

    res: List[str] = []
    # obj1.
    obj1 = set(obj1)
    hdbg.dassert_lte(1, len(obj1))
    res.append(f"* {obj1_name}: ({len(obj1)}) {_to_string(obj1)}")
    if add_space:
        res.append("")
    # obj2.
    obj2 = set(obj2)
    hdbg.dassert_lte(1, len(obj2))
    res.append(f"* {obj2_name}: ({len(obj2)}) {_to_string(obj2)}")
    if add_space:
        res.append("")
    # obj1 intersect obj2.
    intersection = obj1.intersection(obj2)
    res.append(f"* intersect=({len(intersection)}) {_to_string(intersection)}")
    if add_space:
        res.append("")
    # obj1 - obj2.
    diff = obj1 - obj2
    res.append(f"* {obj1_name}-{obj2_name}=({len(diff)}) {_to_string(diff)}")
    if add_space:
        res.append("")
    # obj2 - obj1.
    diff = obj2 - obj1
    res.append(f"* {obj2_name}-{obj1_name}=({len(diff)}) {_to_string(diff)}")
    if add_space:
        res.append("")
    #
    res = "\n".join(res)
    return res


# #############################################################################


def remove_non_printable_chars(txt: str) -> str:
    # From https://stackoverflow.com/questions/14693701
    # 7-bit and 8-bit C1 ANSI sequences
    ansi_escape = re.compile(
        r"""
        \x1B  # ESC
        (?:   # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |     # or [ for CSI, followed by a control sequence
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    """,
        re.VERBOSE,
    )
    txt = ansi_escape.sub("", txt)
    return txt


# TODO(gp): Maybe move to helpers/hpython.py since it's not about printing.
def sort_dictionary(dict_: Dict) -> Dict:
    """
    Sort a dictionary recursively using nested OrderedDict.
    """
    import collections

    res = collections.OrderedDict()
    for k, v in sorted(dict_.items()):
        if isinstance(v, dict):
            res[k] = sort_dictionary(v)
        else:
            res[k] = v
    return res


def to_pretty_str(obj: Any) -> str:
    if isinstance(obj, dict):
        res = pprint.pformat(obj)
        # import json
        # res = json.dumps(obj, indent=4, sort_keys=True)
    else:
        res = str(obj)
    return res


# TODO(gp): GSI -> rename remove_lines()?
def filter_text(regex: str, txt: str) -> str:
    """
    Remove lines in `txt` that match the regex `regex`.
    """
    _LOG.debug("Filtering with '%s'", regex)
    if regex is None:
        return txt
    txt_out = []
    txt_as_arr = txt.split("\n")
    for line_ in txt_as_arr:
        if re.search(regex, line_):
            _LOG.debug("Skipping line='%s'", line_)
            continue
        txt_out.append(line_)
    # We can only remove lines.
    hdbg.dassert_lte(
        len(txt_out),
        len(txt_as_arr),
        "txt_out=\n'''%s'''\ntxt=\n'''%s'''",
        "\n".join(txt_out),
        "\n".join(txt_as_arr),
    )
    txt = "\n".join(txt_out)
    return txt


def dassert_one_trailing_newline(txt: str) -> None:
    num_newlines = len(re.search(r'\n*$', txt).group())
    hdbg.dassert_eq(num_newlines, 0, "num_newlines='%s' txt='%s'", num_newlines, txt)


def to_info(tag: str, txt: Union[str, List[str]]) -> str:
    hdbg.dassert_isinstance(tag, str)
    hdbg.dassert_isinstance(txt, (str, list))
    txt_tmp = ""
    txt_tmp += "# " + tag + "\n"
    # Indent the text.
    if not isinstance(txt, str):
        for t in txt:
            hdbg.dassert_isinstance(t, str)
        txt = "\n".join(txt)
    txt_tmp += indent(txt)
    # Ensure that there is a single trailing newline.
    txt_tmp = txt_tmp.rstrip("\n")
    # txt_tmp += "\n"
    # _dassert_one_trailing_newline(txt_tmp)
    _LOG.debug("'%s'", txt_tmp)
    return txt_tmp


# #############################################################################
# Notebook output
# #############################################################################

# TODO(gp): Move to explore.py or notebook.py


def config_notebook(sns_set: bool = True) -> None:
    # Matplotlib.
    import matplotlib.pyplot as plt

    # plt.rcParams
    plt.rcParams["figure.figsize"] = (20, 5)
    plt.rcParams["legend.fontsize"] = 14
    plt.rcParams["font.size"] = 14
    plt.rcParams["image.cmap"] = "rainbow"

    if False:
        # Tweak the size of the plots to make it more readable when embedded in
        # documents or presentations.
        # font = {'family' : 'normal',
        #         #'weight' : 'bold',
        #         'size'   : 32}
        # matplotlib.rc('font', **font)
        scale = 3
        small_size = 8 * scale
        medium_size = 10 * scale
        bigger_size = 12 * scale
        # Default text sizes.
        plt.rc("font", size=small_size)
        # Fontsize of the axes title.
        plt.rc("axes", titlesize=small_size)
        # Fontsize of the x and y labels.
        plt.rc("axes", labelsize=medium_size)
        # Fontsize of the tick labels.
        plt.rc("xtick", labelsize=small_size)
        # Fontsize of the tick labels.
        plt.rc("ytick", labelsize=small_size)
        # Legend fontsize.
        plt.rc("legend", fontsize=small_size)
        # Fontsize of the figure title.
        plt.rc("figure", titlesize=bigger_size)

    # Seaborn.
    import seaborn as sns

    if sns_set:
        sns.set()

    # Pandas.
    import pandas as pd

    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 500)
    pd.set_option("display.width", 1000)

    # Warnings.
    import helpers.hwarnings as hwarnin

    # Force the linter to keep this import.
    _ = hwarnin
