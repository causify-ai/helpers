import logging
import os
from typing import List, Tuple

import pandas as pd
import pytest

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import linters.amp_normalize_import as lamnoimp
import linters.utils as liutils

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test generating long-to-short import mappings
# #############################################################################


class TestChunkify(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test long imports separated by dots only.
        """
        long_import = "amp.core.backtest"
        actual = lamnoimp.LongToShortImportGenerator._chunkify(long_import)
        expected = ["amp", "core", "backtest"]
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test long imports separated by dots and underscores.
        """
        long_import = "linters.import_process_lib"
        actual = lamnoimp.LongToShortImportGenerator._chunkify(long_import)
        expected = ["linters", "import", "process", "lib"]
        self.assert_equal(str(actual), str(expected))


class TestComputeMaxChunkLengths(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test one chunk, given that length <= 8.
        """
        chunks = ["linter"]
        actual = lamnoimp.LongToShortImportGenerator._compute_max_chunk_lengths(
            chunks
        )
        expected = [6]
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test one chunk, given that length > 8.
        """
        chunks = ["precommit"]
        actual = lamnoimp.LongToShortImportGenerator._compute_max_chunk_lengths(
            chunks
        )
        expected = [8]
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test multiple chunks.
        """
        chunks = ["dataflow", "amp", "real", "time", "pipeline"]
        actual = lamnoimp.LongToShortImportGenerator._compute_max_chunk_lengths(
            chunks
        )
        expected = [1, 1, 2, 2, 2]
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test multiple chunks, given that last chunk's length < 3.
        """
        chunks = ["dataflow", "amp", "r"]
        actual = lamnoimp.LongToShortImportGenerator._compute_max_chunk_lengths(
            chunks
        )
        expected = [1, 3, 1]
        self.assert_equal(str(actual), str(expected))


class TestComputeShortImport(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test short import computation.
        """
        chunks = ["import", "check", "show", "imports"]
        chunk_lengths = [1, 2, 2, 3]
        actual = lamnoimp.LongToShortImportGenerator._compute_short_import(
            chunks, chunk_lengths
        )
        expected = "ichshimp"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test short import computation.
        """
        chunks = ["amp", "core", "features"]
        chunk_lengths = [1, 2, 3]
        actual = lamnoimp.LongToShortImportGenerator._compute_short_import(
            chunks, chunk_lengths
        )
        expected = "acofea"
        self.assert_equal(actual, expected)


class TestUseSpecialAbbreviations(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test "helpers" (as a dir name).
        """
        chunks = ["helpers", "dbg"]
        chunk_lenghts = [2, 3]
        actual = lamnoimp.LongToShortImportGenerator._use_special_abbreviations(
            chunks, chunk_lenghts
        )
        expected = (["h", "dbg"], [1, 3])
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test "dataflow".
        """
        chunks = ["amp", "dataflow", "utils"]
        chunk_lenghts = [1, 2, 3]
        actual = lamnoimp.LongToShortImportGenerator._use_special_abbreviations(
            chunks, chunk_lenghts
        )
        expected = (["amp", "dtf", "utils"], [1, 3, 3])
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test "im".
        """
        chunks = ["im", "check"]
        chunk_lenghts = [1, 3]
        actual = lamnoimp.LongToShortImportGenerator._use_special_abbreviations(
            chunks, chunk_lenghts
        )
        expected = (["im", "check"], [2, 3])
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test "helpers" (as not a dir name).
        """
        chunks = ["core", "pandas", "helpers"]
        chunk_lenghts = [1, 2, 3]
        actual = lamnoimp.LongToShortImportGenerator._use_special_abbreviations(
            chunks, chunk_lenghts
        )
        expected = (["core", "pandas", "helpers"], [1, 2, 3])
        self.assert_equal(str(actual), str(expected))


class TestSearchForUniqueShortImport(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test search given that short import is not in existing short imports.
        """
        chunks = ["amp", "dataflow", "utils"]
        chunk_lenghts = [1, 2, 3]
        short_imports = ["abc", "def"]
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._search_for_unique_short_import(
            chunks=chunks,
            chunk_lengths=chunk_lenghts,
            short_imports=set(short_imports),
        )
        expected = "adtfuti"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test search given that short import is in existing short imports.
        """
        chunks = ["amp", "dataflow", "utils"]
        chunk_lenghts = [1, 2, 3]
        short_imports = ["abc", "def", "adtfuti"]
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._search_for_unique_short_import(
            chunks=chunks,
            chunk_lengths=chunk_lenghts,
            short_imports=set(short_imports),
        )
        expected = "adtuti"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test search given that a unique short import cannot be generated.
        """
        chunks = ["amp", "core", "explore"]
        chunk_lenghts = [1, 1, 3]
        short_imports = ["acexp", "acex", "ace"]
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._search_for_unique_short_import(
            chunks=chunks,
            chunk_lengths=chunk_lenghts,
            short_imports=set(short_imports),
        )
        self.assertIsNone(actual)


class TestShortenImport(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test shorten import for long helper name (>7 chars).
        """
        long_import = "helpers.translate"
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._shorten_import(long_import, {})
        expected = "htransl"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test shorten import for short helper name (<7 chars).
        """
        long_import = "helpers.dbg"
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._shorten_import(long_import, {})
        expected = "hdbg"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test shorten import for helper name with underscore between words.
        """
        long_import = "helpers.system_interaction"
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._shorten_import(long_import, {})
        expected = "hsysinte"
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test shorten import for helper name with underscore at the end.
        """
        long_import = "helpers.io_"
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._shorten_import(long_import, {})
        expected = "hio"
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test shorten import for helper name with more than 2 chunks.
        """
        long_import = "helpers.unit_test_skeleton"
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._shorten_import(long_import, {})
        expected = "hunteske"
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test shorten import.
        """
        long_import = "linters.amp_isort"
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator._shorten_import(long_import, {})
        expected = "lampisor"
        self.assert_equal(actual, expected)


class TestFindCollisions(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test no collisions.
        """
        short_import_to_long = {
            "ahuti": ["amp.helpers.utils"],
            "ahsys": ["amp.helpers.system"],
        }
        collisions = lamnoimp.LongToShortImportGenerator._find_collisions(
            short_import_to_long
        )
        self.assertEqual(len(collisions), 0)

    def test2(self) -> None:
        """
        Test one collision.
        """
        short_import_to_long = {
            "ahuti": ["amp.helpers.utils", "amp.helpers.utilsss"],
            "ahsys": ["amp.helpers.system"],
        }
        collisions = lamnoimp.LongToShortImportGenerator._find_collisions(
            short_import_to_long
        )
        self.assertEqual(len(collisions), 1)


class TestGetLongImportFromFilePath(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that "py" letters inside a file name are not removed.
        """
        file_path = "linters/amp_mypy.py"
        actual = (
            lamnoimp.LongToShortImportGenerator.get_long_import_from_file_path(
                file_path
            )
        )
        expected = "linters.amp_mypy"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test that root dir is removed.
        """
        root_dir = hgit.get_client_root(False)
        file_path = os.path.join(root_dir, "core/test.py")
        actual = (
            lamnoimp.LongToShortImportGenerator.get_long_import_from_file_path(
                file_path
            )
        )
        expected = "core.test"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test that amp is removed.
        """
        file_path = os.path.join("amp", "core/test.py")
        actual = (
            lamnoimp.LongToShortImportGenerator.get_long_import_from_file_path(
                file_path
            )
        )
        expected = "core.test"
        self.assert_equal(actual, expected)

    def test4(self) -> None:
        """
        Test that both root dir and amp are removed.
        """
        root_dir = hgit.get_client_root(False)
        file_path = os.path.join(root_dir, "amp", "core/test.py")
        actual = (
            lamnoimp.LongToShortImportGenerator.get_long_import_from_file_path(
                file_path
            )
        )
        expected = "core.test"
        self.assert_equal(actual, expected)

    def test5(self) -> None:
        """
        Test that long import is constructed correctly.
        """
        file_path = "linters/check/test.py"
        actual = (
            lamnoimp.LongToShortImportGenerator.get_long_import_from_file_path(
                file_path
            )
        )
        expected = "linters.check.test"
        self.assert_equal(actual, expected)

    def test6(self) -> None:
        """
        Test that "amp" as a part of a file's name is not removed.
        """
        file_path = "amp_test_file.py"
        actual = (
            lamnoimp.LongToShortImportGenerator.get_long_import_from_file_path(
                file_path
            )
        )
        expected = "amp_test_file"
        self.assert_equal(actual, expected)


class TestShortenImportNames(hunitest.TestCase):
    def test_end_to_end1(self) -> None:
        """
        Test shorten import end to end.
        """
        py_files = [
            "amp/helpers/cache.py",
            "core/dataflow/nodes/sarimax_models.py",
            "core/dataflow/nodes/sklearn_models.py",
            "helpers/backtest.py",
            "linters/import_process_lib.py",
        ]
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator.shorten_import_names(py_files)
        expected = {
            "helpers.cache": "hcache",
            "core.dataflow.nodes.sarimax_models": "cdtfnosamo",
            "core.dataflow.nodes.sklearn_models": "cdtfnoskmo",
            "helpers.backtest": "hbackte",
            "linters.import_process_lib": "limprlib",
        }
        self.assert_equal(str(actual), str(expected))

    def test_end_to_end2(self) -> None:
        """
        Test shorten import end to end with problematic imports.

        Imports for `research/RH8E/RH8Ec_pipeline.py` and
        `research/RH8E/RH8Ed_pipeline.py` are skipped.
        """
        # List of filenames from the Lime repo, provided in DevToolsTask353.
        py_files = [
            "research/RH2E/utils.py",
            "research/RH2E/RH2Ea_pipeline.py",
            "research/RH2E/RH2Ec_configs.py",
            "research/RH2E/RH2Ed_configs.py",
            "research/RH2E/RH2Ee_configs.py",
            "research/RH2E/RH2Ef_configs.py",
            "research/RH2E/RH2Eg_configs.py",
            "research/RH2E/RH2Ea_configs.py",
            "research/RH2E/RH2Eb_pipeline.py",
            "research/RH2E/RH2Ec_pipeline.py",
            "research/RH2E/RH2Ed_pipeline.py",
            "research/RH2E/RH2Ee_pipeline.py",
            "research/RH2E/RH2Ef_pipeline.py",
            "research/RH2E/RH2Eg_pipeline.py",
            "research/RH1E/RH1E_configs.py",
            "research/RH1E/RH1E_pipeline.py",
            "research/RH1E/RH1Eb_configs.py",
            "research/RH1E/RH1Eb_pipeline.py",
            "research/RH4E/RH4Ea_configs.py",
            "research/RH4E/RH4Ea_pipeline.py",
            "research/RH8E/RH8Ea_configs.py",
            "research/RH8E/RH8Ea_pipeline.py",
            "research/RH8E/RH8Eb_configs.py",
            "research/RH8E/RH8Eb_pipeline.py",
            "research/RH8E/RH8Ec_configs.py",
            "research/RH8E/RH8Ec_pipeline.py",
            "research/RH8E/RH8Ed_pipeline.py",
            "research/RH8E/utils.py",
        ]
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        actual = short_imports_generator.shorten_import_names(py_files)
        expected = {
            "research.RH2E.utils": "rrh2util",
            "research.RH2E.RH2Ea_pipeline": "rrhrhpip",
            "research.RH2E.RH2Ec_configs": "rrhrhcon",
            "research.RH2E.RH2Ed_configs": "rrrhcon",
            "research.RH2E.RH2Ee_configs": "rrhrcon",
            "research.RH2E.RH2Ef_configs": "rrrcon",
            "research.RH2E.RH2Eg_configs": "rrhrhco",
            "research.RH2E.RH2Ea_configs": "rrrhco",
            "research.RH2E.RH2Eb_pipeline": "rrrhpip",
            "research.RH2E.RH2Ec_pipeline": "rrhrpip",
            "research.RH2E.RH2Ed_pipeline": "rrrpip",
            "research.RH2E.RH2Ee_pipeline": "rrhrhpi",
            "research.RH2E.RH2Ef_pipeline": "rrrhpi",
            "research.RH2E.RH2Eg_pipeline": "rrhrpi",
            "research.RH1E.RH1E_configs": "rrhrco",
            "research.RH1E.RH1E_pipeline": "rrrpi",
            "research.RH1E.RH1Eb_configs": "rrrco",
            "research.RH1E.RH1Eb_pipeline": "rrhrhp",
            "research.RH4E.RH4Ea_configs": "rrhrhc",
            "research.RH4E.RH4Ea_pipeline": "rrrhp",
            "research.RH8E.RH8Ea_configs": "rrrhc",
            "research.RH8E.RH8Ea_pipeline": "rrhrp",
            "research.RH8E.RH8Eb_configs": "rrhrc",
            "research.RH8E.RH8Eb_pipeline": "rrrp",
            "research.RH8E.RH8Ec_configs": "rrrc",
            "research.RH8E.utils": "rrh8util",
        }
        self.assert_equal(str(actual), str(expected))


# #############################################################################
# Test replacing short imports in code
# #############################################################################


class TestIsShortImportUsed(hunitest.TestCase):
    def test1(self) -> None:
        """
        Short import is used with the correct long import.
        """
        code = "import io as short_import"
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test2(self) -> None:
        """
        Short import is used in an assignment statement.
        """
        assignment_examples = [
            "short_import = 3",
            "short_import=other_var",
            "short_import = 'hi'",
        ]
        short_import = "short_import"
        long_import = "io"
        for code in assignment_examples:
            actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
                code, short_import, long_import
            )
            self.assertTrue(actual)

    def test3(self) -> None:
        """
        Partial short import is used.
        """
        code = "other_short_import=3"
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test4(self) -> None:
        """
        Short import is used inside the docstring.
        """
        code = '''
def test_docstring():
    """
    Test if import io as short_import can be found in the docstring.
    """
    return
'''
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test5(self) -> None:
        """
        Short import is used inside the docstring.
        """
        code = '''
def test_docstring():
    """Test if import io as short_import can be found in the docstring."""
    return
'''
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test6(self) -> None:
        """
        Short import is used inside the docstring.
        """
        code = """
def test_docstring():
    '''
    Test if import io as short_import can be found in the docstring.
    '''
    return
"""
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test7(self) -> None:
        """
        Short import is used inside the docstring.
        """
        code = """
def test_docstring():
    '''Test if import io as short_import can be found in the docstring.'''
    return
"""
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test8(self) -> None:
        """
        Short import is used in the comment.
        """
        code = "# import io as short_import"
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test9(self) -> None:
        """
        Short import is used as the content of the string.
        """
        code = 'string_import = "import io as short_import"'
        short_import = "short_import"
        long_import = "io"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertFalse(actual)

    def test10(self) -> None:
        """
        Short import is used with an incorrect long import.
        """
        code = "import io as short_import"
        short_import = "short_import"
        long_import = "helpers.hdbg"
        actual = lamnoimp.CodeImportNormalizer._is_short_import_used(
            code, short_import, long_import
        )
        self.assertTrue(actual)


class TestExtractExistingImportMappingsFromCode(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test an import without a short import.
        """
        code = "import test"
        expected: List[Tuple[str, str]] = []
        act = lamnoimp.CodeImportNormalizer._extract_existing_import_mappings_from_code(
            code=code
        )[0]
        self.assertEqual(act, expected)

    def test2(self) -> None:
        """
        Test an import with a short import.
        """
        code = "import test as te"
        expected = [("test", "te")]
        act = lamnoimp.CodeImportNormalizer._extract_existing_import_mappings_from_code(
            code=code
        )[0]
        self.assertEqual(act, expected)

    def test3(self) -> None:
        """
        Test single short imports with a dot in path.
        """
        code = "import test.sub as tsub"
        expected = [("test.sub", "tsub")]
        act = lamnoimp.CodeImportNormalizer._extract_existing_import_mappings_from_code(
            code=code
        )[0]
        self.assertEqual(act, expected)

    def test4(self) -> None:
        """
        Test multiple short imports are parsed correctly.
        """
        code = """
        import test as te
        import test.sub as tsub
        """
        expected = [("test", "te"), ("test.sub", "tsub")]
        act = lamnoimp.CodeImportNormalizer._extract_existing_import_mappings_from_code(
            code=code
        )[0]
        self.assertEqual(act, expected)

    def test5(self) -> None:
        """
        Test that exclusion list is respected.
        """
        code = """
        import IPython.utils.shimmodule as iush
        """
        expected: List[Tuple[str, str]] = []
        act = lamnoimp.CodeImportNormalizer._extract_existing_import_mappings_from_code(
            code=code
        )[0]
        self.assertEqual(act, expected)

    def test6(self) -> None:
        """
        Test that only unique occurrences are stored.
        """
        code = """
        import helpers.abc as abc

        def func_xyz(...):
            x = "import helpers.abc as xyz"
            return x

        y = "helpers.abc as xyz"
        """
        expected = [("helpers.abc", "abc"), ("helpers.abc", "xyz")]
        act = lamnoimp.CodeImportNormalizer._extract_existing_import_mappings_from_code(
            code=code
        )[0]
        self.assertEqual(act, expected)


class TestReplaceShortImportInCode(hunitest.TestCase):
    def test1(self) -> None:
        """
        No matches.
        """
        code = "import test as te"
        expected = code
        self._helper(code, expected)

    def test2(self) -> None:
        """
        Old short import is replaced in imports.
        """
        code = "import test as old_short_import"
        expected = "import test as new_short_import"
        self._helper(code, expected)

    def test3(self) -> None:
        """
        Old short import is replaced in function calls.
        """
        code = "old_short_import.hello()"
        expected = "new_short_import.hello()"
        self._helper(code, expected)

    def test4(self) -> None:
        """
        Check that indentation is preserved.
        """
        code = "    old_short_import.hello()"
        expected = "    new_short_import.hello()"
        self._helper(code, expected)

    def test5(self) -> None:
        """
        Check that test attributes are not updated.
        """
        code = "io.old_short_import.hello()"
        expected = "io.old_short_import.hello()"
        self._helper(code, expected)

    def test6(self) -> None:
        """
        Test that partial matches are not replaced.
        """
        code = "not_old_short_import.hello()"
        expected = "not_old_short_import.hello()"
        self._helper(code, expected)

    def test7(self) -> None:
        """
        When module name matches existing short import, it's not replaced.

        E.g., import helpers.hdbg as dbg
        """
        code = "import io.old_short_import as oauton"
        expected = "import io.old_short_import as oauton"
        self._helper(code, expected)

    def test8(self) -> None:
        """
        Do not replace short import in comments.
        """
        code = "old_short_import.hello() # But old_short_import is ok."
        expected = "new_short_import.hello() # But old_short_import is ok."
        self._helper(code, expected)

    def test9(self) -> None:
        """
        Test that short imports with the same name are not created.
        """
        code = "import old_short_import"
        expected = "import old_short_import"
        self._helper(code, expected)

    def test10(self) -> None:
        """
        Replacement does not change import path.
        """
        code = "import old_short_import.autonotebook as old_short_import"
        expected = "import old_short_import.autonotebook as new_short_import"
        self._helper(code, expected)

    def test11(self) -> None:
        """
        Test that replacement works.
        """
        code = "import hello_old_short_import as old_short_import"
        expected = "import hello_old_short_import as new_short_import"
        self._helper(code, expected)

    def test12(self) -> None:
        """
        Replacement does not change a file path.
        """
        code = "amp/helpers/old_short_import.py"
        expected = code
        self._helper(code, expected)

    def test13(self) -> None:
        """
        Do not replace short imports in comments.
        """
        code = "# import test as old_short_import"
        expected = code
        self._helper(code, expected)

    def test14(self) -> None:
        """
        Do not replace short imports in comments.
        """
        code = "# old_short_import.hello()"
        expected = code
        self._helper(code, expected)

    def test15(self) -> None:
        """
        Do not replace short imports in strings.
        """
        code = '"import test as old_short_import" is wrong'
        expected = code
        self._helper(code, expected)

    def test16(self) -> None:
        """
        Do not replace short imports in strings.
        """
        code = '"old_short_import.hello()" is wrong'
        expected = code
        self._helper(code, expected)

    def test17(self) -> None:
        """
        Do not replace short imports in docstrings.
        """
        code = '''
        def func():
            """
            Testing import test as old_short_import.
            """
            pass
        '''
        expected = code
        self._helper(code, expected)

    def test18(self) -> None:
        """
        Do not replace short imports in docstrings.
        """
        code = '''
        def func():
            """
            Testing old_short_import.hello().
            """
            pass
        '''
        expected = code
        self._helper(code, expected)

    def _helper(self, code: str, expected: str) -> None:
        """
        Test short import replacement.

        :param code: Python code
        :param expected: expected outcome of short import replacement
        """
        old_short_import = "old_short_import"
        new_short_import = "new_short_import"
        actual = lamnoimp.CodeImportNormalizer._replace_short_import_in_code(
            code,
            old_short_import,
            new_short_import,
        )
        self.assertEqual(expected, actual)


class TestReplaceShortImportsInFile(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test local package wrong short import.
        """
        input_code = "import helpers.hparser as parseeer"
        expected_code = "import helpers.hparser as hparser"
        self._check_import_normalization(input_code, expected_code)

    def test2(self) -> None:
        """
        Test local package correct short import.
        """
        input_code = "import helpers.hparser as hparser"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test3(self) -> None:
        """
        Test local package w/o "as".
        """
        input_code = "import helpers.hparser"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test4(self) -> None:
        """
        Test local package with underscores wrong short import.
        """
        input_code = "import linters.amp_normalize_import as norm"
        expected_code = "import linters.amp_normalize_import as lamnoimp"
        self._check_import_normalization(input_code, expected_code)

    def test5(self) -> None:
        """
        Test local package with "from".
        """
        input_code = "from linters import amp_normalize_import"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test6(self) -> None:
        """
        Test local package with spaces.
        """
        input_code = "    import linters.amp_normalize_import as norm"
        expected_code = "    import linters.amp_normalize_import as lamnoimp"
        self._check_import_normalization(input_code, expected_code)

    def test7(self) -> None:
        """
        Test native package w/o "as".
        """
        input_code = "import itertools"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test8(self) -> None:
        """
        Test native package wrong short import.
        """
        input_code = "import itertools as iter_wrong"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test9(self) -> None:
        """
        Test 3rd party package w/o "as".
        """
        input_code = "import pandas"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test10(self) -> None:
        """
        Test 3rd party package wrong short import.
        """
        input_code = "import pandas as panda"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test11(self) -> None:
        """
        Test 3rd party package correct short import.
        """
        input_code = "import pandas as pd"
        expected_code = input_code
        self._check_import_normalization(input_code, expected_code)

    def test12(self) -> None:
        """
        Test multiple cases.
        """
        input_code = """
        import intertools
        import datetime as dateti

        import matplotlib
        import numpy as nmp
        import pandas as pd

        import helpers.hcache as hcache
        import helpers.hparser as prs
        import linters.amp_normalize_import as lamnoimp
        import linters.amp_black as black
        import linters.amp_utils

        some code...
        """
        expected_code = """
        import intertools
        import datetime as dateti

        import matplotlib
        import numpy as nmp
        import pandas as pd

        import helpers.hcache as hcache
        import helpers.hparser as hparser
        import linters.amp_normalize_import as lamnoimp
        import linters.amp_black as lampblac
        import linters.amp_utils

        some code...
        """
        self._check_import_normalization(input_code, expected_code)

    def _check_import_normalization(self, code: str, expected_code: str) -> None:
        """
        Check import normalization in a file.

        :param code: code that is initially contained in a file
        :param expected_code: code that is expected to be after import normalization
        :return:
        """
        # Get the long-to-short import mappings for a "root_dir".
        root_dir = hgit.get_client_root(True)
        file_names = liutils.get_python_files_to_lint(root_dir)
        short_import_generator = lamnoimp.LongToShortImportGenerator()
        long_to_short_import = short_import_generator.shorten_import_names(
            file_names
        )
        # Save the code to the file.
        scratch_dir = self.get_scratch_space()
        file = os.path.join(scratch_dir, "test.txt")
        hio.to_file(file, code)
        # Update the import statements in the file.
        import_normalizer = lamnoimp.CodeImportNormalizer()
        import_normalizer.replace_short_imports_in_file(
            file, long_to_short_import
        )
        updated_code = hio.from_file(file)
        # Check that import normalization went as expected.
        self.assert_equal(updated_code, expected_code)


# #############################################################################
# Test updating import docstrings
# #############################################################################


class TestInsertDocstringIfNeeded(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the import docstring is not added.

        The code starts with the docstring with import line. The case
        with the shebang.
        """
        input_code = '''#!/usr/bin/env python
        """
        Import as:

        import linters.amp_normalize_import as lamnoimp
        """
        '''
        # Docstring is not added since file already contains import docstring.
        expected_code = input_code
        # Check the results.
        self._helper(input_code, expected_code)

    def test2(self) -> None:
        """
        Test that the import docstring is added to the file without the import
        docstring.

        The case w/o the shebang.
        """
        # Remove new-line with "\".
        input_code = """\
        import argparse
        import logging
        import re
        from typing import List
        """
        # Empty docstring line is added at the beginning of the file.
        # Remove new-line with "\".
        expected_code = '''\
        """
        """

        import argparse
        import logging
        import re
        from typing import List
        '''
        # Check the results.
        self._helper(input_code, expected_code)

    def test3(self) -> None:
        """
        Test that the import docstring is not added.

        The code starts with the docstring but without the import line.
        The case w/o the shebang.
        """
        # Remove new-line with "\".
        input_code = '''\
        """
        Reformat and lint python and ipynb files.

        E.g.,
        # Lint all modified files in git client.
        """
        '''
        # Docstring is not added since file already starts with the docstring.
        expected_code = input_code
        # Check the results.
        self._helper(input_code, expected_code)

    def test4(self) -> None:
        """
        Test that the import docstring is not added.

        The code starts with the docstring with import line. The case
        w/o the shebang.
        """
        # Remove new-line with "\".
        input_code = '''\
        """
        Import as:

        import linters.amp_normalize_import as lamnoimp
        """
        '''
        # Docstring is not added since file already contains import docstring.
        expected_code = input_code
        # Compare the output.
        self._helper(input_code, expected_code)

    def _helper(
        self,
        code_snippet: str,
        expected_outcome: str,
    ) -> None:
        """
        Test empty docstring insertion.

        :param code_snippet: the code to process
        :param expected_outcome: the code with an empty inserted docstring
        """
        # Remove indentation.
        code = code_snippet.replace("    ", "")
        expected_outcome = expected_outcome.replace("    ", "")
        # Insert an empty docstring if needed.
        import_line_generator = lamnoimp.ImportDocstringGenerator()
        actual_outcome = import_line_generator._insert_docstring_if_needed(code)
        # Check the results.
        self.assert_equal(actual_outcome, expected_outcome)


class TestCleanDocstringFromImport(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test no import line in the docstring text.
        """
        input_docstring = """
        File description...
        """
        expected_docstring = """
        File description...
        """
        self._helper(input_docstring, expected_docstring)

    def test2(self) -> None:
        """
        Test that the 1st part of the import line is removed.
        """
        input_docstring = """
        File description...

        Import as:
        """
        expected_docstring = """
        File description...
        """
        self._helper(input_docstring, expected_docstring)

    def test3(self) -> None:
        """
        Test that the import line is removed.
        """
        input_docstring = """
        File description...

        Import as:

        import test.check as tcheck
        """
        expected_docstring = """
        File description...
        """
        self._helper(input_docstring, expected_docstring)

    def _helper(
        self,
        docstring_text: str,
        expected_outcome: str,
    ) -> None:
        """
        Test cleaning the import docstring.

        :param docstring_text: the docstring text to process
        :param expected_outcome: the docstring w/o import line
        """
        # Remove indentation.
        docstring = docstring_text.replace("    ", "")
        expected_outcome = expected_outcome.replace("    ", "")
        # Remove import line from a docstring text.
        actual_outcome = (
            lamnoimp.ImportDocstringGenerator._remove_import_from_docstring_text(
                docstring
            )
        )
        # Check the results.
        self.assert_equal(actual_outcome, expected_outcome)


class TestProcessContent(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the import line is added.

        The case w/o the docstring.
        """
        # Remove the new-line with "\".
        input_code = """\
        import argparse
        import itertools
        from typing import List
        """
        # Remove the new-line with "\".
        expected_code = '''\
        """
        Import as:

        import linters.amp_normalize_import as lamnoimp
        """

        import argparse
        import itertools
        from typing import List
        '''
        long_import = "linters.amp_normalize_import"
        short_import = "lamnoimp"
        # Check the results.
        self._helper(input_code, long_import, short_import, expected_code)

    def test2(self) -> None:
        """
        Test that the import line is added.

        The case with the docstring but w/o the import line.
        """
        # Remove the new-line with "\".
        input_code = '''\
        """
        Text...
        """

        import argparse
        import itertools
        from typing import List
        '''
        # Remove the new-line with "\".
        expected_code = '''\
        """
        Text...

        Import as:

        import linters.amp_normalize_import as lamnoimp
        """

        import argparse
        import itertools
        from typing import List
        '''
        long_import = "linters.amp_normalize_import"
        short_import = "lamnoimp"
        # Check the results.
        self._helper(input_code, long_import, short_import, expected_code)

    def test3(self) -> None:
        """
        Test that the import line is updated.

        The case with import line but wrong short import.
        """
        # Remove the new-line with "\".
        input_code = '''\
        """
        Text...

        Import as:

        import linters.amp_normalize_import as linter
        """

        import argparse
        import itertools
        from typing import List
        '''
        # Remove the new-line with "\".
        expected_code = '''\
        """
        Text...

        Import as:

        import linters.amp_normalize_import as lamnoimp
        """

        import argparse
        import itertools
        from typing import List
        '''
        long_import = "linters.amp_normalize_import"
        short_import = "lamnoimp"
        # Check the results.
        self._helper(input_code, long_import, short_import, expected_code)

    def test4(self) -> None:
        """
        Test that the import line is not updated.

        The case with the correct import line.
        """
        # Remove the new-line with "\".
        input_code = '''\
        """
        Text...

        Import as:

        import linters.amp_normalize_import as lamnoimp
        """

        import argparse
        import itertools
        from typing import List
        '''
        expected_code = input_code
        long_import = "linters.amp_normalize_import"
        short_import = "lamnoimp"
        # Check the results.
        self._helper(input_code, long_import, short_import, expected_code)

    def test5(self) -> None:
        """
        Test that the import line is not updated.

        Case 1 with the shebang.
        """
        # Remove the new-line with "\".
        input_code = '''\
        #!/usr/bin/env python

        """
        Text...
        """

        import argparse
        import itertools
        from typing import List
        '''
        expected_code = input_code
        long_import = "linters.amp_normalize_import"
        short_import = "lamnoimp"
        # Check the results.
        self._helper(input_code, long_import, short_import, expected_code)

    def test6(self) -> None:
        """
        Test that the import line is not updated.

        Case 2 with the shebang.
        """
        # Remove the new-line with "\".
        input_code = """\
        #!/usr/bin/env python

        import argparse
        import itertools
        from typing import List
        """
        expected_code = input_code
        long_import = "linters.amp_normalize_import"
        short_import = "lamnoimp"
        # Check the results.
        self._helper(input_code, long_import, short_import, expected_code)

    def _helper(
        self,
        code_snippet: str,
        long_import: str,
        short_import: str,
        expected_code: str,
    ) -> None:
        """
        Test import docstring processing.

        :param code_snippet: the snippet of the code
        :param long_import: full import name, e.g., "helpers.dbg"
        :param short_import: short version of import, e.g. "hdbg"
        :param expected_code: code with the updated import line
        """
        # Remove indentation.
        code = code_snippet.replace("    ", "")
        expected_outcome = expected_code.replace("    ", "")
        # Update the import line.
        import_line_generator = lamnoimp.ImportDocstringGenerator()
        actual_outcome = import_line_generator._process_code(
            code,
            long_import,
            short_import,
        )
        # Check the results.
        self.assert_equal(actual_outcome, expected_outcome)


# #############################################################################
# Test import normalization end-to-end
# #############################################################################


class TestEndToEnd(hunitest.TestCase):
    def test(self) -> None:
        """
        Test that import normalization works end-to-end.

        Note: import docstring is not generated for test files.
        """
        code_to_check = """
        import itertools as itools
        import os
        from typing import List, Set

        import bs4
        import numpy as npy
        import pandas as pd

        import helpers.hgit as hgit
        import helpers.hs3
        import helpers.hsql as sqllll
        import helpers.hsystem as systemi

        wrong_module_usage = sqllll.test()
        correct_module_usage = hgit.get_client_root()
        """
        # Remove indentation.
        code_to_check = hprint.dedent(code_to_check)
        # Init action.
        root_dir = hgit.get_client_root(super_module=False)
        py_files = liutils.get_python_files_to_lint(root_dir)
        action = lamnoimp._NormalizeImports(py_files)
        # Save the temp file with the code.
        scratch_dir = self.get_scratch_space()
        file_path = os.path.join(scratch_dir, "test.py")
        hio.to_file(file_path, code_to_check)
        # Run action.
        action._execute(file_path, pedantic=0)
        actual_code = hio.from_file(file_path)
        # Compare with the golden outcome.
        self.check_string(actual_code, purify_text=True)


class TestEndToEndShortImports(hunitest.TestCase):
    """
    End-to-end test to check how short imports are modified.
    """

    @pytest.mark.skip(reason="Run manually")
    def test_collect_file_names(self) -> None:
        """
        Collect all the Python file names in a root dir and save them in a file
        for further processing.

        We want to refresh this file manually so that it's stable and
        can be used in a test.
        """
        root_dir = hgit.get_client_root(super_module=True)
        file_names = liutils.get_python_files_to_lint(root_dir)
        # Save list of file names as JSON.
        dst_file_path = self._get_file_path()
        hio.to_json(dst_file_path, file_names)

    def test_normalize_imports(self) -> None:
        """
        Freeze the short imports corresponding to the files computed in
        `test_collect_file_names()`.
        """
        # Extract amp file names from the file.
        dst_file_path = self._get_file_path()
        file_names = hio.from_json(dst_file_path)
        # Generate short imports dict.
        short_imports_generator = lamnoimp.LongToShortImportGenerator()
        short_import_names = short_imports_generator.shorten_import_names(
            file_names
        )
        # Convert dict to JSON string and compare it with golden outcome.
        actual = pd.Series(short_import_names).to_json(indent=4)
        self.check_string(actual, purify_text=True)

    def _get_file_path(self) -> str:
        """
        Get path to the file with Python file names for the test.
        """
        dst_dir_name = self.get_input_dir(use_only_test_class=True)
        dst_file_path = os.path.join(dst_dir_name, "python_file_names.json")
        return dst_file_path
