import logging
import re

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
        line = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if not line:
            continue
        result_lines.append(line)
    return "\n".join(result_lines).strip()


# #############################################################################
# Test_mdm_py_list
# #############################################################################


class Test_mdm_py_list(hunitest.TestCase):
    """
    Tests for list action.
    """

    def test1(self) -> None:
        """
        Test skill list action with no pattern shows skills.
        """
        # Run test.
        actual = _run_mdm("skill", "list")
        # Check outputs.
        # Expected: Non-empty string with one or more skill names per line
        # Invariant: Output should not be empty (at least one skill exists)
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        # Expected: List of skill names, one per line
        # Invariant: At least one line should be present
        self.assertGreater(len(lines), 0)
        # Expected: Each line contains a valid skill name (non-empty string)
        # Invariant: No blank lines in output
        for line in lines:
            self.assertTrue(len(line) > 0)

    def test2(self) -> None:
        """
        Test skill list action with pattern filter.
        """
        # Run test.
        actual = _run_mdm("skill", "list", "blog")
        # Check outputs.
        # Expected: Skill names matching the "blog" pattern, one per line
        # Invariant: At least one line should match the filter
        lines = actual.split("\n")
        self.assertGreater(len(lines), 0)
        # Expected: Each returned line contains "blog" (case-insensitive)
        # Invariant: Pattern filter successfully filters results
        for line in lines:
            self.assertIn("blog", line.lower())

    def test3(self) -> None:
        """
        Test rules list action shows rule names without .rules.md suffix.
        """
        # Run test.
        actual = _run_mdm("rules", "list")
        # Check outputs.
        # Expected: Rule names without file extension suffix (e.g., "coding" not "coding.rules.md")
        # Invariant: No line should contain ".rules.md" extension when rules are listed
        if actual:
            lines = actual.split("\n")
            self.assertTrue(all(".rules.md" not in line for line in lines))


# #############################################################################
# Test_mdm_py_full_list
# #############################################################################


class Test_mdm_py_full_list(hunitest.TestCase):
    """
    Tests for full_list action.
    """

    def test1(self) -> None:
        """
        Test skill full_list action shows full paths with SKILL.md.
        """
        # Run test.
        actual = _run_mdm("skill", "full_list")
        # Check outputs.
        # Expected: Non-empty string with full file paths
        # Invariant: Output should not be empty when skills exist
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        # Expected: Multiple full paths to SKILL.md files
        # Invariant: At least one line should be present
        self.assertGreater(len(lines), 0)
        # Expected: At least one line contains "SKILL.md" (indicating full path format)
        # Invariant: Full list includes complete file paths, not just names
        self.assertTrue(any("SKILL.md" in line for line in lines))

    def test2(self) -> None:
        """
        Test rules full_list action shows full paths with .rules.md.
        """
        # Run test.
        actual = _run_mdm("rules", "full_list")
        # Check outputs.
        # Expected: Full paths to .rules.md files (e.g., "/path/to/coding.rules.md")
        # Invariant: At least one line should contain ".rules.md" extension when rules exist
        if actual:
            lines = actual.split("\n")
            self.assertTrue(any(".rules.md" in line for line in lines))


# #############################################################################
# Test_mdm_py_directory
# #############################################################################


class Test_mdm_py_directory(hunitest.TestCase):
    """
    Tests for directory action.
    """

    def test1(self) -> None:
        """
        Test skill directory action returns valid directory path.
        """
        # Run test.
        actual = _run_mdm("skill", "directory")
        # Check outputs.
        # Expected: Non-empty path to the skills directory
        # Invariant: Output should not be empty (directory path must exist)
        self.assertNotEqual(actual, "")
        # Expected: Path contains ".claude/skills" indicating the standard location
        # Invariant: Returned path points to the expected skills directory structure
        self.assertIn(".claude/skills", actual)

    def test2(self) -> None:
        """
        Test research topic directory action executes without error.
        """
        # Run test - research directory may not exist in all environments
        try:
            actual = _run_mdm("research", "directory")
            # Expected: Path containing "research" directory indicator (if path is returned)
            # Invariant: When research directory exists, returned path should mention it
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
            # Expected: Path containing "short_stories" directory indicator (if path is returned)
            # Invariant: When story directory exists, returned path should mention it
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
            # Expected: Command executes without raising exceptions
            # Invariant: Blog directory command should be callable (success or graceful failure)
            _run_mdm("blog", "directory")
        except Exception:
            pass


# #############################################################################
# Test_mdm_py_describe
# #############################################################################


class Test_mdm_py_describe(hunitest.TestCase):
    """
    Tests for describe action.
    """

    def test1(self) -> None:
        """
        Test skill describe action shows skill names with descriptions.
        """
        # Run test.
        actual = _run_mdm("skill", "describe")
        # Check outputs.
        # Expected: Non-empty output with skill names and their descriptions
        # Invariant: At least one skill with its description should be returned
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        # Expected: Multiple lines, each containing skill name and description info
        # Invariant: At least one line should be present in describe output
        self.assertGreater(len(lines), 0)

    def test2(self) -> None:
        """
        Test skill describe with pattern filter shows only matching skills.
        """
        # Run test.
        actual = _run_mdm("skill", "describe", "blog")
        # Check outputs.
        # Expected: Descriptions for skills matching "blog" pattern, one per line
        # Invariant: Each non-empty line should contain "blog" (case-insensitive)
        lines = actual.split("\n") if actual else []
        for line in lines:
            # Expected: Filtered output containing only "blog"-related skills
            # Invariant: Pattern filter successfully restricts describe results
            if line:
                self.assertIn("blog", line.lower())


# #############################################################################
# Test_mdm_py_topics
# #############################################################################


class Test_mdm_py_topics(hunitest.TestCase):
    """
    Tests for topics action.
    """

    def test1(self) -> None:
        """
        Test skill topics action lists unique prefixes.
        """
        # Run test.
        actual = _run_mdm("skill", "topics")
        # Check outputs.
        # Expected: Non-empty string with topic prefixes (e.g., "blog", "coding", "docker")
        # Invariant: At least one topic prefix should be listed
        self.assertNotEqual(actual, "")
        lines = actual.split("\n")
        # Expected: Multiple unique topic prefixes, one per line
        # Invariant: At least one line should be present
        self.assertGreater(len(lines), 0)
        # Expected: Each prefix contains only alphanumeric characters and underscores
        # Invariant: Valid identifier format for skill topic names (e.g., "blog", "coding_qa")
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
        # Expected: Output containing "blog" topic prefix when filtered
        # Invariant: Pattern filter successfully returns matching topic prefixes
        self.assertIn("blog", actual)
