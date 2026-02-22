import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as umock
from typing import Dict, List

import dev_scripts_helpers.git.git_hooks.utils as dsgghout

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_GIT_HOOKS_DIR = pathlib.Path("dev_scripts_helpers/git/git_hooks")


def _build_env(extra_env: Dict[str, str]) -> Dict[str, str]:
    env = dict(os.environ)
    repo_root = str(_REPO_ROOT)
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{repo_root}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = repo_root
    env.update(extra_env)
    return env


def _run_cmd(
    cmd: List[str], cwd: pathlib.Path, env: Dict[str, str]
) -> subprocess.CompletedProcess[str]:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def _copy_git_hooks_tree(dst_repo: pathlib.Path) -> None:
    src_dev_scripts = _REPO_ROOT / "dev_scripts_helpers"
    dst_dev_scripts = dst_repo / "dev_scripts_helpers"
    (dst_dev_scripts / "git").mkdir(parents=True)
    shutil.copy2(
        src_dev_scripts / "__init__.py",
        dst_dev_scripts / "__init__.py",
    )
    shutil.copy2(
        src_dev_scripts / "git/__init__.py",
        dst_dev_scripts / "git/__init__.py",
    )
    shutil.copytree(
        src_dev_scripts / "git/git_hooks", dst_dev_scripts / "git/git_hooks"
    )


class _GitHooksTestCase(unittest.TestCase):
    def _assert_cmd_ok(
        self, result: subprocess.CompletedProcess[str], cmd: str
    ) -> None:
        msg = (
            f"Command failed: {cmd}\n"
            f"returncode={result.returncode}\n"
            f"stdout=\n{result.stdout}\n"
            f"stderr=\n{result.stderr}"
        )
        self.assertEqual(result.returncode, 0, msg=msg)


class TestGitHooksChecks1(_GitHooksTestCase):
    def test_check_master_fails_on_master_branch1(self) -> None:
        with umock.patch.object(
            dsgghout, "_system_to_string", return_value=(0, "master\n")
        ):
            with self.assertRaises(SystemExit):
                dsgghout.check_master(abort_on_error=True)

    def test_check_master_passes_on_feature_branch1(self) -> None:
        with umock.patch.object(
            dsgghout, "_system_to_string", return_value=(0, "feature/test\n")
        ):
            dsgghout.check_master(abort_on_error=True)

    def test_check_author_fails_for_invalid_email1(self) -> None:
        with umock.patch.object(
            dsgghout, "_system", return_value=0
        ), umock.patch.object(
            dsgghout,
            "_system_to_string",
            return_value=(0, "invalid_email\n"),
        ):
            with self.assertRaises(SystemExit):
                dsgghout.check_author(abort_on_error=True)

    def test_check_author_passes_for_valid_email1(self) -> None:
        with umock.patch.object(
            dsgghout, "_system", return_value=0
        ), umock.patch.object(
            dsgghout,
            "_system_to_string",
            return_value=(0, "dev@example.com\n"),
        ):
            dsgghout.check_author(abort_on_error=True)

    def test_check_file_size_fails_for_large_file1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = pathlib.Path(tmp_dir) / "too_big.txt"
            file_path.write_bytes(b"a" * 2048)
            with umock.patch.object(dsgghout, "_MAX_FILE_SIZE_IN_KB", 1):
                with self.assertRaises(SystemExit):
                    dsgghout.check_file_size(
                        abort_on_error=True,
                        file_list=[str(file_path)],
                    )

    def test_check_python_compile_fails_for_invalid_file1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = pathlib.Path(tmp_dir) / "invalid.py"
            file_path.write_text("def broken(:\n    pass\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                dsgghout.check_python_compile(
                    abort_on_error=True,
                    file_list=[str(file_path)],
                )

    def test_check_gitleaks_passes_on_zero_return_code1(self) -> None:
        with umock.patch.object(
            dsgghout.hgit, "find_git_root", return_value="/tmp/repo"
        ), umock.patch.object(
            dsgghout.hgit, "find_helpers_root", return_value="/tmp/repo"
        ), umock.patch.object(
            dsgghout, "_system", return_value=0
        ):
            dsgghout.check_gitleaks(abort_on_error=True)

    def test_check_gitleaks_fails_on_non_zero_return_code1(self) -> None:
        with umock.patch.object(
            dsgghout.hgit, "find_git_root", return_value="/tmp/repo"
        ), umock.patch.object(
            dsgghout.hgit, "find_helpers_root", return_value="/tmp/repo"
        ), umock.patch.object(
            dsgghout, "_system", return_value=1
        ):
            with self.assertRaises(SystemExit):
                dsgghout.check_gitleaks(abort_on_error=True)


class TestCommitMsgHook1(_GitHooksTestCase):
    def _run_commit_msg_hook(
        self,
        message: str,
        precommit_output: str,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = pathlib.Path(tmp_dir)
            message_file = tmp_path / "message.txt"
            message_file.write_text(message, encoding="utf-8")
            precommit_file = tmp_path / "tmp.precommit_output.txt"
            precommit_file.write_text(precommit_output, encoding="utf-8")
            cmd = [
                sys.executable,
                str(_REPO_ROOT / _GIT_HOOKS_DIR / "commit-msg.py"),
                str(message_file),
            ]
            env = _build_env({})
            result = _run_cmd(cmd, tmp_path, env)
            result.stdout += message_file.read_text(encoding="utf-8")
            return result

    def test_commit_msg_passes_for_valid_message1(self) -> None:
        result = self._run_commit_msg_hook(
            "Initial commit\n",
            "Pre-commit checks:\nAll checks passed\n",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Pre-commit checks:", result.stdout)

    def test_commit_msg_fails_for_invalid_message1(self) -> None:
        result = self._run_commit_msg_hook(
            "invalid commit\n",
            "Pre-commit checks:\nAll checks passed\n",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Pre-commit checks:", result.stdout)


class TestGitHooksIntegration1(_GitHooksTestCase):
    def test_install_commit_and_remove_hooks1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = pathlib.Path(tmp_dir) / "repo"
            repo_dir.mkdir()
            _copy_git_hooks_tree(repo_dir)
            env = _build_env(
                {
                    "CSFY_REPO_CONFIG_PATH": str(
                        _REPO_ROOT / "repo_config.yaml"
                    )
                }
            )
            self._assert_cmd_ok(_run_cmd(["git", "init"], repo_dir, env), "init")
            self._assert_cmd_ok(
                _run_cmd(
                    ["git", "checkout", "-b", "feature/test"],
                    repo_dir,
                    env,
                ),
                "checkout",
            )
            self._assert_cmd_ok(
                _run_cmd(
                    ["git", "config", "user.name", "Test User"], repo_dir, env
                ),
                "git config user.name",
            )
            self._assert_cmd_ok(
                _run_cmd(
                    ["git", "config", "user.email", "test@example.com"],
                    repo_dir,
                    env,
                ),
                "git config user.email",
            )
            self._assert_cmd_ok(
                _run_cmd(
                    ["git", "commit", "--allow-empty", "-m", "Bootstrap"],
                    repo_dir,
                    env,
                ),
                "bootstrap commit",
            )
            install_script = repo_dir / _GIT_HOOKS_DIR / "install_hooks.py"
            self._assert_cmd_ok(
                _run_cmd(
                    [
                        sys.executable,
                        str(install_script),
                        "--action",
                        "install",
                    ],
                    repo_dir,
                    env,
                ),
                "install hooks",
            )
            hooks_dir = repo_dir / ".git/hooks"
            self.assertTrue((hooks_dir / "pre-commit").exists())
            self.assertTrue((hooks_dir / "commit-msg").exists())
            fake_bin_dir = repo_dir / "fake_bin"
            fake_bin_dir.mkdir()
            fake_docker = fake_bin_dir / "docker"
            fake_docker.write_text(
                "#!/usr/bin/env bash\nexit 0\n",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env["PATH"] = f"{str(fake_bin_dir)}:{env['PATH']}"
            (repo_dir / "hello.py").write_text(
                "print('hello')\n",
                encoding="utf-8",
            )
            self._assert_cmd_ok(
                _run_cmd(["git", "add", "hello.py"], repo_dir, env),
                "git add",
            )
            self._assert_cmd_ok(
                _run_cmd(
                    ["git", "commit", "-m", "Initial commit"], repo_dir, env
                ),
                "git commit",
            )
            log_result = _run_cmd(
                ["git", "log", "-1", "--pretty=%B"], repo_dir, env
            )
            self._assert_cmd_ok(log_result, "git log")
            self.assertIn("Pre-commit checks:", log_result.stdout)
            self._assert_cmd_ok(
                _run_cmd(
                    [
                        sys.executable,
                        str(install_script),
                        "--action",
                        "remove",
                    ],
                    repo_dir,
                    env,
                ),
                "remove hooks",
            )
            self.assertFalse((hooks_dir / "pre-commit").exists())
            self.assertFalse((hooks_dir / "commit-msg").exists())
