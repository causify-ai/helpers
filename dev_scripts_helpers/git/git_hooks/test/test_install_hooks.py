import logging

import pytest

import dev_scripts_helpers.git.git_hooks.utils as dsgghout  # pylint: disable=no-name-in-module
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


@pytest.mark.skipif(
    hserver.is_inside_ci(), reason="CI is not set up for committing code in GH"
)
class Test_git_hooks_utils1(hunitest.TestCase):
    def test_check_master1(self) -> None:
        abort_on_error = False
        dsgghout.check_master(abort_on_error)

    @pytest.mark.skipif(
        hserver.is_inside_docker(),
        reason="There are no Git credentials inside Docker",
    )
    def test_check_author1(self) -> None:
        abort_on_error = False
        dsgghout.check_author(abort_on_error)

    def test_check_file_size1(self) -> None:
        abort_on_error = False
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


class Test_install_hooks1(hunitest.TestCase):
    def test_install1(self) -> None:
        """
        Install action links both git hook phases into the target hooks dir.
        """
        import unittest.mock as umock
        import dev_scripts_helpers.git.git_hooks.install_hooks as dsgghinho

        commands = []

        def _system(cmd: str, *args, **kwargs):
            commands.append(cmd)
            return 0

        with umock.patch("sys.argv", ["install_hooks.py", "--action", "install"]), \
            umock.patch("helpers.hgit.find_helpers_root", return_value="/repo"), \
            umock.patch("helpers.hdbg.dassert_dir_exists"), \
            umock.patch("helpers.hdbg.dassert_file_exists"), \
            umock.patch("helpers.hsystem.system_to_one_line", return_value=(0, "/repo/.git/hooks")), \
            umock.patch("helpers.hsystem.system", side_effect=_system):
            dsgghinho._main()
        expected = [
            "ln -sf /repo/dev_scripts_helpers/git/git_hooks/pre-commit.py /repo/.git/hooks/pre-commit",
            "chmod +x /repo/dev_scripts_helpers/git/git_hooks/pre-commit.py",
            "chmod +x /repo/.git/hooks/pre-commit",
            "ln -sf /repo/dev_scripts_helpers/git/git_hooks/commit-msg.py /repo/.git/hooks/commit-msg",
            "chmod +x /repo/dev_scripts_helpers/git/git_hooks/commit-msg.py",
            "chmod +x /repo/.git/hooks/commit-msg",
        ]
        self.assertEqual(commands, expected)

    def test_remove1(self) -> None:
        """
        Remove action unlinks installed hook files when they exist.
        """
        import unittest.mock as umock
        import dev_scripts_helpers.git.git_hooks.install_hooks as dsgghinho

        commands = []

        def _system(cmd: str, *args, **kwargs):
            commands.append(cmd)
            return 0

        with umock.patch("sys.argv", ["install_hooks.py", "--action", "remove"]), \
            umock.patch("helpers.hgit.find_helpers_root", return_value="/repo"), \
            umock.patch("helpers.hdbg.dassert_dir_exists"), \
            umock.patch("helpers.hsystem.system_to_one_line", return_value=(0, "/repo/.git/hooks")), \
            umock.patch("os.path.exists", return_value=True), \
            umock.patch("helpers.hsystem.system", side_effect=_system):
            dsgghinho._main()
        expected = [
            "unlink /repo/.git/hooks/pre-commit",
            "unlink /repo/.git/hooks/commit-msg",
        ]
        self.assertEqual(commands, expected)
