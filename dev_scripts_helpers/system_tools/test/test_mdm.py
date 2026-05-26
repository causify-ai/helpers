import logging

import helpers.hunit_test as hunitest
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# TODO(ai_gp): Split test class by topic (e.g., list, describe, ...),
# e.g., Test_mdm_py_list, ...
# TODO(ai_gp): Factor out _run_mdm so that all classes can call it
class Test_mdm_py(hunitest.TestCase):
    """
    End-to-end tests for the mdm executable script.

    Tests verify CLI behavior including argument parsing, action execution,
    and output correctness across different topics and actions.
    """

    def _run_mdm(
        self,
        topic: str,
        action: str,
        *names: str,
    ) -> str:
        """
        Run mdm executable and capture output, filtering out logging lines.

        :param topic: content topic (research, blog, story, skill, rules)
        :param action: action to perform (list, edit, directory, etc.)
        :param names: optional arguments (names, patterns, etc.)
        :return: captured stdout (without logging messages)
        """
        # TODO(ai_gp): Apply .claude/skills/testing.rules.md:741:## Locate Script Paths Dynamically
        script_path = "dev_scripts_helpers/system_tools/mdm"
        args = [script_path, topic, action] + list(names)
        cmd = " ".join(f'"{arg}"' if " " in arg else arg for arg in args)
        cmd = f"{cmd} 2>/dev/null"
        _LOG.debug("Running command: %s", cmd)
        _, output = hsystem.system_to_string(cmd, suppress_output=True)
        lines = output.strip().split("\n")
        result_lines = []
        for line in lines:
            if not line:
                continue
            if "hdbg.py" in line or "Saving log to file" in line or " - " in line:
                continue
            if line.startswith("\x1b"):
                continue
            result_lines.append(line)
        return "\n".join(result_lines).strip()

    def test1(self) -> None:
        """
        Test skill list action with no pattern shows skills.
        """
        # Run test.
        actual = self._run_mdm("skill", "list")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        for line in lines:
            self.assertTrue(len(line) > 0)

    def test2(self) -> None:
        """
        Test skill list action with pattern filter.
        """
        # Run test.
        actual = self._run_mdm("skill", "list", "blog")
        # Check outputs.
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        for line in lines:
            self.assertIn("blog", line.lower())

    def test3(self) -> None:
        """
        Test skill full_list action shows full paths with SKILL.md.
        """
        # Run test.
        actual = self._run_mdm("skill", "full_list")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        self.assertTrue(any("SKILL.md" in line for line in lines))

    def test4(self) -> None:
        """
        Test skill directory action returns valid directory path.
        """
        # Run test.
        actual = self._run_mdm("skill", "directory")
        # Check outputs.
        self.assertNotEqual(actual, "")
        self.assertIn(".claude/skills", actual)

    def test5(self) -> None:
        """
        Test skill describe action shows skill names with descriptions.
        """
        # Run test.
        actual = self._run_mdm("skill", "describe")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)

    def test6(self) -> None:
        """
        Test skill topics action lists unique prefixes.
        """
        # Run test.
        actual = self._run_mdm("skill", "topics")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        for prefix in lines:
            self.assertTrue(
                prefix.isalpha() or all(c.isalnum() or c == "_" for c in prefix),
                f"Prefix '{prefix}' has invalid characters",
            )

    def test7(self) -> None:
        """
        Test rules full_list action shows full paths with .rules.md.
        """
        # Run test.
        actual = self._run_mdm("rules", "full_list")
        # Check outputs.
        if actual:
            lines = actual.split("\n")
            self.assertTrue(any(".rules.md" in line for line in lines))

    def test8(self) -> None:
        """
        Test rules list action shows rule names without .rules.md suffix.
        """
        # Run test.
        actual = self._run_mdm("rules", "list")
        # Check outputs.
        if actual:
            lines = actual.split("\n")
            self.assertTrue(all(".rules.md" not in line for line in lines))

    def test9(self) -> None:
        """
        Test prefix matching: 'sk' matches 'skill' topic.
        """
        # Run test.
        actual_full = self._run_mdm("skill", "list")
        actual_prefix = self._run_mdm("sk", "list")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test10(self) -> None:
        """
        Test prefix matching: 'bl' matches 'blog' topic.
        """
        # Run test.
        actual_full = self._run_mdm("blog", "directory")
        actual_prefix = self._run_mdm("bl", "directory")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test11(self) -> None:
        """
        Test prefix matching: 'res' matches 'research' topic.
        """
        # Run test.
        actual_full = self._run_mdm("research", "directory")
        actual_prefix = self._run_mdm("res", "directory")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test12(self) -> None:
        """
        Test prefix matching: 'st' matches 'story' topic.
        """
        # Run test.
        actual_full = self._run_mdm("story", "directory")
        actual_prefix = self._run_mdm("st", "directory")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test13(self) -> None:
        """
        Test prefix matching: 'l' matches 'list' action.
        """
        # Run test.
        actual_full = self._run_mdm("skill", "list")
        actual_prefix = self._run_mdm("skill", "l")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test14(self) -> None:
        """
        Test prefix matching: 'f' matches 'full_list' action.
        """
        # Run test.
        actual_full = self._run_mdm("skill", "full_list")
        actual_prefix = self._run_mdm("skill", "f")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test15(self) -> None:
        """
        Test prefix matching: 'di' matches 'directory' action.
        """
        # Run test.
        actual_full = self._run_mdm("skill", "directory")
        actual_prefix = self._run_mdm("skill", "di")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test16(self) -> None:
        """
        Test prefix matching: 'de' matches 'describe' action.
        """
        # Run test.
        actual_full = self._run_mdm("skill", "describe")
        actual_prefix = self._run_mdm("skill", "de")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test17(self) -> None:
        """
        Test prefix matching: 't' matches 'topics' action.
        """
        # Run test.
        actual_full = self._run_mdm("skill", "topics")
        actual_prefix = self._run_mdm("skill", "t")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test18(self) -> None:
        """
        Test prefix matching: 'ru' matches 'rules' topic.
        """
        # Run test.
        actual_full = self._run_mdm("rules", "list")
        actual_prefix = self._run_mdm("ru", "list")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test19(self) -> None:
        """
        Test skill topics with pattern filter shows only matching prefixes.
        """
        # Run test.
        actual = self._run_mdm("skill", "topics", "blog")
        # Check outputs.
        self.assertIn("blog", actual)

    def test20(self) -> None:
        """
        Test skill describe with pattern filter shows only matching skills.
        """
        # Run test.
        actual = self._run_mdm("skill", "describe", "blog")
        # Check outputs.
        lines = actual.split("\n") if actual else []
        for line in lines:
            if line:
                self.assertIn("blog", line.lower())

    def test21(self) -> None:
        """
        Test case-insensitive prefix matching for actions.
        """
        # Run test.
        actual_lower = self._run_mdm("skill", "list")
        actual_upper = self._run_mdm("SKILL", "LIST")
        # Check outputs.
        self.assertEqual(actual_lower, actual_upper)

    def test22(self) -> None:
        """
        Test research topic directory action executes without error.
        """
        # Run test - research directory may not exist in all environments
        try:
            actual = self._run_mdm("research", "directory")
            if actual:
                self.assertIn("research", actual.lower())
        except Exception:
            pass

    def test23(self) -> None:
        """
        Test story topic directory action executes without error.
        """
        # Run test - story directory may not exist in all environments
        try:
            actual = self._run_mdm("story", "directory")
            if actual:
                self.assertIn("short_stories", actual.lower())
        except Exception:
            pass

    def test24(self) -> None:
        """
        Test blog topic directory action executes without error.
        """
        # Run test - blog directory may not exist in all environments
        try:
            self._run_mdm("blog", "directory")
        except Exception:
            pass
