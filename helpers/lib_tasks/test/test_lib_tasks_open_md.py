import logging

import helpers.hunit_test as hunitest
import helpers.lib_tasks.lib_tasks_open_md as hltltaomd

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_build_open_md_cmd1
# #############################################################################


class Test_build_open_md_cmd1(hunitest.TestCase):
    """
    Test `_build_open_md_cmd()`.
    """

    def test_default1(self) -> None:
        """
        Default mode (pandoc) and backend (global).
        """
        script_path = hltltaomd._get_open_md_script_path()
        actual = hltltaomd._build_open_md_cmd("xyz.md")
        expected = f"{script_path} --input xyz.md --mode pandoc --backend global"
        self.assert_equal(str(actual), str(expected))

    def test_mode1(self) -> None:
        """
        Open the file on GitHub.
        """
        script_path = hltltaomd._get_open_md_script_path()
        actual = hltltaomd._build_open_md_cmd("xyz.md", mode="github")
        expected = f"{script_path} --input xyz.md --mode github --backend global"
        self.assert_equal(str(actual), str(expected))

    def test_dockerized1(self) -> None:
        """
        Dockerized backend with force rebuild and sudo.
        """
        script_path = hltltaomd._get_open_md_script_path()
        actual = hltltaomd._build_open_md_cmd(
            "xyz.md",
            mode="grip",
            backend="dockerized",
            dockerized_force_rebuild=True,
            dockerized_use_sudo=True,
        )
        expected = (
            f"{script_path} --input xyz.md --mode grip --backend dockerized "
            "--dockerized_force_rebuild --dockerized_use_sudo"
        )
        self.assert_equal(str(actual), str(expected))

    def test_css1(self) -> None:
        """
        Custom HTML snippet for pandoc mode.
        """
        script_path = hltltaomd._get_open_md_script_path()
        actual = hltltaomd._build_open_md_cmd("xyz.md", css="my_style.html")
        expected = (
            f"{script_path} --input xyz.md --mode pandoc --backend global "
            "--css my_style.html"
        )
        self.assert_equal(str(actual), str(expected))

    def test_flags1(self) -> None:
        """
        Daemon and skip_open flags.
        """
        script_path = hltltaomd._get_open_md_script_path()
        actual = hltltaomd._build_open_md_cmd(
            "xyz.md", mode="pdf", daemon=True, skip_open=True
        )
        expected = (
            f"{script_path} --input xyz.md --mode pdf --backend global "
            "--daemon --skip_open"
        )
        self.assert_equal(str(actual), str(expected))

    def test_invalid_mode1(self) -> None:
        """
        An invalid mode is rejected.
        """
        with self.assertRaises(AssertionError):
            hltltaomd._build_open_md_cmd("xyz.md", mode="invalid_mode")

    def test_invalid_backend1(self) -> None:
        """
        An invalid backend is rejected.
        """
        with self.assertRaises(AssertionError):
            hltltaomd._build_open_md_cmd("xyz.md", backend="invalid_backend")

    def test_invalid_input1(self) -> None:
        """
        An empty input file is rejected.
        """
        with self.assertRaises(AssertionError):
            hltltaomd._build_open_md_cmd("")
