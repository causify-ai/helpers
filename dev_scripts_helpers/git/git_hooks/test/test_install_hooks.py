import logging
import os

import pytest

import dev_scripts_helpers.git.git_hooks.utils as dsgghout  # pylint: disable=no-name-in-module
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hserver as hserver
import helpers.hsystem as hsystem
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

    def test_is_tmp_log_file1(self) -> None:
        """
        Test `_is_tmp_log_file()` on matching and non-matching file names.
        """
        # Prepare inputs and run test and check outputs.
        tmp_log_files = [
            "tmp.pytest.log",
            "tmp.log",
            "dir/tmp.build.log",
            # A plain `*.log` file (not prefixed with `tmp.`) also matches.
            "foo.log",
            "debug.log",
            # A `tmp.*` file without a `.log` extension also matches.
            "tmp.precommit_output.txt",
            "tmp.pytest.txt",
            "dir/tmp.cache.json",
        ]
        for file_name in tmp_log_files:
            self.assertTrue(dsgghout._is_tmp_log_file(file_name))
        other_files = ["log.tmp", "foo.py", "dir/data.csv"]
        for file_name in other_files:
            self.assertFalse(dsgghout._is_tmp_log_file(file_name))

    def test_check_tmp_log_files1(self) -> None:
        """
        Test `check_tmp_log_files()` passes when a `tmp.*.log` file is only
        deleted.
        """
        # Prepare inputs.
        abort_on_error = True
        file_statuses = [("D", "tmp.pytest.log"), ("M", "foo.py")]
        # Run test.
        dsgghout.check_tmp_log_files(abort_on_error, file_statuses)

    def test_check_tmp_log_files2(self) -> None:
        """
        Test `check_tmp_log_files()` aborts when a `tmp.*.log` file is added.
        """
        # Prepare inputs.
        abort_on_error = True
        file_statuses = [("A", "tmp.pytest.log")]
        # Run test and check output.
        with self.assertRaises(SystemExit):
            dsgghout.check_tmp_log_files(abort_on_error, file_statuses)

    def test_check_tmp_log_files3(self) -> None:
        """
        Test `check_tmp_log_files()` aborts when a `tmp.*.log` file is
        modified.
        """
        # Prepare inputs.
        abort_on_error = True
        file_statuses = [("M", "tmp.pytest.log")]
        # Run test and check output.
        with self.assertRaises(SystemExit):
            dsgghout.check_tmp_log_files(abort_on_error, file_statuses)

    def test_check_tmp_log_files4(self) -> None:
        """
        Test `check_tmp_log_files()` aborts when a plain `.log` file (not
        prefixed with `tmp.`) is added.
        """
        # Prepare inputs.
        abort_on_error = True
        file_statuses = [("A", "debug.log")]
        # Run test and check output.
        with self.assertRaises(SystemExit):
            dsgghout.check_tmp_log_files(abort_on_error, file_statuses)

    def test_check_tmp_log_files5(self) -> None:
        """
        Test `check_tmp_log_files()` aborts when a `tmp.*` file without a
        `.log` extension is added.
        """
        # Prepare inputs.
        abort_on_error = True
        file_statuses = [("A", "tmp.cache.json")]
        # Run test and check output.
        with self.assertRaises(SystemExit):
            dsgghout.check_tmp_log_files(abort_on_error, file_statuses)

    @pytest.mark.skipif(
        not hsystem.check_exec("ruff"), reason="`ruff` is not installed"
    )
    def test_check_ruff_format1(self) -> None:
        """
        Test `check_ruff_format()` aborts and reformats a badly formatted
        file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "bad_format.py")
        hio.to_file(file_name, "x=1\n")
        abort_on_error = True
        # Run test.
        with self.assertRaises(SystemExit):
            dsgghout.check_ruff_format(abort_on_error, [file_name])
        # Check outputs.
        actual = hio.from_file(file_name)
        self.assertIn("x = 1", actual)

    @pytest.mark.skipif(
        not hsystem.check_exec("ruff"), reason="`ruff` is not installed"
    )
    def test_check_ruff_format2(self) -> None:
        """
        Test `check_ruff_format()` passes for an already well-formatted
        file.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        file_name = os.path.join(scratch_dir, "good_format.py")
        hio.to_file(file_name, "x = 1\n")
        abort_on_error = True
        # Run test and check output.
        dsgghout.check_ruff_format(abort_on_error, [file_name])

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
