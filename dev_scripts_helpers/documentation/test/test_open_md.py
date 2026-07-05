import os
import tempfile
from unittest import mock

import helpers.hio as hio
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.open_md as dshdopmd


# #############################################################################
# Test_convert_ssh_to_https
# #############################################################################


# TODO(ai_gp): Rename the tests.
# TODO(ai_gp): Factor out common code.
class Test_convert_ssh_to_https(hunitest.TestCase):
    """
    Test SSH to HTTPS URL conversion.
    """

    def test_ssh_to_https(self) -> None:
        """
        Test converting SSH URL to HTTPS.
        """
        # Prepare inputs.
        ssh_url = "git@github.com:causify-ai/helpers.git"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(ssh_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_ssh_to_https_without_git_suffix(self) -> None:
        """
        Test converting SSH URL without .git suffix.
        """
        # Prepare inputs.
        ssh_url = "git@github.com:causify-ai/helpers"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(ssh_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_https_passthrough(self) -> None:
        """
        Test that HTTPS URLs are passed through.
        """
        # Prepare inputs.
        https_url = "https://github.com/causify-ai/helpers.git"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(https_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_https_without_git_suffix(self) -> None:
        """
        Test HTTPS URL without .git suffix.
        """
        # Prepare inputs.
        https_url = "https://github.com/causify-ai/helpers"
        expected = "https://github.com/causify-ai/helpers"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(https_url)
        # Check output.
        self.assertEqual(actual, expected)

    def test_unknown_format_passthrough(self) -> None:
        """
        Test unknown URL format is returned as-is.
        """
        # Prepare inputs.
        unknown_url = "file:///home/user/repo"
        expected = "file:///home/user/repo"
        # Call function to test.
        actual = dshdopmd._convert_ssh_to_https(unknown_url)
        # Check output.
        self.assertEqual(actual, expected)


# #############################################################################
# Test_find_git_root_for_file
# #############################################################################


# TODO(ai_gp): Rename the tests.
# TODO(ai_gp): Factor out common code.
# TODO(ai_gp): Is _find_git_root_for_file general?
class Test_find_git_root_for_file(hunitest.TestCase):
    """
    Test finding git root for a file, handling subrepos.
    """

    def test_find_git_root_in_main_repo(self) -> None:
        """
        Test finding git root for file in main repo.
        """
        # TODO(ai_gp): Use self.get_scratch_space()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a git repo.
            git_root = tmpdir
            git_dir = os.path.join(git_root, ".git")
            os.makedirs(git_dir)
            # Create a file in the repo.
            file_path = os.path.join(git_root, "test.md")
            with open(file_path, "w") as f:
                f.write("test")
            # Call function.
            result = dshdopmd._find_git_root_for_file(file_path)
            # Check result.
            self.assertEqual(result, git_root)

    def test_find_git_root_in_subdirectory(self) -> None:
        """
        Test finding git root for file in subdirectory of repo.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a git repo.
            git_root = tmpdir
            git_dir = os.path.join(git_root, ".git")
            os.makedirs(git_dir)
            # Create a subdirectory with a file.
            subdir = os.path.join(git_root, "docs", "guides")
            os.makedirs(subdir)
            file_path = os.path.join(subdir, "test.md")
            with open(file_path, "w") as f:
                f.write("test")
            # Call function.
            result = dshdopmd._find_git_root_for_file(file_path)
            # Check result.
            self.assertEqual(result, git_root)

    def test_find_git_root_in_subrepo(self) -> None:
        """
        Test finding git root for file in subrepo.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create main repo.
            main_root = tmpdir
            main_git_dir = os.path.join(main_root, ".git")
            os.makedirs(main_git_dir)
            # Create subrepo inside main repo.
            subrepo_dir = os.path.join(main_root, "submodule")
            os.makedirs(subrepo_dir)
            subrepo_git_dir = os.path.join(subrepo_dir, ".git")
            os.makedirs(subrepo_git_dir)
            # Create a file in subrepo.
            file_path = os.path.join(subrepo_dir, "test.md")
            with open(file_path, "w") as f:
                f.write("test")
            # Call function.
            result = dshdopmd._find_git_root_for_file(file_path)
            # Should find subrepo git root, not main repo.
            self.assertEqual(result, subrepo_dir)

    def test_find_git_root_fallback(self) -> None:
        """
        Test edge case: falls back to the main repo root when no ancestor
        `.git` directory is found.
        """
        # Prepare inputs.
        file_path = "/some/path/without/git/test.md"
        # Run test.
        with mock.patch("os.path.exists", return_value=False):
            with mock.patch(
                "helpers.hgit.get_client_root", return_value="/main/repo"
            ):
                result = dshdopmd._find_git_root_for_file(file_path)
        # Check outputs.
        self.assertEqual(result, "/main/repo")


# #############################################################################
# Test_open_file
# #############################################################################


class Test_open_file(hunitest.TestCase):
    """
    Test the `_open_file()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: on macOS the `open` command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with mock.patch("platform.system", return_value="Darwin"):
            with hunteuti.capture_system_calls() as invocations:
                dshdopmd._open_file(file_path)
        # Check outputs.
        expected_invocations = [
            {
                "function": "subprocess.run",
                "args": (["open", file_path],),
                "kwargs": {"check": True},
            }
        ]
        expected = hunteuti.invocations_to_str(expected_invocations)
        hunteuti.assert_invocations(self, invocations, expected)

    def test2(self) -> None:
        """
        Test edge case: on Linux the `xdg-open` command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with mock.patch("platform.system", return_value="Linux"):
            with hunteuti.capture_system_calls() as invocations:
                dshdopmd._open_file(file_path)
        # Check outputs.
        expected_invocations = [
            {
                "function": "subprocess.run",
                "args": (["xdg-open", file_path],),
                "kwargs": {"check": True},
            }
        ]
        expected = hunteuti.invocations_to_str(expected_invocations)
        hunteuti.assert_invocations(self, invocations, expected)

    def test3(self) -> None:
        """
        Test edge case: on an unsupported OS no command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with mock.patch("platform.system", return_value="Windows"):
            with hunteuti.capture_system_calls() as invocations:
                dshdopmd._open_file(file_path)
        # Check outputs.
        self.assertEqual(invocations, [])


# #############################################################################
# Test_run_render_images
# #############################################################################


class Test_run_render_images(hunitest.TestCase):
    """
    Test the `_run_render_images()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: builds and runs the `render_images.py` command.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.render_images.md")
        render_images_script = os.path.join(scratch_dir, "render_images.py")
        hio.to_file(render_images_script, "# fake script")
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:

            def _create_output(*_args: object, **_kwargs: object) -> int:
                hio.to_file(output_file, "rendered")
                return 0

            with mock.patch(
                "helpers.hgit.find_file", return_value=render_images_script
            ):
                with mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system:
                    # Run test.
                    actual = dshdopmd._run_render_images(input_file)
        finally:
            os.chdir(cwd)
        # Check outputs.
        self.assertEqual(actual, "tmp.open_md.render_images.md")
        called_cmd = mock_system.call_args[0][0]
        self.assertIn("render_images.py", called_cmd)
        self.assertIn(input_file, called_cmd)
        self.assertIn("--action render", called_cmd)


# #############################################################################
# Test_open_on_github
# #############################################################################


class Test_open_on_github(hunitest.TestCase):
    """
    Test the `_open_on_github()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: builds the GitHub URL and opens it in the browser.
        """
        # Prepare inputs.
        with tempfile.TemporaryDirectory() as tmpdir:
            git_root = tmpdir
            os.makedirs(os.path.join(git_root, ".git"))
            file_path = os.path.join(git_root, "docs", "readme.md")
            os.makedirs(os.path.dirname(file_path))
            hio.to_file(file_path, "# Doc")
            with mock.patch(
                "helpers.hsystem.system_to_one_line",
                return_value=(0, "git@github.com:causify-ai/helpers.git"),
            ):
                with mock.patch(
                    "helpers.hgit.get_branch_name", return_value="main"
                ):
                    with mock.patch.object(
                        dshdopmd, "_open_file"
                    ) as mock_open_file:
                        # Run test.
                        dshdopmd._open_on_github(file_path)
        # Check outputs.
        expected_url = (
            "https://github.com/causify-ai/helpers/blob/main/docs/readme.md"
        )
        mock_open_file.assert_called_once_with(expected_url)


# #############################################################################
# Test_render_with_pandoc
# #############################################################################


class Test_render_with_pandoc(hunitest.TestCase):
    """
    Test the `_render_with_pandoc()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: `global` backend runs `pandoc` directly.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.pandoc.html")
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:

            def _create_output(*_args: object, **_kwargs: object) -> int:
                hio.to_file(output_file, "<html></html>")
                return 0

            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system:
                    with mock.patch.object(
                        dshdopmd, "_open_file"
                    ) as mock_open_file:
                        # Run test.
                        dshdopmd._render_with_pandoc(
                            input_file, backend="global"
                        )
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        self.assertIn("pandoc", called_cmd)
        self.assertIn(input_file, called_cmd)
        mock_open_file.assert_called_once_with("tmp.open_md.pandoc.html")

    def test2(self) -> None:
        """
        Test edge case: an invalid backend raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test and check output.
        with mock.patch.object(
            dshdopmd, "_run_render_images", return_value=input_file
        ):
            with self.assertRaises(ValueError):
                dshdopmd._render_with_pandoc(input_file, backend="invalid")

    def test3(self) -> None:
        """
        Test edge case: `dockerized` backend runs pandoc via
        `run_dockerized_pandoc()`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.pandoc.html")
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:

            def _create_output(*_args: object, **_kwargs: object) -> None:
                hio.to_file(output_file, "<html></html>")

            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch.object(
                    dshdopmd.dshdlipa,
                    "run_dockerized_pandoc",
                    side_effect=_create_output,
                ) as mock_run_dockerized:
                    with mock.patch.object(dshdopmd, "_open_file"):
                        # Run test.
                        dshdopmd._render_with_pandoc(
                            input_file, backend="dockerized"
                        )
        finally:
            os.chdir(cwd)
        # Check outputs.
        mock_run_dockerized.assert_called_once()
        called_cmd = mock_run_dockerized.call_args[0][0]
        self.assertIn("pandoc", called_cmd)


# #############################################################################
# Test_render_with_grip
# #############################################################################


class Test_render_with_grip(hunitest.TestCase):
    """
    Test the `_render_with_grip()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: `global` backend runs `grip --export`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.grip.html")
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:

            def _create_output(*_args: object, **_kwargs: object) -> int:
                hio.to_file(output_file, "<html></html>")
                return 0

            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system:
                    with mock.patch.object(
                        dshdopmd, "_open_file"
                    ) as mock_open_file:
                        # Run test.
                        dshdopmd._render_with_grip(
                            input_file, backend="global"
                        )
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        self.assertEqual(
            called_cmd, f"grip --export {input_file} tmp.open_md.grip.html"
        )
        mock_open_file.assert_called_once_with("tmp.open_md.grip.html")

    def test2(self) -> None:
        """
        Test edge case: an invalid backend raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test and check output.
        with mock.patch.object(
            dshdopmd, "_run_render_images", return_value=input_file
        ):
            with self.assertRaises(ValueError):
                dshdopmd._render_with_grip(input_file, backend="invalid")

    def test3(self) -> None:
        """
        Test edge case: `dockerized` backend runs `uvx grip --export`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.grip.html")
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:

            def _create_output(*_args: object, **_kwargs: object) -> int:
                hio.to_file(output_file, "<html></html>")
                return 0

            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system:
                    with mock.patch.object(dshdopmd, "_open_file"):
                        # Run test.
                        dshdopmd._render_with_grip(
                            input_file, backend="dockerized"
                        )
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        self.assertEqual(
            called_cmd,
            f"uvx grip --export {input_file} tmp.open_md.grip.html",
        )


# #############################################################################
# Test_render_with_grip_daemon
# #############################################################################


class Test_render_with_grip_daemon(hunitest.TestCase):
    """
    Test the `_render_with_grip_daemon()` function.
    """

    def test1(self) -> None:
        """
        Test happy path: `dockerized` backend runs `uvx grip` in daemon mode.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test.
        with mock.patch.object(
            dshdopmd, "_run_render_images", return_value=input_file
        ):
            with hunteuti.capture_system_calls() as invocations:
                dshdopmd._render_with_grip_daemon(
                    input_file, backend="dockerized"
                )
        # Check outputs.
        expected_invocations = [
            {
                "function": "hsystem.system",
                "args": (f"uvx grip -b --quiet {input_file}",),
                "kwargs": {},
            }
        ]
        expected = hunteuti.invocations_to_str(expected_invocations)
        actual = hunteuti.invocations_to_str(invocations)
        self.assert_equal(
            actual, expected, purify_text=True, purify_expected_text=True
        )

    def test2(self) -> None:
        """
        Test edge case: an invalid backend raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test and check output.
        with mock.patch.object(
            dshdopmd, "_run_render_images", return_value=input_file
        ):
            with self.assertRaises(ValueError):
                dshdopmd._render_with_grip_daemon(
                    input_file, backend="invalid"
                )


# #############################################################################
# Test_open_md_py_main
# #############################################################################


class Test_open_md_py_main(hunitest.TestCase):
    """
    Test `_main()` called directly (in-process) with mocked `sys.argv`.
    """

    def test1(self) -> None:
        """
        Test happy path: `--mode github` dispatches to `_open_on_github()`.
        """
        # Prepare inputs.
        argv = ["open_md.py", "--input", "readme.md", "--mode", "github"]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(dshdopmd, "_open_on_github") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with("readme.md")

    def test2(self) -> None:
        """
        Test edge case: `--mode grip_daemon` dispatches to
        `_render_with_grip_daemon()`.
        """
        # Prepare inputs.
        argv = [
            "open_md.py",
            "--input",
            "readme.md",
            "--mode",
            "grip_daemon",
            "--backend",
            "dockerized",
        ]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(
            dshdopmd, "_render_with_grip_daemon"
        ) as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with("readme.md", backend="dockerized")

    def test3(self) -> None:
        """
        Test edge case: `--mode pandoc` dispatches to `_render_with_pandoc()`
        with the dockerized-force-rebuild arguments.
        """
        # Prepare inputs.
        argv = ["open_md.py", "--input", "readme.md", "--mode", "pandoc"]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(
            "readme.md",
            backend="global",
            force_rebuild=False,
            use_sudo=False,
        )

    def test4(self) -> None:
        """
        Test edge case: `--mode grip` dispatches to `_render_with_grip()`.
        """
        # Prepare inputs.
        argv = ["open_md.py", "--input", "readme.md", "--mode", "grip"]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(dshdopmd, "_render_with_grip") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with("readme.md", backend="global")
