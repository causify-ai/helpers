import os
import tempfile
from unittest import mock

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.documentation.open_md as dshdopmd


# #############################################################################
# Test_convert_ssh_to_https
# #############################################################################


class Test_convert_ssh_to_https(hunitest.TestCase):
    """
    Test SSH to HTTPS URL conversion.
    """

    def test1(self) -> None:
        """
        Test converting SSH URL to HTTPS.
        """
        # Prepare inputs.
        ssh_url = "git@github.com:causify-ai/helpers.git"
        expected = "https://github.com/causify-ai/helpers"
        # Run test.
        actual = dshdopmd._convert_ssh_to_https(ssh_url)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test converting SSH URL without .git suffix.
        """
        # Prepare inputs.
        ssh_url = "git@github.com:causify-ai/helpers"
        expected = "https://github.com/causify-ai/helpers"
        # Run test.
        actual = dshdopmd._convert_ssh_to_https(ssh_url)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that HTTPS URLs are passed through.
        """
        # Prepare inputs.
        https_url = "https://github.com/causify-ai/helpers.git"
        expected = "https://github.com/causify-ai/helpers"
        # Run test.
        actual = dshdopmd._convert_ssh_to_https(https_url)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test HTTPS URL without .git suffix.
        """
        # Prepare inputs.
        https_url = "https://github.com/causify-ai/helpers"
        expected = "https://github.com/causify-ai/helpers"
        # Run test.
        actual = dshdopmd._convert_ssh_to_https(https_url)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test unknown URL format is returned as-is.
        """
        # Prepare inputs.
        unknown_url = "file:///home/user/repo"
        expected = unknown_url
        # Run test.
        actual = dshdopmd._convert_ssh_to_https(unknown_url)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_find_git_root_for_file
# #############################################################################


class Test_find_git_root_for_file(hunitest.TestCase):
    """
    Test finding git root for a file, handling subrepos.
    """

    def _make_git_repo(self, repo_path: str) -> None:
        """
        Create a git repository at the given path.

        :param repo_path: Path where git repository will be created
        """
        git_dir = os.path.join(repo_path, ".git")
        os.makedirs(git_dir)

    def test1(self) -> None:
        """
        Test finding git root for file in main repo.
        """
        # Prepare inputs.
        git_root = self.get_scratch_space()
        self._make_git_repo(git_root)
        file_path = os.path.join(git_root, "test.md")
        hio.to_file(file_path, "test")
        # Run test.
        result = dshdopmd._find_git_root_for_file(file_path)
        # Check outputs.
        self.assert_equal(result, git_root)

    def test2(self) -> None:
        """
        Test finding git root for file in subdirectory of repo.
        """
        # Prepare inputs.
        git_root = self.get_scratch_space()
        self._make_git_repo(git_root)
        subdir = os.path.join(git_root, "docs", "guides")
        os.makedirs(subdir)
        file_path = os.path.join(subdir, "test.md")
        hio.to_file(file_path, "test")
        # Run test.
        result = dshdopmd._find_git_root_for_file(file_path)
        # Check outputs.
        self.assert_equal(result, git_root)

    def test3(self) -> None:
        """
        Test finding git root for file in subrepo.
        """
        # Prepare inputs.
        main_root = self.get_scratch_space()
        self._make_git_repo(main_root)
        subrepo_dir = os.path.join(main_root, "submodule")
        os.makedirs(subrepo_dir)
        self._make_git_repo(subrepo_dir)
        file_path = os.path.join(subrepo_dir, "test.md")
        hio.to_file(file_path, "test")
        # Run test.
        result = dshdopmd._find_git_root_for_file(file_path)
        # Check outputs: should find subrepo git root, not main repo.
        self.assert_equal(result, subrepo_dir)

    def test4(self) -> None:
        """
        Test falls back to the main repo root when no ancestor
        `.git` directory is found.
        """
        # Prepare inputs.
        file_path = "/some/path/without/git/test.md"
        expected_root = "/main/repo"
        # Run test.
        with mock.patch("os.path.exists", return_value=False):
            with mock.patch(
                "helpers.hgit.get_client_root", return_value=expected_root
            ):
                result = dshdopmd._find_git_root_for_file(file_path)
        # Check outputs.
        self.assert_equal(result, expected_root)


# #############################################################################
# Test_open_file
# #############################################################################


class Test_open_file(hunitest.TestCase):
    """
    Test the `_open_file()` function.
    """

    def test1(self) -> None:
        """
        Test on macOS the `open` command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with mock.patch("platform.system", return_value="Darwin"):
            with hunteuti.capture_sys_calls() as sys_calls:
                dshdopmd._open_file(file_path)
        # Check outputs.
        expected = f"""
        [{{'function': 'subprocess.run',
          'args': (['open', '{file_path}'],),
          'kwargs': {{'check': True}}}}]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected, dedent=True)

    def test2(self) -> None:
        """
        Test on Linux the `xdg-open` command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with mock.patch("platform.system", return_value="Linux"):
            with hunteuti.capture_sys_calls() as sys_calls:
                dshdopmd._open_file(file_path)
        # Check outputs.
        expected = f"""
        [{{'function': 'subprocess.run',
          'args': (['xdg-open', '{file_path}'],),
          'kwargs': {{'check': True}}}}]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected, dedent=True)

    def test3(self) -> None:
        """
        Test on an unsupported OS no command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with mock.patch("platform.system", return_value="Windows"):
            with hunteuti.capture_sys_calls() as sys_calls:
                dshdopmd._open_file(file_path)
        # Check outputs.
        self.assertEqual(sys_calls, [])


# #############################################################################
# Test_run_render_images
# #############################################################################


class Test_run_render_images(hunitest.TestCase):
    """
    Test the `_run_render_images()` function.
    """

    def test1(self) -> None:
        """
        Test builds and runs the `render_images.py` command.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.render_images.md")
        render_images_script = os.path.join(scratch_dir, "render_images.py")
        hio.to_file(render_images_script, "# fake script")
        expected_output = "tmp.open_md.render_images.md"
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
        self.assertEqual(actual, expected_output)
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
        Test builds the GitHub URL and opens it in the browser.
        """
        # Prepare inputs.
        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare repo structure.
            git_root = tmpdir
            os.makedirs(os.path.join(git_root, ".git"))
            file_path = os.path.join(git_root, "docs", "readme.md")
            os.makedirs(os.path.dirname(file_path))
            hio.to_file(file_path, "# Doc")
            # Prepare outputs.
            expected_url = (
                "https://github.com/causify-ai/helpers/blob/main/docs/readme.md"
            )
            # Run test.
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
                        dshdopmd._open_on_github(file_path)
            # Check outputs.
            mock_open_file.assert_called_once_with(expected_url)


# #############################################################################
# Test_render_with_pandoc
# #############################################################################


class Test_render_with_pandoc(hunitest.TestCase):
    """
    Test the `_render_with_pandoc()` function.
    """

    def _create_output_file(
        self, output_file: str, content: str = "<html></html>"
    ) -> object:
        """
        Create output file side effect for mocking.

        :param output_file: Path to output file to create
        :param content: Content to write to output file
        :return: Callable that creates output file and returns 0
        """

        def _side_effect(*_args: object, **_kwargs: object) -> int:
            hio.to_file(output_file, content)
            return 0

        return _side_effect

    def test1(self) -> None:
        """
        Test `global` backend runs `pandoc` directly.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.pandoc.html")
        backend = "global"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ) as mock_system:
                    with mock.patch.object(
                        dshdopmd, "_open_file"
                    ) as mock_open_file:
                        # Run test.
                        dshdopmd._render_with_pandoc(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        self.assertIn("pandoc", called_cmd)
        self.assertIn(input_file, called_cmd)
        mock_open_file.assert_called_once_with("tmp.open_md.pandoc.html")

    def test2(self) -> None:
        """
        Test an invalid backend raises a `ValueError`.
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
        Test `dockerized` backend runs pandoc via
        `run_dockerized_pandoc()`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.pandoc.html")
        backend = "dockerized"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch.object(
                    dshdopmd.dshdlipa,
                    "run_dockerized_pandoc",
                    side_effect=self._create_output_file(output_file),
                ) as mock_run_dockerized:
                    with mock.patch.object(dshdopmd, "_open_file"):
                        # Run test.
                        dshdopmd._render_with_pandoc(input_file, backend=backend)
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

    def _create_output_file(
        self, output_file: str, content: str = "<html></html>"
    ) -> object:
        """
        Create output file side effect for mocking.

        :param output_file: Path to output file to create
        :param content: Content to write to output file
        :return: Callable that creates output file and returns 0
        """

        def _side_effect(*_args: object, **_kwargs: object) -> int:
            hio.to_file(output_file, content)
            return 0

        return _side_effect

    def test1(self) -> None:
        """
        Test `global` backend runs `grip --export`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.grip.html")
        backend = "global"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ) as mock_system:
                    with mock.patch.object(
                        dshdopmd, "_open_file"
                    ) as mock_open_file:
                        # Run test.
                        dshdopmd._render_with_grip(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        expected_cmd = f"grip --export {input_file} tmp.open_md.grip.html"
        self.assertEqual(called_cmd, expected_cmd)
        mock_open_file.assert_called_once_with("tmp.open_md.grip.html")

    def test2(self) -> None:
        """
        Test an invalid backend raises a `ValueError`.
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
        Test `dockerized` backend runs `uvx grip --export`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.open_md.grip.html")
        backend = "dockerized"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ):
                with mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ) as mock_system:
                    with mock.patch.object(dshdopmd, "_open_file"):
                        # Run test.
                        dshdopmd._render_with_grip(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        expected_cmd = f"uvx grip --export {input_file} tmp.open_md.grip.html"
        self.assertEqual(called_cmd, expected_cmd)


# #############################################################################
# Test_render_with_grip_daemon
# #############################################################################


class Test_render_with_grip_daemon(hunitest.TestCase):
    """
    Test the `_render_with_grip_daemon()` function.
    """

    def test1(self) -> None:
        """
        Test `dockerized` backend runs `uvx grip` in daemon mode.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test.
        with mock.patch.object(
            dshdopmd, "_run_render_images", return_value=input_file
        ):
            with hunteuti.capture_sys_calls() as sys_calls:
                dshdopmd._render_with_grip_daemon(
                    input_file, backend="dockerized"
                )
        # Check outputs.
        expected = f"""
        [{{'function': 'hsystem.system',
          'args': ('uvx grip -b --quiet {input_file}',),
          'kwargs': {{}}}}]
        """
        expected = hprint.dedent(expected)
        hunteuti.assert_sys_calls(self, sys_calls, expected, dedent=True)

    def test2(self) -> None:
        """
        Test an invalid backend raises a `ValueError`.
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
                dshdopmd._render_with_grip_daemon(input_file, backend="invalid")


# #############################################################################
# Test_open_md_py_main
# #############################################################################


class Test_open_md_py_main(hunitest.TestCase):
    """
    Test `_main()` called directly (in-process) with mocked `sys.argv`.
    """

    def test1(self) -> None:
        """
        Test `--mode github` dispatches to `_open_on_github()`.
        """
        # Prepare inputs.
        input_file = "readme.md"
        mode = "github"
        argv = ["open_md.py", "--input", input_file, "--mode", mode]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(dshdopmd, "_open_on_github") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(input_file)

    def test2(self) -> None:
        """
        Test `--mode grip_daemon` dispatches to
        `_render_with_grip_daemon()`.
        """
        # Prepare inputs.
        input_file = "readme.md"
        mode = "grip_daemon"
        backend = "dockerized"
        argv = [
            "open_md.py",
            "--input",
            input_file,
            "--mode",
            mode,
            "--backend",
            backend,
        ]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(dshdopmd, "_render_with_grip_daemon") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(input_file, backend=backend)

    def test3(self) -> None:
        """
        Test `--mode pandoc` dispatches to `_render_with_pandoc()`
        with the dockerized-force-rebuild arguments.
        """
        # Prepare inputs.
        input_file = "readme.md"
        mode = "pandoc"
        argv = ["open_md.py", "--input", input_file, "--mode", mode]
        parser = dshdopmd._parse()
        # Prepare outputs.
        expected_backend = "global"
        expected_force_rebuild = False
        expected_use_sudo = False
        # Run test.
        with mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(
            input_file,
            backend=expected_backend,
            force_rebuild=expected_force_rebuild,
            use_sudo=expected_use_sudo,
        )

    def test4(self) -> None:
        """
        Test `--mode grip` dispatches to `_render_with_grip()`.
        """
        # Prepare inputs.
        input_file = "readme.md"
        mode = "grip"
        backend = "global"
        argv = ["open_md.py", "--input", input_file, "--mode", mode]
        parser = dshdopmd._parse()
        # Run test.
        with mock.patch.object(dshdopmd, "_render_with_grip") as mock_fn:
            with mock.patch("sys.argv", argv):
                dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(input_file, backend=backend)
