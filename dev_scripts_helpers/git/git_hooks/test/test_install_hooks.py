import logging

import pytest
from unittest.mock import MagicMock, patch

import dev_scripts_helpers.git.git_hooks.utils as dsgghout  # pylint: disable=no-name-in-module
import dev_scripts_helpers.git.git_hooks.install_hooks as dsgghinho
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="CI is not set up for committing code in GH"
)
class Test_git_hooks_utils1(hunitest.TestCase):
    def test_check_master1(self) -> None:
        abort_on_error = False
        with patch(
            "dev_scripts_helpers.git.git_hooks.utils._system_to_string",
            return_value=(0, "feature-branch"),
        ):
            dsgghout.check_master(abort_on_error)

    @pytest.mark.skipif(
        hserver.is_inside_docker(),
        reason="There are no Git credentials inside Docker",
    )
    def test_check_author1(self) -> None:
        abort_on_error = False
        # Mock git config calls.
        with patch(
            "dev_scripts_helpers.git.git_hooks.utils._system_to_string",
            side_effect=[
                (0, "testuser"),
                (0, "origin"),
                (0, "test@gmail.com"),
                (0, "origin"),
            ],
        ):
            dsgghout.check_author(abort_on_error)

    def test_check_file_size1(self) -> None:
        abort_on_error = False
        with patch(
            "dev_scripts_helpers.git.git_hooks.utils._get_files",
            return_value=["foo.py"],
        ), patch("os.path.exists", return_value=True), patch("os.stat") as mock_stat:
            mock_stat.return_value.st_size = 100
            dsgghout.check_file_size(abort_on_error)

    def test_caesar1(self) -> None:
        txt = """
        1 2 3 4 5 6 7 8 9 0
        This pangram contains four As, one B, two Cs, one D, thirty Es, six Fs, five
        Gs, seven Hs, eleven Is, one J, one K, two Ls, two Ms, eighteen Ns, fifteen
        Os, two Ps, one Q, five Rs, twenty-seven Ss, eighteen Ts, two Us, seven Vs,
        eight Ws, two Xs, three Ys, & one Z.
        """
        txt = hprint.dedent(txt)
        step = 3
        transformed_txt = dsgghout.caesar(txt, step)
        txt2 = dsgghout.caesar(transformed_txt, -step)
        self.assert_equal(txt, txt2)

    def test_regex1(self) -> None:
        words = "ln Ln LN lnpk LNPK sptl sltvuhkl slt jyfwav"
        for word in words.split():
            self._helper(word, False, True)
            self._helper("# " + word, False, True)
            self._helper(" " + word, False, True)
            self._helper(word + " ", False, True)
            self._helper(word + "a", False, False)
            self._helper(word + "_hello", False, True)
            self._helper("is_" + word, False, True)

    def test_regex2(self) -> None:
        decaesarify = False
        self._helper("Olssv LN", decaesarify, True)
        self._helper("LN go", decaesarify, True)
        self._helper("LN_o", decaesarify, True)
        self._helper("_LN", decaesarify, True)
        self._helper("is_LN go", decaesarify, True)
        self._helper("Olssv_TLN", decaesarify, False)
        self._helper("Olssv_LN_Hello", decaesarify, True)
        self._helper("Olssv_LNHello", decaesarify, False)
        #
        self._helper("LNPK", decaesarify, True)
        self._helper("This is LNPK or is not", decaesarify, True)
        self._helper("This is _LNPK or is not", decaesarify, True)
        self._helper("LNPKhello", decaesarify, False)

    def test_regex3(self) -> None:
        # We can't have any found word, otherwise the pre-commit check will
        # trigger.
        decaesarify = True
        self._helper("Ego", decaesarify, False)
        self._helper("_eggo", decaesarify, False)
        self._helper("NOTIFY_JUPYTER_TOKEN", decaesarify, False)

    def test_check_words_in_text1(self) -> None:
        txt = """
        Olssv LN
        Olssv_TLN
        Olssv_LN_Hello
        Olssv LN
        """
        txt = hprint.dedent(txt)
        file_name = "foobar.txt"
        lines = txt.split("\n")
        actual = "\n".join(
            dsgghout._check_words_in_text(file_name, lines, decaesarify=False)
        )
        # Check.
        expected = r"""
        foobar.txt:1: Found 'SU'
        foobar.txt:3: Found 'SU'
        foobar.txt:4: Found 'SU'"""
        expected = hprint.dedent(expected)
        self.assert_equal(actual, expected)

    def _helper(self, txt: str, decaesarify: bool, expected: bool) -> None:
        _LOG.debug(hprint.to_str("txt decaesarify expected"))
        regex = dsgghout._get_regex(decaesarify)
        m = regex.search(txt)
        _LOG.debug("  -> m=%s", bool(m))
        if m:
            val = m.group(1)
            _LOG.debug("  -> val=%s", val)
        self.assertEqual(bool(m), expected)

    def test_check_python_compile1(self) -> None:
        """
        Verify check_python_compile runs without error on dummy files.
        """
        # We mock _get_files to return this file itself, which should compile.
        with patch(
            "dev_scripts_helpers.git.git_hooks.utils._get_files"
        ) as mock_get_files:
            mock_get_files.return_value = [__file__]
            abort_on_error = False
            dsgghout.check_python_compile(abort_on_error)


class Test_install_hooks(hunitest.TestCase):
    def test_install_1(self) -> None:
        """
        Test the 'install' action.
        """
        # Mocking arguments
        args = MagicMock()
        args.action = "install"
        args.log_level = "INFO"

        with patch("argparse.ArgumentParser.parse_args", return_value=args), patch(
            "helpers.hgit.find_helpers_root", return_value="/tmp/helpers"
        ), patch(
            "helpers.hsystem.system_to_one_line", return_value=(0, "/tmp/.git/hooks")
        ), patch(
            "helpers.hdbg.dassert_dir_exists"
        ), patch(
            "helpers.hdbg.dassert_file_exists"
        ), patch(
            "helpers.hsystem.system"
        ) as mock_system:

            dsgghinho._main()

            # verify chmod and ln commands were called
            # We expect calls for pre-commit, commit-msg, etc.
            self.assertTrue(mock_system.called)
            # Check for at least one expected call
            cmd_args = [c[0][0] for c in mock_system.call_args_list]
            self.assertTrue(any("ln -sf" in cmd for cmd in cmd_args))
            self.assertTrue(any("chmod +x" in cmd for cmd in cmd_args))

    def test_remove_1(self) -> None:
        """
        Test the 'remove' action.
        """
        args = MagicMock()
        args.action = "remove"
        args.log_level = "INFO"

        with patch("argparse.ArgumentParser.parse_args", return_value=args), patch(
            "helpers.hgit.find_helpers_root", return_value="/tmp/helpers"
        ), patch(
            "helpers.hsystem.system_to_one_line", return_value=(0, "/tmp/.git/hooks")
        ), patch(
            "helpers.hdbg.dassert_dir_exists"
        ), patch(
            "os.path.exists", return_value=True
        ), patch(
            "helpers.hsystem.system"
        ) as mock_system:

            dsgghinho._main()

            # verify unlink commands were called
            self.assertTrue(mock_system.called)
            cmd_args = [c[0][0] for c in mock_system.call_args_list]
            self.assertTrue(any("unlink" in cmd for cmd in cmd_args))
