"""Test the independent source inventory used by the pytest sanity checker."""

import os
import pprint
from typing import Dict

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hpytest_sanity_inventory as hpysainv
import helpers.hunit_test as hunitest


# #############################################################################
# Test_collect_source_tests
# #############################################################################


class Test_collect_source_tests(hunitest.TestCase):
    """Test `helpers.hpytest_sanity_inventory.collect_source_tests()`."""

    def helper(self, files: Dict[str, str]) -> hpysainv.SourceInventory:
        """Write a real source tree and scan it without importing modules."""
        root = self.get_scratch_space()
        for path, content in files.items():
            full_path = os.path.join(root, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            hio.to_file(full_path, hprint.dedent(content))
        file_patterns = ("test_*.py", "*_test.py")
        class_patterns = ("Test",)
        function_patterns = ("test",)
        excluded_dirs = (".git",)
        return hpysainv.collect_source_tests(
            root, file_patterns, class_patterns, function_patterns, excluded_dirs
        )

    def test1(self) -> None:
        """Find tests in omitted directories without executing module code."""
        # Prepare inputs.
        files = {
            "omitted/test_a.py": """
            raise RuntimeError('must not import')
            def test1():
                def test_local():
                    pass
            async def test2():
                pass
            class TestOuter:
                def test3(self):
                    pass
                class TestInner:
                    def test4(self):
                        pass
            """
        }
        expected = [
            "omitted/test_a.py::TestOuter::TestInner::test4",
            "omitted/test_a.py::TestOuter::test3",
            "omitted/test_a.py::test1",
            "omitted/test_a.py::test2",
        ]
        # Run test.
        actual = self.helper(files)
        # Check outputs.
        self.assert_equal(
            pprint.pformat(sorted(actual.tests)), pprint.pformat(expected)
        )
        self.assertEqual(len(actual.errors), 0)

    def test2(self) -> None:
        """Preserve local inherited methods and explicit disabled classes."""
        # Prepare inputs.
        files = {
            "test_a.py": """
            import unittest
            class Base:
                def test_inherited(self):
                    pass
            class TestChild(Base):
                def test_own(self):
                    pass
            class Legacy(unittest.TestCase):
                def test_old(self):
                    pass
            class TestDisabled:
                __test__ = False
                def test_hidden(self):
                    pass
            """
        }
        expected = {
            "test_a.py::Legacy::test_old": "",
            "test_a.py::TestChild::test_inherited": "",
            "test_a.py::TestChild::test_own": "",
            "test_a.py::TestDisabled::test_hidden": "class __test__ = False",
        }
        # Run test.
        inventory = self.helper(files)
        actual = {
            key: value.excluded_reason for key, value in inventory.tests.items()
        }
        # Check outputs.
        self.assert_equal(pprint.pformat(actual), pprint.pformat(expected))

    def test5(self) -> None:
        """Expose imported inheritance and dynamic module definitions as
        uncertain.
        """
        files = {
            "test_a.py": """
            from external import Base
            class TestImported(Base):
                def test_local(self):
                    setattr(self, 'value', 1)
            globals()['test_generated'] = lambda: None
            """
        }
        actual = self.helper(files)
        self.assertEqual(len(actual.uncertainties), 2)
        self.assertEqual(len(actual.tests), 1)

    def test6(self) -> None:
        """Discover conditional class methods without executing their
        conditions.
        """
        files = {
            "test_a.py": """
            class TestConditional:
                if feature_enabled:
                    def test_optional(self):
                        pass
            """
        }
        actual = self.helper(files)
        self.assertEqual(
            actual.tests[
                "test_a.py::TestConditional::test_optional"
            ].uncertain_reason,
            "conditional source definition",
        )

    def test3(self) -> None:
        """Report syntax errors without losing valid files in the same tree."""
        # Prepare inputs.
        files = {
            "test_bad.py": "def invalid(:",
            "test_good.py": "def test1(): pass",
        }
        expected = (["test_good.py::test1"], ["test_bad.py"])
        # Run test.
        inventory = self.helper(files)
        actual = (sorted(inventory.tests), sorted(inventory.errors))
        # Check outputs.
        self.assert_equal(pprint.pformat(actual), pprint.pformat(expected))

    def test4(self) -> None:
        """Retain conditional tests without asserting the branch was executed."""
        # Prepare inputs.
        files = {
            "test_a.py": """
            if unknown_feature:
                def test_conditional():
                    pass
            else:
                class TestConditional:
                    def test_method(self):
                        pass
            """
        }
        expected = {
            "test_a.py::TestConditional::test_method": "conditional source definition",
            "test_a.py::test_conditional": "conditional source definition",
        }
        # Run test.
        inventory = self.helper(files)
        actual = {
            key: item.uncertain_reason for key, item in inventory.tests.items()
        }
        # Check outputs.
        self.assert_equal(pprint.pformat(actual), pprint.pformat(expected))
