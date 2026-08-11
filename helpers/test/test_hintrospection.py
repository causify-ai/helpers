import importlib.abc
import importlib.machinery
import importlib.util
import logging
import os
import sys
import types
import unittest.mock as umock
from typing import Any, Callable, cast, Dict

import helpers.hdbg as hdbg
import helpers.hintrospection as hintros
import helpers.hio as hio
import helpers.hpickle as hpickle
import helpers.hsystem as hsystem
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_is_pickleable
# #############################################################################


def hello() -> bool:
    return False


# #############################################################################
# _ClassPickleable
# #############################################################################


class _ClassPickleable:
    """
    Class with pickleable param values.
    """

    def __init__(self) -> None:
        self._arg1 = 1
        self._arg2 = ["2", 3]

    @staticmethod
    def say2(self) -> None:
        print("Hello")

    def say(self) -> None:
        print("Hello")


# #############################################################################
# _ClassNonPickleable
# #############################################################################


class _ClassNonPickleable:
    """
    Class with non-pickleable param values.
    """

    def __init__(self) -> None:
        self._arg1 = lambda x: x
        self._arg2 = 2


# #############################################################################
# Test_is_pickleable1
# #############################################################################


class Test_is_pickleable1(hunitest.TestCase):
    def helper(
        self,
        obj: Any,
        exp_str: str,
        exp_bound: bool,
        exp_lambda: bool,
        exp_pickled: bool,
    ) -> None:
        _LOG.debug("obj=%s", obj)
        #
        act_str = str(obj)
        _LOG.debug("act_str=%s", act_str)
        _LOG.debug("exp_str=%s", exp_str)
        self.assert_equal(act_str, exp_str, purify_text=True)
        #
        act_bound = hintros.is_bound_to_object(obj)
        _LOG.debug("act_bound=%s", act_bound)
        _LOG.debug("exp_bound=%s", exp_bound)
        self.assertEqual(act_bound, exp_bound)
        #
        act_lambda = hintros.is_lambda_function(obj)
        _LOG.debug("act_lambda=%s", act_lambda)
        _LOG.debug("exp_lambda=%s", exp_lambda)
        self.assertEqual(act_lambda, exp_lambda)
        # Try to pickle.
        try:
            file_name = os.path.join(self.get_scratch_space(), "obj.pkl")
            hpickle.to_pickle(obj, file_name)
            act_pickled = True
        except AttributeError as e:
            _LOG.error("e=%s", e)
            act_pickled = False
        _LOG.debug("act_pickled=%s", act_pickled)
        _LOG.debug("exp_pickled=%s", exp_pickled)
        self.assertEqual(act_pickled, exp_pickled)

    def test_lambda1(self) -> None:
        # Local lambda.
        lambda_ = lambda: 0
        func = lambda_
        exp_str = r"<function Test_is_pickleable1.test_lambda1.<locals>.<lambda> at 0x>"
        # A lambda is not bound to an object.
        exp_bound = False
        exp_lambda = True
        # A lambda is not pickleable.
        exp_pickled = False
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_lambda2(self) -> None:
        lambda_ = lambda x: x
        func = lambda_
        exp_str = r"<function Test_is_pickleable1.test_lambda2.<locals>.<lambda> at 0x>"
        # A lambda is not bound to an object.
        exp_bound = False
        exp_lambda = True
        # A lambda is not pickleable.
        exp_pickled = False
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_func1(self) -> None:
        def _hello() -> bool:
            return False

        #
        func = _hello
        exp_str = (
            r"<function Test_is_pickleable1.test_func1.<locals>._hello at 0x>"
        )
        exp_bound = False
        exp_lambda = False
        # A local object is not pickleable.
        exp_pickled = False
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_func2(self) -> None:
        # Global function.
        func = hello
        exp_str = r"<function hello at 0x>"
        exp_bound = False
        exp_lambda = False
        # A global function is pickleable since it's not bound locally or
        # to an object.
        exp_pickled = True
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_method1(self) -> None:
        # A class method but unbound to an object.
        func = _ClassPickleable.say
        exp_str = r"<function _ClassPickleable.say at 0x>"
        exp_bound = False
        exp_lambda = False
        # A unbound class method is actually pickleable.
        exp_pickled = True
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_method2(self) -> None:
        # A static class method.
        func = _ClassPickleable.say2
        exp_str = r"<function _ClassPickleable.say2 at 0x>"
        exp_bound = False
        exp_lambda = False
        exp_pickled = True
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_method3(self) -> None:
        # A bound method.
        class_instance = _ClassPickleable()
        func = class_instance.say
        exp_str = r"<bound method _ClassPickleable.say of <helpers.test.test_hintrospection._ClassPickleable object at 0x>>"
        exp_bound = True
        exp_lambda = False
        # A method bound to an object is just a function, so it's pickleable.
        exp_pickled = True
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)

    def test_method4(self) -> None:
        # A static class method.
        class_instance = _ClassPickleable()
        func = class_instance.say2
        exp_str = r"<function _ClassPickleable.say2 at 0x>"
        exp_bound = False
        exp_lambda = False
        exp_pickled = True
        self.helper(func, exp_str, exp_bound, exp_lambda, exp_pickled)


# #############################################################################
# Test_is_pickleable2
# #############################################################################


class Test_is_pickleable2(hunitest.TestCase):
    def helper(
        self,
        obj: Any,
        mode: str,
        expected: bool,
    ) -> None:
        """
        Check that picklebility is detected correctly for specified mode.
        """
        _LOG.debug("obj=%s", obj)
        actual = hintros.is_pickleable(obj, mode=mode)
        _LOG.debug("actual=%s", actual)
        _LOG.debug("expected=%s", expected)
        self.assertEqual(actual, expected)

    def test_non_callable1(self) -> None:
        obj = [1, "2", 0.3]
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_non_callable2(self) -> None:
        obj = [1, "2", 0.3]
        mode = "try_and_catch"
        expected = True
        self.helper(obj, mode, expected)

    def test_lambda1(self) -> None:
        obj = lambda x: x
        mode = "type_search"
        expected = False
        self.helper(obj, mode, expected)

    def test_lambda2(self) -> None:
        obj = lambda x: x
        mode = "try_and_catch"
        expected = False
        self.helper(obj, mode, expected)

    def test_local_object1(self) -> None:
        def _hello() -> bool:
            return False

        obj = _hello
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_local_object2(self) -> None:
        def _hello() -> bool:
            return False

        obj = _hello
        mode = "try_and_catch"
        expected = False
        self.helper(obj, mode, expected)

    def test_global_object1(self) -> None:
        obj = hello
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_global_object2(self) -> None:
        obj = hello
        mode = "try_and_catch"
        expected = True
        self.helper(obj, mode, expected)

    def test_unbound_class_method1(self) -> None:
        obj = _ClassPickleable.say
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_unbound_class_method2(self) -> None:
        obj = _ClassPickleable.say
        mode = "try_and_catch"
        expected = True
        self.helper(obj, mode, expected)

    def test_static_class_method1(self) -> None:
        obj = _ClassPickleable.say
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_static_class_method2(self) -> None:
        obj = _ClassPickleable.say
        mode = "try_and_catch"
        expected = True
        self.helper(obj, mode, expected)

    def test_bound_to_object_method1(self) -> None:
        class_instance = _ClassPickleable()
        obj = class_instance.say
        mode = "type_search"
        expected = False
        self.helper(obj, mode, expected)

    def test_bound_to_object_method2(self) -> None:
        class_instance = _ClassPickleable()
        obj = class_instance.say
        mode = "try_and_catch"
        expected = True
        self.helper(obj, mode, expected)

    def test_pickleable_class1(self) -> None:
        obj = _ClassPickleable()
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_pickleable_class2(self) -> None:
        obj = _ClassPickleable()
        mode = "try_and_catch"
        expected = True
        self.helper(obj, mode, expected)

    def test_nonpickleable_class1(self) -> None:
        obj = _ClassNonPickleable()
        mode = "type_search"
        expected = True
        self.helper(obj, mode, expected)

    def test_nonpickleable_class2(self) -> None:
        obj = _ClassNonPickleable()
        mode = "try_and_catch"
        expected = False
        self.helper(obj, mode, expected)


# #############################################################################
# Test_get_function_name1
# #############################################################################


def test_function() -> None:
    pass


# #############################################################################
# Test_get_function_name1
# #############################################################################


class Test_get_function_name1(hunitest.TestCase):
    def test1(self) -> None:
        actual = hintros.get_function_name()
        expected = "test1"
        self.assert_equal(actual, expected, purify_text=True)


# #############################################################################
# Test_get_name_from_function1
# #############################################################################


class Test_get_name_from_function1(hunitest.TestCase):
    def test1(self) -> None:
        actual = hintros.get_name_from_function(test_function)
        expected = "helpers.test.test_hintrospection.test_function"
        self.assert_equal(actual, expected, purify_text=True)


# #############################################################################
# Test_get_function_from_string1
# #############################################################################


def dummy_function() -> None:
    pass


# #############################################################################
# Test_get_function_from_string1
# #############################################################################


class Test_get_function_from_string1(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that function is correctly extracted from a string.
        """
        func_str = "helpers.test.test_hintrospection.dummy_function"
        # Compute the actual value.
        act_func = hintros.get_function_from_string(func_str)
        actual = hintros.get_name_from_function(act_func)
        # Compute the expected value.
        exp_func = dummy_function
        expected = hintros.get_name_from_function(exp_func)
        # Run.
        hdbg.dassert_isinstance(act_func, Callable)
        # `expected` is computed dynamically from `dummy_function`, so it
        # carries the same checkout-dependent qualname prefix as `actual`
        # and needs the same purification.
        self.assert_equal(
            actual, expected, purify_text=True, purify_expected_text=True
        )


# #############################################################################
# Test_get_public_methods_as_str
# #############################################################################


class _SampleClassWithMethods:
    """
    Sample class used to test `get_public_methods_as_str()`.
    """

    def method_with_docstring(self, x: int) -> int:
        """
        Double the input value.

        Uses simple multiplication.
        """
        return x * 2

    def method_no_docstring(self) -> None:
        pass


class Test_get_public_methods_as_str(hunitest.TestCase):
    """
    Test `hintrospection.get_public_methods_as_str()` function.
    """

    def helper(self, obj: Any, use_markdown: bool, expected: str) -> None:
        """
        Check the public-methods listing generated for `obj`.

        :param obj: class or instance to inspect
        :param use_markdown: whether to format the output as markdown
        :param expected: expected listing string
        """
        # Run test.
        actual = hintros.get_public_methods_as_str(
            obj, use_markdown=use_markdown
        )
        # Check outputs.
        # `remove_lead_trail_empty_lines` also drops the trailing blank
        # line that `get_public_methods_as_str()` appends after the last
        # method entry in non-markdown mode.
        self.assert_equal(
            actual, expected, dedent=True, remove_lead_trail_empty_lines=True
        )

    def test1(self) -> None:
        """
        Test a class rendered as markdown.

        Methods are listed alphabetically, and a multi-line docstring is
        truncated to its first line with `...`.
        """
        # Prepare inputs.
        obj = _SampleClassWithMethods
        use_markdown = True
        # Prepare outputs.
        expected = """
        **_SampleClassWithMethods**
        - `method_no_docstring(self) -> None`
        - `method_with_docstring(self, x: int) -> int`: Double the input value...
        """
        # Run test.
        self.helper(obj, use_markdown, expected)

    def test2(self) -> None:
        """
        Test the same class rendered as plain text (not markdown).
        """
        # Prepare inputs.
        obj = _SampleClassWithMethods
        use_markdown = False
        # Prepare outputs.
        expected = """
        _SampleClassWithMethods
        method_no_docstring(self) -> None

        method_with_docstring(self, x: int) -> int
            Double the input value...
        """
        # Run test.
        self.helper(obj, use_markdown, expected)

    def test3(self) -> None:
        """
        Test that an instance (not a class) is labeled with its class name.

        Methods look up as bound methods on an instance, so their
        signatures drop the leading `self` parameter.
        """
        # Prepare inputs.
        obj = _SampleClassWithMethods()
        use_markdown = True
        # Prepare outputs.
        expected = """
        **_SampleClassWithMethods**
        - `method_no_docstring() -> None`
        - `method_with_docstring(x: int) -> int`: Double the input value...
        """
        # Run test.
        self.helper(obj, use_markdown, expected)


# #############################################################################
# Test_get_function_info_as_str
# #############################################################################


def _sample_function_with_docstring(x: int, y: str = "a") -> bool:
    """
    Do something with x and y.

    This second line should be truncated away.
    """
    return bool(x) and bool(y)


def _sample_function_one_line_docstring() -> None:
    """
    Do one simple thing.
    """


def _sample_function_no_docstring(x: int) -> int:
    return x


class Test_get_function_info_as_str(hunitest.TestCase):
    """
    Test `hintrospection.get_function_info_as_str()` function.
    """

    def helper(self, obj: Callable, use_markdown: bool, expected: str) -> None:
        """
        Check the info string generated for `obj`.

        :param obj: function to describe
        :param use_markdown: whether to format the output as markdown
        :param expected: expected info string
        """
        # Run test.
        actual = hintros.get_function_info_as_str(
            obj, use_markdown=use_markdown
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test a function with a multi-line docstring rendered as markdown.

        The docstring summary is truncated to its first line with `...`.
        """
        # Prepare inputs.
        obj = _sample_function_with_docstring
        use_markdown = True
        # Prepare outputs.
        expected = (
            "- `_sample_function_with_docstring(x: int, y: str = 'a') -> bool`  \n"
            "  Do something with x and y..."
        )
        # Run test.
        self.helper(obj, use_markdown, expected)

    def test2(self) -> None:
        """
        Test the same function rendered as plain text (not markdown).
        """
        # Prepare inputs.
        obj = _sample_function_with_docstring
        use_markdown = False
        # Prepare outputs.
        expected = """
        _sample_function_with_docstring(x: int, y: str = 'a') -> bool
            Do something with x and y...
        """
        # Run test.
        self.helper(obj, use_markdown, expected)

    def test3(self) -> None:
        """
        Test a function whose docstring is only one line.

        Since there's nothing to truncate, no `...` is appended.
        """
        # Prepare inputs.
        obj = _sample_function_one_line_docstring
        use_markdown = True
        # Prepare outputs.
        expected = (
            "- `_sample_function_one_line_docstring() -> None`  \n"
            "  Do one simple thing."
        )
        # Run test.
        self.helper(obj, use_markdown, expected)

    def test4(self) -> None:
        """
        Test a function with no docstring at all.
        """
        # Prepare inputs.
        obj = _sample_function_no_docstring
        use_markdown = True
        # Prepare outputs.
        expected = "- `_sample_function_no_docstring(x: int) -> int`"
        # Run test.
        self.helper(obj, use_markdown, expected)

    def test5(self) -> None:
        """
        Test `verbose=True` rendered as markdown.

        The entire docstring is printed, not just its first line.
        """
        # Prepare inputs.
        obj = _sample_function_with_docstring
        # Prepare outputs.
        expected = (
            "- `_sample_function_with_docstring(x: int, y: str = 'a') -> bool`  \n"
            "  Do something with x and y.\n"
            "\n"
            "  This second line should be truncated away."
        )
        # Run test.
        actual = hintros.get_function_info_as_str(
            obj, use_markdown=True, verbose=True
        )
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test `verbose=True` rendered as plain text (not markdown).
        """
        # Prepare inputs.
        obj = _sample_function_with_docstring
        # Prepare outputs.
        expected = (
            "_sample_function_with_docstring(x: int, y: str = 'a') -> bool\n"
            "    Do something with x and y.\n"
            "\n"
            "    This second line should be truncated away."
        )
        # Run test.
        actual = hintros.get_function_info_as_str(
            obj, use_markdown=False, verbose=True
        )
        self.assert_equal(actual, expected)


# #############################################################################
# Test_print_obj_info
# #############################################################################


def _sample_function_for_print_obj_info(x: int) -> int:
    """
    Return x unchanged.

    Used only to check that `print_obj_info()` renders a function via
    `get_function_info_as_str()`.
    """
    return x


class _SampleClassForPrintObjInfo:
    """
    Sample class used to check that `print_obj_info()` renders a class via
    `get_public_methods_as_str()`.
    """

    def method1(self, x: int) -> int:
        """
        Double x.
        """
        return x * 2


class Test_print_obj_info(hunitest.TestCase):
    """
    Test `hintrospection.print_obj_info()` function.
    """

    def helper(self, obj: Any, expected: str, **kwargs: Any) -> None:
        """
        Check the Markdown text `print_obj_info()` passes to `display()`.

        :param obj: object passed to `print_obj_info()`
        :param expected: expected Markdown text
        :param kwargs: extra options passed through to `print_obj_info()`
        """
        # Run test: mock only the external `IPython.display.display()` call
        # so the Markdown text it receives can be inspected; everything
        # else (including the real `get_link_to_code()` call) executes
        # normally.
        with umock.patch("IPython.display.display") as display_mock:
            hintros.print_obj_info(obj, **kwargs)
        # Check outputs.
        actual = display_mock.call_args[0][0].data
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test that a function is rendered via `get_function_info_as_str()`.
        """
        # Prepare inputs.
        obj = _sample_function_for_print_obj_info
        # Prepare outputs.
        expected = hintros.get_function_info_as_str(obj, use_markdown=True)
        # Run test.
        self.helper(obj, expected)

    def test2(self) -> None:
        """
        Test that a class is rendered via `get_public_methods_as_str()`.
        """
        # Prepare inputs.
        obj = _SampleClassForPrintObjInfo
        # Prepare outputs.
        expected = hintros.get_public_methods_as_str(obj, use_markdown=True)
        # Run test.
        self.helper(obj, expected)

    def test3(self) -> None:
        """
        Test that `**kwargs` are forwarded to `get_function_info_as_str()`.

        `verbose=True` should print the entire docstring, not just its
        first line.
        """
        # Prepare inputs.
        obj = _sample_function_for_print_obj_info
        # Prepare outputs.
        expected = hintros.get_function_info_as_str(
            obj, use_markdown=True, verbose=True
        )
        # Run test.
        self.helper(obj, expected, verbose=True)


# #############################################################################
# Test_get_link_to_code
# #############################################################################


def _init_git_repo(git_repo: str, *, branch_name: str, remote_url: str) -> None:
    """
    Initialize `git_repo` as a Git repo with a checked-out branch and an
    `origin` remote.

    :param git_repo: path to the (already created) directory to turn
        into a Git repo
    :param branch_name: name of the branch to check out
    :param remote_url: URL to register as the `origin` remote
    """
    _LOG.debug(
        "git_repo=%s branch_name=%s remote_url=%s",
        git_repo,
        branch_name,
        remote_url,
    )
    with hsystem.cd(git_repo):
        hsystem.system("git init", suppress_output=True)
        hsystem.system(
            "git config user.email 'test@test.com'", suppress_output=True
        )
        hsystem.system(
            "git config user.name 'Test User'", suppress_output=True
        )
        # Check out a known branch name so the test doesn't depend on the
        # host's `init.defaultBranch` config (e.g., `main` vs `master`).
        hsystem.system(f"git checkout -b {branch_name}", suppress_output=True)
        hsystem.system(
            f"git remote add origin {remote_url}", suppress_output=True
        )


def _commit_all(git_repo: str) -> None:
    """
    Stage and commit all files in `git_repo`.

    A commit is needed for `git rev-parse --abbrev-ref HEAD` (used by
    `hgit.get_branch_name()`) to resolve on a freshly initialized repo.

    :param git_repo: path to the Git repo
    """
    with hsystem.cd(git_repo):
        hsystem.system("git add -A", suppress_output=True)
        hsystem.system(
            "git commit -m 'initial commit'", suppress_output=True
        )


def _load_module_from_file(
    file_path: str, module_name: str
) -> types.ModuleType:
    """
    Import `file_path` as a standalone module named `module_name`.

    Used to obtain real function/class objects whose code points at
    `file_path`, so `inspect.getsourcefile()`/`getsourcelines()` resolve
    against it exactly like they would for a normally imported module. The
    module is registered in `sys.modules` (like a normal import would do)
    since `inspect` resolves a class's file via
    `sys.modules[cls.__module__].__file__`.

    :param file_path: path to the `.py` file to load
    :param module_name: name to register the module under
    :return: the loaded module
    """
    _LOG.debug("file_path=%s module_name=%s", file_path, module_name)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    hdbg.dassert_is_not(
        spec, None, "Can't create module spec for '%s'", file_path
    )
    spec = cast(importlib.machinery.ModuleSpec, spec)
    hdbg.dassert_is_not(
        spec.loader, None, "Module spec for '%s' has no loader", file_path
    )
    loader = cast(importlib.abc.Loader, spec.loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module


class Test_get_link_to_code(hunitest.TestCase):
    """
    Test `hintrospection.get_link_to_code()` function.
    """

    def _create_repo_with_module(
        self, file_content: str, *, rel_path: str = "module.py"
    ) -> types.ModuleType:
        """
        Create a Git repo containing a committed module at `rel_path` and
        import it.

        :param file_content: source code to write to the module file
        :param rel_path: path of the module file relative to the repo
            root
        :return: the imported module, backed by a file inside the new
            repo
        """
        # Prepare inputs: a Git repo with a known remote and branch,
        # containing one committed module file.
        scratch_dir = self.get_scratch_space()
        git_repo = os.path.join(scratch_dir, "repo")
        hio.create_dir(git_repo, incremental=False)
        remote_url = "git@github.com:test_owner/test_repo.git"
        _init_git_repo(
            git_repo, branch_name="test_branch", remote_url=remote_url
        )
        module_file = os.path.join(git_repo, rel_path)
        hio.to_file(module_file, file_content)
        _commit_all(git_repo)
        # Import the module under a name unique to this test so that
        # concurrent/repeated test runs don't clobber each other's entry in
        # `sys.modules`.
        module_name = "tmp_module_" + self.id().replace(".", "_")
        module = _load_module_from_file(module_file, module_name)
        return module

    def test1(self) -> None:
        """
        Test the link for a function defined on the first line of a file.
        """
        # Prepare inputs.
        file_content = "def foo():\n    pass\n"
        module = self._create_repo_with_module(file_content)
        # Prepare outputs.
        expected = (
            "https://github.com/test_owner/test_repo/blob/test_branch/"
            "module.py#L1"
        )
        # Run test.
        actual = hintros.get_link_to_code(module.foo)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test the link for a class defined after leading comments and blank
        lines, i.e., the reported line matches the `class` line, not line 1.
        """
        # Prepare inputs.
        file_content = (
            "# A leading comment.\n"
            "\n"
            "\n"
            "class Bar:\n"
            "    def method(self) -> None:\n"
            "        pass\n"
        )
        module = self._create_repo_with_module(file_content)
        # Prepare outputs.
        expected = (
            "https://github.com/test_owner/test_repo/blob/test_branch/"
            "module.py#L4"
        )
        # Run test.
        actual = hintros.get_link_to_code(module.Bar)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that a decorated function's link points at the decorator line,
        not the `def` line, matching `inspect.getsourcelines()` semantics.
        """
        # Prepare inputs.
        file_content = (
            "def identity_decorator(func):\n"
            "    return func\n"
            "\n"
            "\n"
            "@identity_decorator\n"
            "def decorated_foo():\n"
            "    pass\n"
        )
        module = self._create_repo_with_module(file_content)
        # Prepare outputs.
        expected = (
            "https://github.com/test_owner/test_repo/blob/test_branch/"
            "module.py#L5"
        )
        # Run test.
        actual = hintros.get_link_to_code(module.decorated_foo)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that the relative path is correct for a module nested inside a
        subdirectory of the Git repo.
        """
        # Prepare inputs.
        file_content = "def foo():\n    pass\n"
        module = self._create_repo_with_module(
            file_content, rel_path=os.path.join("pkg", "sub", "module.py")
        )
        # Prepare outputs.
        expected = (
            "https://github.com/test_owner/test_repo/blob/test_branch/"
            "pkg/sub/module.py#L1"
        )
        # Run test.
        actual = hintros.get_link_to_code(module.foo)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test that `use_master=True` points at the `master` branch regardless
        of the currently checked-out branch.
        """
        # Prepare inputs.
        file_content = "def foo():\n    pass\n"
        module = self._create_repo_with_module(file_content)
        # Prepare outputs.
        expected = (
            "https://github.com/test_owner/test_repo/blob/master/"
            "module.py#L1"
        )
        # Run test.
        actual = hintros.get_link_to_code(module.foo, use_master=True)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test that an object with no retrievable source file (e.g., defined
        via `exec()` with no backing file) raises an assertion instead of
        silently returning a link with a wrong (or stale) line number.
        """
        # Prepare inputs: a function compiled without a real backing file,
        # so `inspect.getsourcefile()` returns `None`.
        code = compile("def foo():\n    pass\n", "<string>", "exec")
        namespace: Dict[str, Any] = {}
        exec(code, namespace)
        foo = namespace["foo"]
        # Run test.
        with self.assertRaises(AssertionError):
            hintros.get_link_to_code(foo)
