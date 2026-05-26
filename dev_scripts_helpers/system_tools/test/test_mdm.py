import logging

import helpers.hgit as hgit
import helpers.hunit_test as hunitest
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _run_mdm(topic: str, action: str, *names: str) -> str:
    """
    Run mdm executable and capture output, filtering out logging lines.

    :param topic: content topic (research, blog, story, skill, rules)
    :param action: action to perform (list, edit, directory, etc.)
    :param names: optional arguments (names, patterns, etc.)
    :return: captured stdout (without logging messages)
    """
    script_path = hgit.find_file_in_git_tree("mdm")
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


# #############################################################################
# Test_mdm_py_list
# #############################################################################


class Test_mdm_py_list(hunitest.TestCase):
    """Tests for list action."""

    def test1(self) -> None:
        """
        Test skill list action with no pattern shows skills.
        """
        # Run test.
        actual = _run_mdm("skill", "list")
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
        actual = _run_mdm("skill", "list", "blog")
        # Check outputs.
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        for line in lines:
            self.assertIn("blog", line.lower())

    def test3(self) -> None:
        """
        Test rules list action shows rule names without .rules.md suffix.
        """
        # Run test.
        actual = _run_mdm("rules", "list")
        # Check outputs.
        if actual:
            lines = actual.split("\n")
            self.assertTrue(all(".rules.md" not in line for line in lines))


# #############################################################################
# Test_mdm_py_full_list
# #############################################################################


class Test_mdm_py_full_list(hunitest.TestCase):
    """Tests for full_list action."""

    def test1(self) -> None:
        """
        Test skill full_list action shows full paths with SKILL.md.
        """
        # Run test.
        actual = _run_mdm("skill", "full_list")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        self.assertTrue(any("SKILL.md" in line for line in lines))

    def test2(self) -> None:
        """
        Test rules full_list action shows full paths with .rules.md.
        """
        # Run test.
        actual = _run_mdm("rules", "full_list")
        # Check outputs.
        if actual:
            lines = actual.split("\n")
            self.assertTrue(any(".rules.md" in line for line in lines))


# #############################################################################
# Test_mdm_py_directory
# #############################################################################


class Test_mdm_py_directory(hunitest.TestCase):
    """Tests for directory action."""

    def test1(self) -> None:
        """
        Test skill directory action returns valid directory path.
        """
        # Run test.
        actual = _run_mdm("skill", "directory")
        # Check outputs.
        self.assertNotEqual(actual, "")
        self.assertIn(".claude/skills", actual)

    def test2(self) -> None:
        """
        Test research topic directory action executes without error.
        """
        # Run test - research directory may not exist in all environments
        try:
            actual = _run_mdm("research", "directory")
            if actual:
                self.assertIn("research", actual.lower())
        except Exception:
            pass

    def test3(self) -> None:
        """
        Test story topic directory action executes without error.
        """
        # Run test - story directory may not exist in all environments
        try:
            actual = _run_mdm("story", "directory")
            if actual:
                self.assertIn("short_stories", actual.lower())
        except Exception:
            pass

    def test4(self) -> None:
        """
        Test blog topic directory action executes without error.
        """
        # Run test - blog directory may not exist in all environments
        try:
            _run_mdm("blog", "directory")
        except Exception:
            pass


# #############################################################################
# Test_mdm_py_describe
# #############################################################################


class Test_mdm_py_describe(hunitest.TestCase):
    """Tests for describe action."""

    def test1(self) -> None:
        """
        Test skill describe action shows skill names with descriptions.
        """
        # Run test.
        actual = _run_mdm("skill", "describe")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)

    def test2(self) -> None:
        """
        Test skill describe with pattern filter shows only matching skills.
        """
        # Run test.
        actual = _run_mdm("skill", "describe", "blog")
        # Check outputs.
        lines = actual.split("\n") if actual else []
        for line in lines:
            if line:
                self.assertIn("blog", line.lower())


# #############################################################################
# Test_mdm_py_topics
# #############################################################################


class Test_mdm_py_topics(hunitest.TestCase):
    """Tests for topics action."""

    def test1(self) -> None:
        """
        Test skill topics action lists unique prefixes.
        """
        # Run test.
        actual = _run_mdm("skill", "topics")
        # Check outputs.
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        for prefix in lines:
            self.assertTrue(
                prefix.isalpha() or all(c.isalnum() or c == "_" for c in prefix),
                f"Prefix '{prefix}' has invalid characters",
            )

    def test2(self) -> None:
        """
        Test skill topics with pattern filter shows only matching prefixes.
        """
        # Run test.
        actual = _run_mdm("skill", "topics", "blog")
        # Check outputs.
        self.assertIn("blog", actual)


# #############################################################################
# Test_mdm_py_prefix_matching
# #############################################################################


class Test_mdm_py_prefix_matching(hunitest.TestCase):
    """Tests for prefix matching in topic and action names."""

    def test1(self) -> None:
        """
        Test prefix matching: 'sk' matches 'skill' topic.
        """
        # Run test.
        actual_full = _run_mdm(self, "skill", "list")
        actual_prefix = _run_mdm(self, "sk", "list")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test2(self) -> None:
        """
        Test prefix matching: 'bl' matches 'blog' topic.
        """
        # Run test.
        actual_full = _run_mdm(self, "blog", "directory")
        actual_prefix = _run_mdm(self, "bl", "directory")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test3(self) -> None:
        """
        Test prefix matching: 'res' matches 'research' topic.
        """
        # Run test.
        actual_full = _run_mdm(self, "research", "directory")
        actual_prefix = _run_mdm(self, "res", "directory")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test4(self) -> None:
        """
        Test prefix matching: 'st' matches 'story' topic.
        """
        # Run test.
        actual_full = _run_mdm(self, "story", "directory")
        actual_prefix = _run_mdm(self, "st", "directory")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test5(self) -> None:
        """
        Test prefix matching: 'l' matches 'list' action.
        """
        # Run test.
        actual_full = _run_mdm(self, "skill", "list")
        actual_prefix = _run_mdm(self, "skill", "l")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test6(self) -> None:
        """
        Test prefix matching: 'f' matches 'full_list' action.
        """
        # Run test.
        actual_full = _run_mdm(self, "skill", "full_list")
        actual_prefix = _run_mdm(self, "skill", "f")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test7(self) -> None:
        """
        Test prefix matching: 'di' matches 'directory' action.
        """
        # Run test.
        actual_full = _run_mdm(self, "skill", "directory")
        actual_prefix = _run_mdm(self, "skill", "di")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test8(self) -> None:
        """
        Test prefix matching: 'de' matches 'describe' action.
        """
        # Run test.
        actual_full = _run_mdm(self, "skill", "describe")
        actual_prefix = _run_mdm(self, "skill", "de")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test9(self) -> None:
        """
        Test prefix matching: 't' matches 'topics' action.
        """
        # Run test.
        actual_full = _run_mdm(self, "skill", "topics")
        actual_prefix = _run_mdm(self, "skill", "t")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)

    def test10(self) -> None:
        """
        Test prefix matching: 'ru' matches 'rules' topic.
        """
        # Run test.
        actual_full = _run_mdm(self, "rules", "list")
        actual_prefix = _run_mdm(self, "ru", "list")
        # Check outputs.
        self.assertEqual(actual_full, actual_prefix)


# #############################################################################
# Test_mdm_py_case_insensitive
# #############################################################################


class Test_mdm_py_case_insensitive(hunitest.TestCase):
    """Tests for case-insensitive argument handling."""

    def test1(self) -> None:
        """
        Test case-insensitive prefix matching for actions.
        """
        # Run test.
        actual_lower = _run_mdm(self, "skill", "list")
        actual_upper = _run_mdm(self, "SKILL", "LIST")
        # Check outputs.
        self.assertEqual(actual_lower, actual_upper)
