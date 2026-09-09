import os
from typing import Dict, List

import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_find as hltltafi


# #############################################################################
# Test_find_test_class_ast1
# #############################################################################


class Test_find_test_class_ast1(hunitest.TestCase):
    def _create_test_files(self, file_dict: Dict[str, str]) -> List[str]:
        test_dir = os.path.join(self.get_scratch_space(), "test")
        file_dict = {
            file_name: hprint.dedent(source)
            for file_name, source in file_dict.items()
        }
        hunitest.create_test_dir(test_dir, incremental=True, file_dict=file_dict)
        return sorted(os.path.join(test_dir, name) for name in file_dict)

    def test_plain_and_multiline_classes_are_found(self) -> None:
        file_names = self._create_test_files(
            {
                "test_classes.py": """
                    class TestPlain:
                        pass

                    class TestMultiline(
                        object,
                    ):
                        pass
                """
            }
        )
        actual = hltltafi._find_test_class(
            "Test", list(reversed(file_names)) + file_names
        )
        expected = [
            f"{file_names[0]}::TestMultiline",
            f"{file_names[0]}::TestPlain",
        ]
        self.assertEqual(actual, expected)

    def test_strings_and_comments_are_ignored(self) -> None:
        file_names = self._create_test_files(
            {
                "test_non_code.py": '''
                    """
                    class TestInString(object):
                        pass
                    """
                    # class TestInComment(object):
                '''
            }
        )
        self.assertEqual(hltltafi._find_test_class("Test", file_names), [])

    def test_exact_and_substring_matching(self) -> None:
        file_names = self._create_test_files(
            {
                "test_names.py": """
                    class TestAlpha:
                        pass

                    class TestAlphabet:
                        pass
                """
            }
        )
        prefix = f"{file_names[0]}::"
        exact = hltltafi._find_test_class(
            "TestAlpha", file_names, exact_match=True
        )
        substring = hltltafi._find_test_class("TestAlpha", file_names)
        self.assertEqual(exact, [prefix + "TestAlpha"])
        self.assertEqual(
            substring, [prefix + "TestAlpha", prefix + "TestAlphabet"]
        )

    def test_nested_classes_are_qualified_and_function_locals_ignored(
        self,
    ) -> None:
        file_names = self._create_test_files(
            {
                "test_nested.py": """
                    if True:
                        class TestConditional:
                            pass

                    class TestOuter:
                        if True:
                            class TestInner:
                                pass

                    def make_class():
                        class TestLocal:
                            pass

                    async def make_async_class():
                        class TestAsyncLocal:
                            pass
                """
            }
        )
        prefix = f"{file_names[0]}::"
        actual = hltltafi._find_test_class("Test", file_names)
        expected = [
            prefix + "TestConditional",
            prefix + "TestOuter",
            prefix + "TestOuter::TestInner",
        ]
        self.assertEqual(actual, expected)

    def test_classes_in_control_flow_blocks_are_found(self) -> None:
        file_names = self._create_test_files(
            {
                "test_blocks.py": """
                    try:
                        class TestTry:
                            pass
                    except Exception:
                        class TestExcept:
                            pass

                    with open(__file__):
                        class TestWith:
                            pass

                    for value in []:
                        class TestFor:
                            pass

                    while False:
                        class TestWhile:
                            pass
                """
            }
        )
        prefix = f"{file_names[0]}::"
        actual = hltltafi._find_test_class("Test", file_names)
        expected = [
            prefix + "TestExcept",
            prefix + "TestFor",
            prefix + "TestTry",
            prefix + "TestWhile",
            prefix + "TestWith",
        ]
        self.assertEqual(actual, expected)

    def test_malformed_file_warns_and_valid_files_are_still_searched(
        self,
    ) -> None:
        file_names = self._create_test_files(
            {
                "test_broken.py": "class TestBroken(\n",
                "test_valid.py": """
                    class TestValid:
                        pass
                """,
            }
        )
        with self.assertLogs(
            "helpers.lib_tasks.lib_tasks_find_class", level="WARNING"
        ) as captured:
            actual = hltltafi._find_test_class("TestValid", file_names)
        self.assertEqual(actual, [f"{file_names[1]}::TestValid"])
        warning = "\n".join(captured.output)
        self.assertIn("Skipping malformed Python file", warning)
        self.assertIn(file_names[0], warning)
        self.assertIn("line 1", warning)
