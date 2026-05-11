import contextlib
import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import dev_scripts_helpers.git.git_hooks.install_hooks as dshgghinho
import dev_scripts_helpers.git.git_hooks.utils as dshgghout


_GIT_HOOKS_DIR = pathlib.Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def _pushd(dst_dir: pathlib.Path):
    src_dir = pathlib.Path.cwd()
    os.chdir(dst_dir)
    try:
        yield
    finally:
        os.chdir(src_dir)


def _load_hook_module(file_name: str, module_name: str):
    path = _GIT_HOOKS_DIR / file_name
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Test_git_hook_checks(unittest.TestCase):
    def test_check_master_rejects_master_branch(self) -> None:
        with mock.patch.object(
            dshgghout, "_system_to_string", return_value=(0, "master\n")
        ), mock.patch.object(dshgghout, "_handle_error") as handle_error:
            dshgghout.check_master(abort_on_error=False)
        handle_error.assert_called_once_with("check_master", True, False)

    def test_check_master_accepts_feature_branch(self) -> None:
        with mock.patch.object(
            dshgghout,
            "_system_to_string",
            return_value=(0, "test/git-hooks\n"),
        ), mock.patch.object(dshgghout, "_handle_error") as handle_error:
            dshgghout.check_master(abort_on_error=False)
        handle_error.assert_called_once_with("check_master", False, False)

    def test_check_merged_branch_blocks_reused_branch(self) -> None:
        responses = [
            (0, "feature\n"),
            (0, "  master\n"),
            (1, ""),
            (0, "  master\n* feature\n"),
            (0, "abc HEAD@{0}: commit: Add change\n"),
        ]
        with mock.patch.object(
            dshgghout, "_system_to_string", side_effect=responses
        ), mock.patch.object(dshgghout, "_handle_error") as handle_error:
            dshgghout.check_merged_branch(abort_on_error=False)
        handle_error.assert_called_once_with(
            "check_merged_branch", True, False
        )

    def test_check_author_rejects_invalid_email(self) -> None:
        with mock.patch.object(dshgghout, "_system"), mock.patch.object(
            dshgghout, "_system_to_string", return_value=(0, "not-an-email\n")
        ), mock.patch.object(dshgghout, "_handle_error") as handle_error:
            dshgghout.check_author(abort_on_error=False)
        handle_error.assert_called_once_with("check_author", True, False)

    def test_check_author_accepts_valid_email(self) -> None:
        with mock.patch.object(dshgghout, "_system"), mock.patch.object(
            dshgghout,
            "_system_to_string",
            return_value=(0, "dev@example.com\n"),
        ), mock.patch.object(dshgghout, "_handle_error") as handle_error:
            dshgghout.check_author(abort_on_error=False)
        handle_error.assert_called_once_with("check_author", False, False)

    def test_check_file_size_rejects_large_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = pathlib.Path(tmpdir) / "large.txt"
            file_path.write_bytes(
                b"x" * (dshgghout._MAX_FILE_SIZE_IN_KB * 1024 + 1)
            )
            with mock.patch.object(
                dshgghout, "_handle_error"
            ) as handle_error:
                dshgghout.check_file_size(
                    abort_on_error=False, file_list=[str(file_path)]
                )
        handle_error.assert_called_once_with("check_file_size", True, False)

    def test_check_file_size_allows_large_notebook(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = pathlib.Path(tmpdir) / "large.ipynb"
            file_path.write_bytes(
                b"x" * (dshgghout._MAX_FILE_SIZE_IN_KB * 1024 + 1)
            )
            with mock.patch.object(
                dshgghout, "_handle_error"
            ) as handle_error:
                dshgghout.check_file_size(
                    abort_on_error=False, file_list=[str(file_path)]
                )
        handle_error.assert_called_once_with("check_file_size", False, False)

    def test_check_python_compile_detects_invalid_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = pathlib.Path(tmpdir)
            good_file = tmpdir_path / "good.py"
            good_file.write_text("VALUE = 1\n", encoding="utf-8")
            bad_file = tmpdir_path / "bad.py"
            bad_file.write_text("def broken(:\n", encoding="utf-8")
            self.assertFalse(dshgghout._check_python_compile([str(good_file)]))
            self.assertTrue(dshgghout._check_python_compile([str(bad_file)]))

    def test_check_python_compile_filters_non_python_files(self) -> None:
        with mock.patch.object(
            dshgghout, "_check_python_compile", return_value=False
        ) as check_python_compile, mock.patch.object(
            dshgghout, "_handle_error"
        ) as handle_error:
            dshgghout.check_python_compile(
                abort_on_error=False, file_list=["a.py", "notes.txt"]
            )
        check_python_compile.assert_called_once_with(["a.py"])
        handle_error.assert_called_once_with(
            "check_python_compile", False, False
        )

    def test_check_gitleaks_reports_failing_scan(self) -> None:
        with mock.patch.object(
            dshgghout.hgit, "find_git_root", return_value="/repo"
        ), mock.patch.object(
            dshgghout.hgit,
            "find_helpers_root",
            return_value="/repo/helpers_root",
        ), mock.patch.object(
            dshgghout, "_system", return_value=1
        ) as system, mock.patch.object(
            dshgghout, "_handle_error"
        ) as handle_error:
            dshgghout.check_gitleaks(abort_on_error=False)
        self.assertIn("zricethezav/gitleaks:latest", system.call_args[0][0])
        handle_error.assert_called_once_with("check_gitleaks", True, False)


class Test_commit_msg_hook(unittest.TestCase):
    def test_commit_msg_appends_precommit_output(self) -> None:
        module = _load_hook_module("commit-msg.py", "commit_msg_hook")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = pathlib.Path(tmpdir)
            message_file = tmpdir_path / "COMMIT_EDITMSG"
            message_file.write_text("Add hook tests\n", encoding="utf-8")
            (tmpdir_path / "tmp.precommit_output.txt").write_text(
                "Pre-commit checks:\nAll checks passed\n", encoding="utf-8"
            )
            with _pushd(tmpdir_path), mock.patch.object(
                sys, "argv", ["commit-msg.py", str(message_file)]
            ):
                module._main()
            message = message_file.read_text(encoding="utf-8")
        self.assertIn("Add hook tests", message)
        self.assertIn("Pre-commit checks:", message)
        self.assertIn("All checks passed", message)

    def test_commit_msg_rejects_lowercase_subject(self) -> None:
        module = _load_hook_module("commit-msg.py", "commit_msg_hook_invalid")
        with tempfile.TemporaryDirectory() as tmpdir:
            message_file = pathlib.Path(tmpdir) / "COMMIT_EDITMSG"
            message_file.write_text("lowercase subject\n", encoding="utf-8")
            with mock.patch.object(
                sys, "argv", ["commit-msg.py", str(message_file)]
            ):
                with self.assertRaises(SystemExit) as cm:
                    module._main()
        self.assertEqual(cm.exception.code, 1)


class Test_install_hooks(unittest.TestCase):
    def _make_helpers_root(self, tmpdir_path: pathlib.Path) -> pathlib.Path:
        helpers_root = tmpdir_path / "helpers_root"
        hook_dir = helpers_root / "dev_scripts_helpers/git/git_hooks"
        hook_dir.mkdir(parents=True)
        (hook_dir / "pre-commit.py").write_text(
            "#!/usr/bin/env python\n", encoding="utf-8"
        )
        (hook_dir / "commit-msg.py").write_text(
            "#!/usr/bin/env python\n", encoding="utf-8"
        )
        return helpers_root

    def test_install_hooks_builds_expected_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = pathlib.Path(tmpdir)
            helpers_root = self._make_helpers_root(tmpdir_path)
            target_dir = tmpdir_path / ".git/hooks"
            target_dir.mkdir(parents=True)
            with mock.patch.object(
                sys, "argv", ["install_hooks.py", "--action", "install"]
            ), mock.patch.object(
                dshgghinho.hgit,
                "find_helpers_root",
                return_value=str(helpers_root),
            ), mock.patch.object(
                dshgghinho.hsystem,
                "system_to_one_line",
                return_value=(0, str(target_dir)),
            ), mock.patch.object(
                dshgghinho.hsystem, "system"
            ) as system:
                dshgghinho._main()
        commands = [call.args[0] for call in system.call_args_list]
        self.assertEqual(len(commands), 6)
        self.assertTrue(commands[0].startswith("ln -sf "))
        self.assertIn("pre-commit.py", commands[0])
        self.assertIn(str(target_dir / "pre-commit"), commands[0])
        self.assertTrue(commands[3].startswith("ln -sf "))
        self.assertIn("commit-msg.py", commands[3])
        self.assertIn(str(target_dir / "commit-msg"), commands[3])

    def test_remove_hooks_unlinks_existing_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = pathlib.Path(tmpdir)
            helpers_root = self._make_helpers_root(tmpdir_path)
            target_dir = tmpdir_path / ".git/hooks"
            target_dir.mkdir(parents=True)
            (target_dir / "pre-commit").write_text("", encoding="utf-8")
            (target_dir / "commit-msg").write_text("", encoding="utf-8")
            with mock.patch.object(
                sys, "argv", ["install_hooks.py", "--action", "remove"]
            ), mock.patch.object(
                dshgghinho.hgit,
                "find_helpers_root",
                return_value=str(helpers_root),
            ), mock.patch.object(
                dshgghinho.hsystem,
                "system_to_one_line",
                return_value=(0, str(target_dir)),
            ), mock.patch.object(
                dshgghinho.hsystem, "system"
            ) as system:
                dshgghinho._main()
        commands = [call.args[0] for call in system.call_args_list]
        self.assertEqual(
            commands,
            [
                f"unlink {target_dir / 'pre-commit'}",
                f"unlink {target_dir / 'commit-msg'}",
            ],
        )

    @unittest.skipIf(os.name == "nt", "ln-based hook install is POSIX-only")
    def test_install_and_remove_hooks_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = pathlib.Path(tmpdir)
            helpers_root = self._make_helpers_root(tmpdir_path)
            target_dir = tmpdir_path / ".git/hooks"
            target_dir.mkdir(parents=True)
            with mock.patch.object(
                dshgghinho.hgit,
                "find_helpers_root",
                return_value=str(helpers_root),
            ), mock.patch.object(
                dshgghinho.hsystem,
                "system_to_one_line",
                return_value=(0, str(target_dir)),
            ):
                with mock.patch.object(
                    sys, "argv", ["install_hooks.py", "--action", "install"]
                ):
                    dshgghinho._main()
                self.assertTrue((target_dir / "pre-commit").exists())
                self.assertTrue((target_dir / "commit-msg").exists())
                with mock.patch.object(
                    sys, "argv", ["install_hooks.py", "--action", "remove"]
                ):
                    dshgghinho._main()
                self.assertFalse((target_dir / "pre-commit").exists())
                self.assertFalse((target_dir / "commit-msg").exists())


class Test_pre_commit_hook(unittest.TestCase):
    def test_write_output_to_file(self) -> None:
        module = _load_hook_module("pre-commit.py", "pre_commit_hook")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = pathlib.Path(tmpdir)
            with _pushd(tmpdir_path):
                module._write_output_to_file(["Pre-commit checks:", "pass"])
            output = (tmpdir_path / "tmp.precommit_output.txt").read_text(
                encoding="utf-8"
            )
        self.assertEqual(output, "Pre-commit checks:\npass\n")
