import hashlib
import os
import tempfile
from typing import List, Tuple
from unittest import mock

import dev_scripts_helpers.documentation.open_md as dshdopmd
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

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
        with (
            mock.patch("os.path.exists", return_value=False),
            mock.patch(
                "helpers.hgit.get_client_root", return_value=expected_root
            ),
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
        with (
            mock.patch("platform.system", return_value="Darwin"),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            dshdopmd._open_file(file_path)
        # Check outputs.
        expected_str = r"""[
        {
        'function': subprocess.run,
        'args': (['open', '/tmp/test.html'],),
        'kwargs': {'check': True},
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str, dedent=True)

    def test2(self) -> None:
        """
        Test on Linux the `xdg-open` command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with (
            mock.patch("platform.system", return_value="Linux"),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            dshdopmd._open_file(file_path)
        # Check outputs.
        expected_str = r"""[
        {
        'function': subprocess.run,
        'args': (['xdg-open', '/tmp/test.html'],),
        'kwargs': {'check': True},
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(self, sys_calls, expected_str, dedent=True)

    def test3(self) -> None:
        """
        Test on an unsupported OS no command is invoked.
        """
        # Prepare inputs.
        file_path = "/tmp/test.html"
        # Run test.
        with (
            mock.patch("platform.system", return_value="Windows"),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            dshdopmd._open_file(file_path)
        # Check outputs.
        self.assertEqual(sys_calls, [])


# #############################################################################
# Test_get_stem
# #############################################################################


class Test_get_stem(hunitest.TestCase):
    """
    Test the `_get_stem()` function.
    """

    def test1(self) -> None:
        """
        Test only the last extension is dropped from the basename.
        """
        # Prepare inputs.
        input_file = "docs/design.architecture.md"
        # Prepare outputs.
        expected = "design.architecture"
        # Run test.
        actual = dshdopmd._get_stem(input_file)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test2(self) -> None:
        """
        Test a file in the current dir.
        """
        # Prepare inputs.
        input_file = "readme.md"
        # Prepare outputs.
        expected = "readme"
        # Run test.
        actual = dshdopmd._get_stem(input_file)
        # Check outputs.
        self.assertEqual(actual, expected)


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
        output_file = os.path.join(
            scratch_dir, "tmp.open_md.input.render_images.md"
        )
        render_images_script = os.path.join(scratch_dir, "render_images.py")
        hio.to_file(render_images_script, "# fake script")
        expected_output = "tmp.open_md.input.render_images.md"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:

            def _create_output(*_args: object, **_kwargs: object) -> int:
                hio.to_file(output_file, "rendered")
                return 0

            with (
                mock.patch(
                    "helpers.hgit.find_file", return_value=render_images_script
                ),
                mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system,
            ):
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
            with (
                mock.patch(
                    "helpers.hsystem.system_to_one_line",
                    return_value=(0, "git@github.com:causify-ai/helpers.git"),
                ),
                mock.patch("helpers.hgit.get_branch_name", return_value="main"),
                mock.patch.object(dshdopmd, "_open_file") as mock_open_file,
            ):
                dshdopmd._open_on_github(file_path)
            # Check outputs.
            mock_open_file.assert_called_once_with(expected_url)


# #############################################################################
# Test_inject_live_reload
# #############################################################################


class Test_inject_live_reload(hunitest.TestCase):
    """
    Test the `_inject_live_reload()` function.
    """

    def test1(self) -> None:
        """
        Test the polling script is inserted before `</head>` and the build file
        stores the hash of the original page.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        html_file = os.path.join(scratch_dir, "tmp.page.html")
        html = "<html><head><title>t</title></head><body>x</body></html>"
        hio.to_file(html_file, html)
        # Prepare outputs.
        build_id = hashlib.md5(html.encode()).hexdigest()
        expected_build = f'window.__open_md_build = "{build_id}";\n'
        # Run test.
        dshdopmd._inject_live_reload(html_file)
        # Check outputs.
        actual_html = hio.from_file(html_file)
        self.assertLess(
            actual_html.index("<script>"), actual_html.index("</head>")
        )
        self.assertIn(f'var build = "{build_id}";', actual_html)
        self.assertIn('script.src = "tmp.page.build.js"', actual_html)
        self.assertIn("<body>x</body>", actual_html)
        build_file = os.path.join(scratch_dir, "tmp.page.build.js")
        self.assertEqual(hio.from_file(build_file), expected_build)

    def test2(self) -> None:
        """
        Test the build id changes only when the rendered content changes.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        html_file = os.path.join(scratch_dir, "tmp.page.html")
        build_file = os.path.join(scratch_dir, "tmp.page.build.js")
        html1 = "<html><head></head><body>one</body></html>"
        html2 = "<html><head></head><body>two</body></html>"
        # Run test.
        hio.to_file(html_file, html1)
        dshdopmd._inject_live_reload(html_file)
        build1 = hio.from_file(build_file)
        hio.to_file(html_file, html1)
        dshdopmd._inject_live_reload(html_file)
        build1_again = hio.from_file(build_file)
        hio.to_file(html_file, html2)
        dshdopmd._inject_live_reload(html_file)
        build2 = hio.from_file(build_file)
        # Check outputs.
        self.assertEqual(build1, build1_again)
        self.assertNotEqual(build1, build2)


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
        output_file = os.path.join(scratch_dir, "tmp.input.html")
        backend = "global"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ) as mock_system,
                mock.patch.object(dshdopmd, "_open_file") as mock_open_file,
            ):
                # Run test.
                dshdopmd._render_with_pandoc(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        self.assertIn("pandoc", called_cmd)
        self.assertIn(input_file, called_cmd)
        mock_open_file.assert_called_once_with("tmp.input.html")

    def test2(self) -> None:
        """
        Test an invalid backend raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test and check output.
        with (
            mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ),
            self.assertRaises(ValueError),
        ):
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
        output_file = os.path.join(scratch_dir, "tmp.input.html")
        backend = "dockerized"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch.object(
                    dshdopmd.dshdlipa,
                    "run_dockerized_pandoc",
                    side_effect=self._create_output_file(output_file),
                ) as mock_run_dockerized,
                mock.patch.object(dshdopmd, "_open_file"),
            ):
                # Run test.
                dshdopmd._render_with_pandoc(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        mock_run_dockerized.assert_called_once()
        called_cmd = mock_run_dockerized.call_args[0][0]
        self.assertIn("pandoc", called_cmd)

    def test4(self) -> None:
        """
        Test the output file is named after the input basename, dropping only
        the last extension.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_dir = os.path.join(scratch_dir, "docs")
        input_file = os.path.join(input_dir, "design.architecture.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.design.architecture.html")
        backend = "global"
        expected = "tmp.design.architecture.html"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ),
                mock.patch.object(dshdopmd, "_open_file") as mock_open_file,
            ):
                # Run test.
                dshdopmd._render_with_pandoc(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        mock_open_file.assert_called_once_with(expected)

    def test5(self) -> None:
        """
        Test `live_reload=True` injects the reload script in the output.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.input.html")
        backend = "global"
        live_reload = True
        skip_open = True
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ),
                mock.patch.object(dshdopmd, "_open_file") as mock_open_file,
                mock.patch.object(
                    dshdopmd, "_inject_live_reload"
                ) as mock_inject,
            ):
                # Run test.
                dshdopmd._render_with_pandoc(
                    input_file,
                    backend=backend,
                    skip_open=skip_open,
                    live_reload=live_reload,
                )
        finally:
            os.chdir(cwd)
        # Check outputs.
        mock_inject.assert_called_once_with("tmp.input.html")
        mock_open_file.assert_not_called()


# #############################################################################
# Test_render_with_pdf
# #############################################################################


class Test_render_with_pdf(hunitest.TestCase):
    """
    Test the `_render_with_pdf()` function.
    """

    def test1(self) -> None:
        """
        Test the output file is named after the input basename.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.input.pdf")
        backend = "global"

        def _create_output(*_args: object, **_kwargs: object) -> int:
            hio.to_file(output_file, "pdf")
            return 0

        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system,
                mock.patch.object(dshdopmd, "_open_file") as mock_open_file,
            ):
                # Run test.
                dshdopmd._render_with_pdf(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        self.assertIn("-o tmp.input.pdf", called_cmd)
        mock_open_file.assert_called_once_with("tmp.input.pdf")


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
        output_file = os.path.join(scratch_dir, "tmp.input.grip.html")
        backend = "global"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ) as mock_system,
                mock.patch.object(dshdopmd, "_open_file") as mock_open_file,
            ):
                # Run test.
                dshdopmd._render_with_grip(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        expected_cmd = f"grip --export {input_file} tmp.input.grip.html"
        self.assertEqual(called_cmd, expected_cmd)
        mock_open_file.assert_called_once_with("tmp.input.grip.html")

    def test2(self) -> None:
        """
        Test an invalid backend raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test and check output.
        with (
            mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ),
            self.assertRaises(ValueError),
        ):
            dshdopmd._render_with_grip(input_file, backend="invalid")

    def test3(self) -> None:
        """
        Test `dockerized` backend runs `uvx grip --export`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        output_file = os.path.join(scratch_dir, "tmp.input.grip.html")
        backend = "dockerized"
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system",
                    side_effect=self._create_output_file(output_file),
                ) as mock_system,
                mock.patch.object(dshdopmd, "_open_file"),
            ):
                # Run test.
                dshdopmd._render_with_grip(input_file, backend=backend)
        finally:
            os.chdir(cwd)
        # Check outputs.
        called_cmd = mock_system.call_args[0][0]
        expected_cmd = f"uvx grip --export {input_file} tmp.input.grip.html"
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
        with (
            mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ),
            hunteuti.capture_sys_calls() as sys_calls,
        ):
            dshdopmd._render_with_grip_daemon(input_file, backend="dockerized")
        # Check outputs.
        expected_str = r"""[
        {
        'function': hsystem.system,
        'args': ('uvx grip -b --quiet $GIT_ROOT/dev_scripts_helpers/documentation/test/outcomes/Test_render_with_grip_daemon.test1/tmp.scratch/input.md',),
        'kwargs': {},
        },
        ]"""
        expected_str = hprint.dedent(expected_str)
        hunteuti.assert_sys_calls(
            self,
            sys_calls,
            expected_str,
            dedent=True,
            purify_text=True,
            purify_expected_text=True,
        )

    def test2(self) -> None:
        """
        Test an invalid backend raises a `ValueError`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        # Run test and check output.
        with (
            mock.patch.object(
                dshdopmd, "_run_render_images", return_value=input_file
            ),
            self.assertRaises(ValueError),
        ):
            dshdopmd._render_with_grip_daemon(input_file, backend="invalid")


# #############################################################################
# Test_get_files_to_render
# #############################################################################


class Test_get_files_to_render(hunitest.TestCase):
    """
    Test the `_get_files_to_render()` function.
    """

    def _create_files(self, rel_paths: List[str]) -> List[str]:
        """
        Create markdown files in the scratch dir.

        :param rel_paths: paths relative to the scratch dir
        :return: absolute paths of the created files
        """
        scratch_dir = self.get_scratch_space()
        paths = []
        for rel_path in rel_paths:
            path = os.path.join(scratch_dir, rel_path)
            hio.to_file(path, "# Title")
            paths.append(path)
        return paths

    def test1(self) -> None:
        """
        Test `--input` selects a single file.
        """
        # Prepare inputs.
        files = self._create_files(["a.md"])
        args = dshdopmd._parse().parse_args(["--input", files[0]])
        # Run test.
        actual = dshdopmd._get_files_to_render(args)
        # Check outputs.
        self.assertEqual(actual, files)

    def test2(self) -> None:
        """
        Test `--files` selects a space-separated list of files.
        """
        # Prepare inputs.
        files = self._create_files(["a.md", "b.md"])
        files_str = " ".join(files)
        args = dshdopmd._parse().parse_args(["--files", files_str])
        # Run test.
        actual = dshdopmd._get_files_to_render(args)
        # Check outputs.
        self.assertEqual(actual, files)

    def test3(self) -> None:
        """
        Test `--from_file` selects the files listed in a file, one per line.
        """
        # Prepare inputs.
        files = self._create_files(["a.md", "b.md"])
        list_file = os.path.join(self.get_scratch_space(), "files.txt")
        hio.to_file(list_file, "\n".join(files))
        args = dshdopmd._parse().parse_args(["--from_file", list_file])
        # Run test.
        actual = dshdopmd._get_files_to_render(args)
        # Check outputs.
        self.assertEqual(actual, files)

    def test4(self) -> None:
        """
        Test files with the same basename are rejected, since their outputs
        would overwrite each other.
        """
        # Prepare inputs.
        files = self._create_files(["dir1/a.md", "dir2/a.md"])
        files_str = " ".join(files)
        args = dshdopmd._parse().parse_args(["--files", files_str])
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshdopmd._get_files_to_render(args)
        self.assertIn("distinct basenames", str(cm.exception))

    def test5(self) -> None:
        """
        Test files with the same basename are accepted in `github` mode, since
        no output file is written.
        """
        # Prepare inputs.
        files = self._create_files(["dir1/a.md", "dir2/a.md"])
        files_str = " ".join(files)
        args = dshdopmd._parse().parse_args(
            ["--files", files_str, "--mode", "github"]
        )
        # Run test.
        actual = dshdopmd._get_files_to_render(args)
        # Check outputs.
        self.assertEqual(actual, files)

    def test6(self) -> None:
        """
        Test that nothing selected is rejected instead of defaulting to the
        files modified in the branch.
        """
        # Prepare inputs.
        args = dshdopmd._parse().parse_args([])
        # Run test and check output.
        with self.assertRaises(AssertionError) as cm:
            dshdopmd._get_files_to_render(args)
        self.assertIn("No files selected", str(cm.exception))


# #############################################################################
# Test_build_render_cmd
# #############################################################################


class Test_build_render_cmd(hunitest.TestCase):
    """
    Test the `_build_render_cmd()` function.
    """

    def helper(self, argv: List[str], input_file: str, expected: str) -> None:
        """
        Build the command for `input_file` and check it.

        :param argv: command line arguments of the script
        :param input_file: file to render
        :param expected: expected command
        """
        args = dshdopmd._parse().parse_args(argv)
        with (
            mock.patch("sys.executable", "/usr/bin/python"),
            mock.patch("sys.argv", ["/path/to/open_md.py"]),
        ):
            actual = dshdopmd._build_render_cmd(args, input_file)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test `pandoc` mode asks for the HTML to reload itself.
        """
        # Prepare inputs.
        argv = ["--files", "a.md b.md", "--mode", "pandoc", "--daemon"]
        input_file = "a.md"
        # Prepare outputs.
        expected = (
            "/usr/bin/python /path/to/open_md.py --input a.md --mode pandoc "
            "--backend global --link_type local --toc_depth 2 -v INFO --live_reload"
        )
        # Run test.
        self.helper(argv, input_file, expected)

    def test2(self) -> None:
        """
        Test `--css` and the dockerized options are passed through, and a path
        with spaces is quoted.
        """
        # Prepare inputs.
        argv = [
            "--input",
            "a.md",
            "--css",
            "my style.html",
            "--backend",
            "dockerized",
            "--dockerized_force_rebuild",
            "--dockerized_use_sudo",
        ]
        input_file = "my docs/a.md"
        # Prepare outputs.
        expected = (
            "/usr/bin/python /path/to/open_md.py --input 'my docs/a.md' "
            "--mode pandoc --backend dockerized --link_type local --toc_depth 2 "
            "-v INFO "
            "--css 'my style.html' --dockerized_force_rebuild "
            "--dockerized_use_sudo --live_reload"
        )
        # Run test.
        self.helper(argv, input_file, expected)

    def test3(self) -> None:
        """
        Test `pdf` mode doesn't ask for a reload, since the PDF viewer reloads
        the file.
        """
        # Prepare inputs.
        argv = ["--input", "a.md", "--mode", "pdf", "-v", "DEBUG"]
        input_file = "a.md"
        # Prepare outputs.
        expected = (
            "/usr/bin/python /path/to/open_md.py --input a.md --mode pdf "
            "--backend global --link_type local --toc_depth 2 -v DEBUG"
        )
        # Run test.
        self.helper(argv, input_file, expected)

    def test4(self) -> None:
        """
        Test `--link_type` is passed through.
        """
        # Prepare inputs.
        argv = ["--input", "a.md", "--mode", "pdf", "--link_type", "master"]
        input_file = "a.md"
        # Prepare outputs.
        expected = (
            "/usr/bin/python /path/to/open_md.py --input a.md --mode pdf "
            "--backend global --link_type master --toc_depth 2 -v INFO"
        )
        # Run test.
        self.helper(argv, input_file, expected)

    def test5(self) -> None:
        """
        Test `--toc` and `--toc_depth` are passed through.
        """
        # Prepare inputs.
        argv = ["--input", "a.md", "--mode", "pdf", "--toc", "--toc_depth", "3"]
        input_file = "a.md"
        # Prepare outputs.
        expected = (
            "/usr/bin/python /path/to/open_md.py --input a.md --mode pdf "
            "--backend global --link_type local --toc_depth 3 -v INFO --toc"
        )
        # Run test.
        self.helper(argv, input_file, expected)

    def test6(self) -> None:
        """
        Test `--no_toc` is passed through.
        """
        # Prepare inputs.
        argv = ["--input", "a.md", "--mode", "pdf", "--no_toc"]
        input_file = "a.md"
        # Prepare outputs.
        expected = (
            "/usr/bin/python /path/to/open_md.py --input a.md --mode pdf "
            "--backend global --link_type local --toc_depth 2 -v INFO --no_toc"
        )
        # Run test.
        self.helper(argv, input_file, expected)


# #############################################################################
# Test_open_md_py_main
# #############################################################################


class Test_open_md_py_main(hunitest.TestCase):
    """
    Test `_main()` called directly (in-process) with mocked `sys.argv`.
    """

    def _create_input_file(self, name: str = "readme.md") -> str:
        """
        Create a markdown file in the scratch dir.

        :param name: file name
        :return: absolute path of the file
        """
        input_file = os.path.join(self.get_scratch_space(), name)
        hio.to_file(input_file, "# Title")
        return input_file

    def test1(self) -> None:
        """
        Test `--mode github` dispatches to `_open_on_github()`.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        mode = "github"
        argv = ["open_md.py", "--input", input_file, "--mode", mode]
        parser = dshdopmd._parse()
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_open_on_github") as mock_fn,
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(input_file)

    def test2(self) -> None:
        """
        Test `--mode grip_daemon` dispatches to
        `_render_with_grip_daemon()`.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
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
        with (
            mock.patch.object(dshdopmd, "_render_with_grip_daemon") as mock_fn,
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(
            input_file, backend=backend, link_type="local"
        )

    def test3(self) -> None:
        """
        Test `--mode pandoc` dispatches to `_render_with_pandoc()`
        with the dockerized-force-rebuild arguments and defaults to
        the bundled GitHub-like style.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        mode = "pandoc"
        argv = ["open_md.py", "--input", input_file, "--mode", mode]
        parser = dshdopmd._parse()
        # Prepare outputs.
        expected_backend = "global"
        expected_force_rebuild = False
        expected_use_sudo = False
        expected_style_file = "/some/path/github_style.html"
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn,
            mock.patch(
                "helpers.hgit.find_file", return_value=expected_style_file
            ),
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(
            input_file,
            backend=expected_backend,
            force_rebuild=expected_force_rebuild,
            use_sudo=expected_use_sudo,
            style_file=expected_style_file,
            skip_open=False,
            live_reload=False,
            link_type="local",
            toc_depth=2,
        )

    def test3a(self) -> None:
        """
        Test `--mode pandoc --css` overrides the default GitHub-like
        style with the custom CSS file.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        mode = "pandoc"
        css_file = "my_style.html"
        argv = [
            "open_md.py",
            "--input",
            input_file,
            "--mode",
            mode,
            "--css",
            css_file,
        ]
        parser = dshdopmd._parse()
        # Prepare outputs.
        expected_backend = "global"
        expected_force_rebuild = False
        expected_use_sudo = False
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn,
            mock.patch("helpers.hgit.find_file") as mock_find_file,
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs: `--css` wins, so `find_file()` is never called.
        mock_find_file.assert_not_called()
        mock_fn.assert_called_once_with(
            input_file,
            backend=expected_backend,
            force_rebuild=expected_force_rebuild,
            use_sudo=expected_use_sudo,
            style_file=css_file,
            skip_open=False,
            live_reload=False,
            link_type="local",
            toc_depth=2,
        )

    def test3b(self) -> None:
        """
        Test omitting `--mode` defaults to `pandoc`.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        argv = ["open_md.py", "--input", input_file]
        parser = dshdopmd._parse()
        # Prepare outputs.
        expected_style_file = "/some/path/github_style.html"
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn,
            mock.patch(
                "helpers.hgit.find_file", return_value=expected_style_file
            ),
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(
            input_file,
            backend="global",
            force_rebuild=False,
            use_sudo=False,
            style_file=expected_style_file,
            skip_open=False,
            live_reload=False,
            link_type="local",
            toc_depth=2,
        )

    def test4(self) -> None:
        """
        Test `--mode grip` dispatches to `_render_with_grip()`.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        mode = "grip"
        backend = "global"
        argv = ["open_md.py", "--input", input_file, "--mode", mode]
        parser = dshdopmd._parse()
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_render_with_grip") as mock_fn,
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once_with(
            input_file,
            backend=backend,
            skip_open=False,
            live_reload=False,
            link_type="local",
        )

    def test5(self) -> None:
        """
        Test several files are each rendered, in order.
        """
        # Prepare inputs.
        input_file1 = self._create_input_file("a.md")
        input_file2 = self._create_input_file("b.md")
        files_str = f"{input_file1} {input_file2}"
        argv = ["open_md.py", "--files", files_str, "--mode", "pandoc"]
        parser = dshdopmd._parse()
        style_file = "/some/path/github_style.html"
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn,
            mock.patch("helpers.hgit.find_file", return_value=style_file),
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        actual = [call.args[0] for call in mock_fn.call_args_list]
        expected = [input_file1, input_file2]
        self.assertEqual(actual, expected)

    def test6(self) -> None:
        """
        Test `--mode grip_daemon` rejects more than one file.
        """
        # Prepare inputs.
        input_file1 = self._create_input_file("a.md")
        input_file2 = self._create_input_file("b.md")
        files_str = f"{input_file1} {input_file2}"
        argv = ["open_md.py", "--files", files_str, "--mode", "grip_daemon"]
        parser = dshdopmd._parse()
        # Run test and check output.
        with (
            mock.patch.object(dshdopmd, "_render_with_grip_daemon") as mock_fn,
            mock.patch("sys.argv", argv),
            self.assertRaises(AssertionError) as cm,
        ):
            dshdopmd._main(parser)
        self.assertIn("single file", str(cm.exception))
        mock_fn.assert_not_called()

    def test7(self) -> None:
        """
        Test `--daemon` watches all the files and builds a command per file.
        """
        # Prepare inputs.
        input_file1 = self._create_input_file("a.md")
        input_file2 = self._create_input_file("b.md")
        files_str = f"{input_file1} {input_file2}"
        argv = ["open_md.py", "--files", files_str, "--daemon"]
        parser = dshdopmd._parse()
        # Run test.
        with (
            mock.patch.object(
                dshdopmd.hdaemon, "run_reactive_daemon_mode_multi"
            ) as mock_fn,
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        mock_fn.assert_called_once()
        actual_files, cmd_func, window_name = mock_fn.call_args.args
        self.assertEqual(actual_files, [input_file1, input_file2])
        self.assertEqual(window_name, "open_md")
        self.assertEqual(
            mock_fn.call_args.kwargs, {"watch_cmd_suffix": " --skip_open"}
        )
        actual_cmd = cmd_func(input_file2)
        self.assertIn(f"--input {input_file2}", actual_cmd)
        self.assertIn("--live_reload", actual_cmd)
        self.assertNotIn("--daemon", actual_cmd)

    def test8(self) -> None:
        """
        Test `--daemon` is rejected for `github` mode.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        argv = [
            "open_md.py",
            "--input",
            input_file,
            "--mode",
            "github",
            "--daemon",
        ]
        parser = dshdopmd._parse()
        # Run test and check output.
        with (
            mock.patch("sys.argv", argv),
            self.assertRaises(AssertionError) as cm,
        ):
            dshdopmd._main(parser)
        self.assertIn("--daemon is only supported", str(cm.exception))

    def test9(self) -> None:
        """
        Test `--link_type` is passed to `_render_with_pandoc()`.
        """
        # Prepare inputs.
        input_file = self._create_input_file()
        argv = ["open_md.py", "--input", input_file, "--link_type", "branch"]
        parser = dshdopmd._parse()
        # Run test.
        with (
            mock.patch.object(dshdopmd, "_render_with_pandoc") as mock_fn,
            mock.patch("helpers.hgit.find_file", return_value="style.html"),
            mock.patch("sys.argv", argv),
        ):
            dshdopmd._main(parser)
        # Check outputs.
        self.assertEqual(mock_fn.call_args.kwargs["link_type"], "branch")

    def test10(self) -> None:
        """
        Test an invalid `--link_type` is rejected.
        """
        # Prepare inputs.
        argv = ["--input", "a.md", "--link_type", "remote"]
        parser = dshdopmd._parse()
        # Run test and check output.
        with self.assertRaises(SystemExit):
            parser.parse_args(argv)


# #############################################################################
# Test_encode_links
# #############################################################################


class Test_encode_links(hunitest.TestCase):
    """
    Test the `_encode_links()` function.
    """

    def helper(self, text: str, link_type: str, expected: str) -> None:
        """
        Encode the links of `text` in a file of a fake repo and check the result.

        The fake repo root is the scratch dir `repo`, with the file
        `docs/prd.md` and the dir `docs/figs` in it.

        :param text: content of the markdown file
        :param link_type: how to encode the links
        :param expected: expected content, where `$ROOT` is the repo root
        """
        # Prepare inputs.
        repo_root = os.path.join(self.get_scratch_space(), "repo")
        os.makedirs(os.path.join(repo_root, ".git"))
        os.makedirs(os.path.join(repo_root, "docs", "figs"))
        hio.to_file(os.path.join(repo_root, "docs", "prd.md"), "# PRD")
        input_file = os.path.join(repo_root, "docs", "input.md")
        hio.to_file(input_file, text)
        processed_file = os.path.join(repo_root, "tmp.input.md")
        hio.to_file(processed_file, text)
        # Run test.
        with (
            mock.patch.object(
                dshdopmd,
                "_get_remote_url_and_branch",
                return_value=("https://github.com/org/repo", "my_branch"),
            ),
        ):
            dshdopmd._encode_links(processed_file, input_file, link_type)
        # Check outputs.
        actual = hio.from_file(processed_file)
        expected = expected.replace("$ROOT", repo_root)
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test `local` encodes the link as a `file://` URL and keeps the anchor.
        """
        text = "See [prd](/docs/prd.md#goal) and [figs](/docs/figs/)."
        expected = (
            "See [prd](file://$ROOT/docs/prd.md#goal) and "
            "[figs](file://$ROOT/docs/figs/)."
        )
        self.helper(text, "local", expected)

    def test2(self) -> None:
        """
        Test `branch` encodes the link as a GitHub URL on the current branch,
        with `tree` for a dir.
        """
        text = "See [prd](/docs/prd.md#goal) and [figs](/docs/figs)."
        expected = (
            "See [prd](https://github.com/org/repo/blob/my_branch/docs/prd.md"
            "#goal) and [figs](https://github.com/org/repo/tree/my_branch/docs/"
            "figs)."
        )
        self.helper(text, "branch", expected)

    def test2a(self) -> None:
        """
        Test a link ending with `/` is a `tree` URL even if the dir does not
        exist.
        """
        text = "See [tests](/test/) and [root](/)."
        expected = (
            "See [tests](https://github.com/org/repo/tree/master/test/) and "
            "[root](https://github.com/org/repo/tree/master/)."
        )
        self.helper(text, "master", expected)

    def test3(self) -> None:
        """
        Test `master` encodes the link as a GitHub URL on `master`.
        """
        text = "See [`docs/prd.md`](/docs/prd.md)."
        expected = (
            "See [`docs/prd.md`](https://github.com/org/repo/blob/master/docs/"
            "prd.md)."
        )
        self.helper(text, "master", expected)

    def test4(self) -> None:
        """
        Test images, other URLs, relative links, and fenced code are not changed.
        """
        text = """
        ![fig](/docs/fig.png)
        [web](https://example.com/a) [proto](//example.com/a) [rel](prd.md)
        ```bash
        > open [prd](/docs/prd.md)
        ```
        [prd](/docs/prd.md)
        """
        text = hprint.dedent(text)
        expected = """
        ![fig](/docs/fig.png)
        [web](https://example.com/a) [proto](//example.com/a) [rel](prd.md)
        ```bash
        > open [prd](/docs/prd.md)
        ```
        [prd](file://$ROOT/docs/prd.md)
        """
        self.helper(text, "local", expected)

    def helper_submodule(self, link_type: str, expected: str) -> None:
        """
        Encode links to a submodule and to a symlink into it, and check them.

        The fake repo has the submodule `sub`, and the symlink `.claude` that
        points to `sub/.claude`.

        :param link_type: how to encode the links
        :param expected: expected content
        """
        # Prepare inputs.
        repo_root = os.path.join(self.get_scratch_space(), "repo")
        sub_root = os.path.join(repo_root, "sub")
        os.makedirs(os.path.join(repo_root, ".git"))
        os.makedirs(os.path.join(sub_root, ".claude", "skills"))
        hio.to_file(
            os.path.join(sub_root, ".git"), "gitdir: ../.git/modules/sub"
        )
        hio.to_file(os.path.join(sub_root, "a.py"), "# a")
        hio.to_file(os.path.join(sub_root, ".claude", "skills", "r.md"), "# r")
        os.symlink(
            os.path.join("sub", ".claude"), os.path.join(repo_root, ".claude")
        )
        text = "[a](/sub/a.py) [r](/.claude/skills/r.md) [sub](/sub/) [b](/b.md)"
        input_file = os.path.join(repo_root, "input.md")
        hio.to_file(input_file, text)
        processed_file = os.path.join(repo_root, "tmp.input.md")
        hio.to_file(processed_file, text)

        def _get_remote_url_and_branch(root: str) -> Tuple[str, str]:
            if os.path.realpath(root) == os.path.realpath(sub_root):
                return "https://github.com/org/sub", "sub_branch"
            return "https://github.com/org/repo", "repo_branch"

        # Run test.
        with mock.patch.object(
            dshdopmd,
            "_get_remote_url_and_branch",
            side_effect=_get_remote_url_and_branch,
        ):
            dshdopmd._encode_links(processed_file, input_file, link_type)
        # Check outputs.
        actual = hio.from_file(processed_file)
        self.assertEqual(actual, expected)

    def test5a(self) -> None:
        """
        Test `branch` links to a submodule and to a symlink into it use the
        remote, the branch, and the path relative to the root of the submodule.
        """
        expected = (
            "[a](https://github.com/org/sub/blob/sub_branch/a.py) "
            "[r](https://github.com/org/sub/blob/sub_branch/.claude/skills/"
            "r.md) [sub](https://github.com/org/sub/tree/sub_branch/) "
            "[b](https://github.com/org/repo/blob/repo_branch/b.md)"
        )
        self.helper_submodule("branch", expected)

    def test5b(self) -> None:
        """
        Test `master` links to a submodule use the remote of the submodule.
        """
        expected = (
            "[a](https://github.com/org/sub/blob/master/a.py) "
            "[r](https://github.com/org/sub/blob/master/.claude/skills/r.md) "
            "[sub](https://github.com/org/sub/tree/master/) "
            "[b](https://github.com/org/repo/blob/master/b.md)"
        )
        self.helper_submodule("master", expected)

    def test5(self) -> None:
        """
        Test the repo is not queried when there is no link to encode.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title\n[web](https://example.com)")
        # Run test.
        with mock.patch.object(
            dshdopmd, "_get_remote_url_and_branch"
        ) as mock_fn:
            dshdopmd._encode_links(input_file, input_file, "branch")
        # Check outputs.
        mock_fn.assert_not_called()
        self.assertEqual(
            hio.from_file(input_file), "# Title\n[web](https://example.com)"
        )


# #############################################################################
# Test_get_toc_depth
# #############################################################################


class Test_get_toc_depth(hunitest.TestCase):
    """
    Test the `_get_toc_depth()` function.
    """

    def helper(self, text: str, argv: List[str], expected: int) -> None:
        """
        Get the TOC depth for a file with `text` and check it.

        :param text: content of the markdown file
        :param argv: extra command line arguments
        :param expected: expected TOC depth
        """
        input_file = os.path.join(self.get_scratch_space(), "input.md")
        hio.to_file(input_file, text)
        args = dshdopmd._parse().parse_args(["--input", input_file] + argv)
        actual = dshdopmd._get_toc_depth(args, input_file)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test a TOC of depth 2 is added by default.
        """
        self.helper("# Title", [], 2)

    def test2(self) -> None:
        """
        Test `--toc_depth` sets the depth of the default TOC.
        """
        self.helper("# Title", ["--toc_depth", "3"], 3)

    def test3(self) -> None:
        """
        Test no TOC is added to a file that already has one.
        """
        self.helper("# Title\n<!-- toc -->\n", [], 0)

    def test4(self) -> None:
        """
        Test `--toc` adds a TOC also to a file that already has one.
        """
        self.helper("# Title\n<!-- toc -->\n", ["--toc"], 2)

    def test5(self) -> None:
        """
        Test `--no_toc` never adds a TOC.
        """
        self.helper("# Title", ["--no_toc"], 0)

    def test6(self) -> None:
        """
        Test `--toc` and `--no_toc` are mutually exclusive.
        """
        parser = dshdopmd._parse()
        with self.assertRaises(SystemExit):
            parser.parse_args(["--input", "a.md", "--toc", "--no_toc"])


# #############################################################################
# Test_toc_in_pandoc_cmd
# #############################################################################


class Test_toc_in_pandoc_cmd(hunitest.TestCase):
    """
    Test the TOC options in the pandoc command of `pandoc` and `pdf` modes.
    """

    def helper(self, mode: str, toc_depth: int) -> str:
        """
        Render a file with a mocked pandoc and return the pandoc command.

        :param mode: `pandoc` or `pdf`
        :param toc_depth: depth of the TOC passed to the render function
        :return: pandoc command
        """
        scratch_dir = self.get_scratch_space()
        input_file = os.path.join(scratch_dir, "input.md")
        hio.to_file(input_file, "# Title")
        ext = "html" if mode == "pandoc" else "pdf"
        output_file = os.path.join(scratch_dir, f"tmp.input.{ext}")

        def _create_output(*_args: object, **_kwargs: object) -> int:
            hio.to_file(output_file, "output")
            return 0

        render = (
            dshdopmd._render_with_pandoc
            if mode == "pandoc"
            else dshdopmd._render_with_pdf
        )
        cwd = os.getcwd()
        os.chdir(scratch_dir)
        try:
            with (
                mock.patch.object(
                    dshdopmd, "_run_render_images", return_value=input_file
                ),
                mock.patch(
                    "helpers.hsystem.system", side_effect=_create_output
                ) as mock_system,
                mock.patch.object(dshdopmd, "_open_file"),
            ):
                render(input_file, backend="global", toc_depth=toc_depth)
        finally:
            os.chdir(cwd)
        return mock_system.call_args[0][0]

    def test1(self) -> None:
        """
        Test `pandoc` mode passes the TOC options to pandoc.
        """
        actual = self.helper("pandoc", 2)
        self.assertIn("--toc --toc-depth=2", actual)

    def test2(self) -> None:
        """
        Test `pandoc` mode doesn't pass the TOC options with depth 0.
        """
        actual = self.helper("pandoc", 0)
        self.assertNotIn("--toc", actual)

    def test3(self) -> None:
        """
        Test `pdf` mode passes the TOC options to pandoc.
        """
        actual = self.helper("pdf", 3)
        self.assertIn("--toc --toc-depth=3", actual)

    def test4(self) -> None:
        """
        Test `pdf` mode doesn't pass the TOC options with depth 0.
        """
        actual = self.helper("pdf", 0)
        self.assertNotIn("--toc", actual)
