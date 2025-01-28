#!/usr/bin/env python
"""
Modify Python code to:

- Use the canonical import docstring
- Use canonical short imports

> amp_normalize_import.py sample_file1.py sample_file2.py

Import as:

import linters.amp_normalize_import as lamnoimp
"""

import argparse
import itertools
import logging
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hstring as hstring
import linters.action as liaction
import linters.utils as liutils

_LOG = logging.getLogger(__name__)

LongImportToShort = Dict[str, str]
ShortImportToLong = Dict[str, List[str]]

Chunks = List[str]
ChunkLengths = List[int]

Collisions = Dict[str, List[str]]

# Given the Python files in the repo
# - Find the files that can be imported (i.e., the ones that are not executables)
# - Find the Python imports (`import helpers.debug`)
# - Convert the file paths into Python imports

# Map long imports -> short imports.
# E.g., maps `long_imports` to `shimp` in statements like:
# ```
# import long_import as shimp
# ```

# TODO(Grisha): use the custom short imports in #215, #216.
_CUSTOM_SHORT_IMPORTS = {
    "helpers.csv_helpers": "hcsv",
    "helpers.datetime_": "hdateti",
    "helpers.git": "hgit",
    "helpers.io_": "hio",
    "helpers.joblib_helpers": "hjoblib",
    "helpers.list": "hlist",
    "helpers.numba_": "hnumba",
    "helpers.open": "hopen",
    "helpers.pickle_": "hpickle",
    "helpers.printing": "hprint",
    "helpers.pytest_": "hpytest",
    "helpers.s3": "hs3",
    "helpers.traceback_helper": "htraceb",
    "helpers.warnings_helpers": "hwarnin",
    # "matplotlib": "mpl",
    # "matplotlib.pyplot": "plt",
    # "numpy": "np",
    # "pandas": "pd",
    # "seaborn": "sns",
    # "statsmodels.api": "sm",
    # "core.config_builders": "ccbuild",
}

# #############################################################################
# Generate long-to-short import mappings
# #############################################################################


class LongToShortImportGenerator:
    """
    Generate long-to-short import mappings from Python files.
    """

    def __init__(self, use_special_abbreviations: bool = True) -> None:
        """
        Init the long-to-short import generator.

        :param use_special_abbreviations: whether to override certain import
            chunks or not
        :return:
        """
        self.use_special_abbreviations = use_special_abbreviations

    @staticmethod
    def get_long_import_from_file_path(file_path: str) -> str:
        """
        Get long import name from a file path.

        E.g., "amp/helpers/git.py" -> "helpers.git".

        :param file_path: path to a file
        :return: file's long import name
        """
        if file_path.startswith(liutils.ROOT_DIR):
            # Remove the root dir from the file path, e.g., "/app/amp/helpers/git.py"
            # -> "amp/helpers/git.py". Since root dir is not used in an import name.
            file_path = os.path.relpath(file_path, liutils.ROOT_DIR)
        # Remove submodule dirs from the file_path, since they are not specified in import
        # statements, e.g., "helpers_root/helpers/git.py" -> "helpers/git.py".
        submodule_dirs = ["amp/", "helpers_root/"]
        for dir_ in submodule_dirs:
            if file_path.startswith(dir_):
                file_path = os.path.relpath(file_path, dir_)
        # Remove a Python file's extension, e.g. "helpers/git.py" ->
        # "helpers/git".
        file_path_wo_ext = re.sub(r".py$", "", file_path)
        # Replace the "/" with the "." to convert a file path to a
        # long import. E.g., "helpers/git" -> "helpers.git".
        long_import = file_path_wo_ext.replace("/", ".")
        return long_import

    def shorten_import_names(self, py_files: List[str]) -> LongImportToShort:
        """
        Shorten the imports for provided filenames.

        If it is impossible to create a unique short import for a filename,
        skip it.

        :param py_files: list of Python files' paths
        :return: long import to short import mappings, e.g.
            `{"long_import1": "short_import1", "long_import2": "short_import1"}`
        """
        # Report the Python files.
        _LOG.debug("Python files=\n%s", "\n".join(py_files))
        # Get long imports from file paths.
        long_imports = [
            self.get_long_import_from_file_path(file) for file in py_files
        ]
        # Verify that there are no duplicated Python files in subdirs.
        # `get_long_import_from_file_path()` removes some subdirs from long
        # imports (e.g., `/app/amp/core/finance.py` -> `core.finance`) but
        # there may be duplicates in different subdirs of such type.
        hdbg.dassert_no_duplicates(
            long_imports, "Remove duplicated Python files before linting."
        )
        # Build the mapping shortening the imports.
        long_import_to_short: LongImportToShort = {}
        for long_import in long_imports:
            _LOG.debug("# Processing '%s'", long_import)
            # E.g., "im.kitbot.data.load.kitbot_s3_data_loader" ->
            # "imkdalokis3datloa".
            short_import = self._shorten_import(long_import, long_import_to_short)
            if short_import is not None:
                hdbg.dassert_ne(short_import, "")
                # Store the long import to short import mapping.
                long_import_to_short[long_import] = short_import
                _LOG.debug("%s -> %s", long_import, short_import)
        _LOG.debug(
            "long_import_to_short=\n%s",
            self._print_long_import_to_short(long_import_to_short),
        )
        # Reverse the mapping.
        short_import_to_long = self._build_reverse_mapping(long_import_to_short)
        # Make sure that all short imports are unique.
        collisions = self._find_collisions(short_import_to_long)
        hdbg.dassert_eq(0, len(collisions))
        return long_import_to_short

    @staticmethod
    def _find_collisions(short_import_to_long: ShortImportToLong) -> Collisions:
        """
        Find the long imports that have the same short name.

        :param short_import_to_long: short import to long import mappings, e.g.
            `{"sh_i1": ["l_i1", "l_i2"], "sh_i2": ["l_i3"]}`
        :return: short imports that have multiple long import mappings, e.g.
            `{"sh_i1": ["l_i1", "l_i2"]}`
        """
        collisions: Collisions = {}
        for value, keys in short_import_to_long.items():
            if len(keys) > 1:
                collisions[value] = keys
        _LOG.debug("Num collisions=%s", len(collisions))
        if collisions:
            _LOG.debug("collisions=\n%s", "\n".join(collisions))
        return collisions

    @staticmethod
    def _use_special_abbreviations(
        chunks: Chunks, chunk_lengths: ChunkLengths
    ) -> Tuple[Chunks, ChunkLengths]:
        """
        Override certain chunks and their lengths using a predefined
        dictionary.

        :param chunks: long import chunks, e.g. `["dataflow", "amp", "real",
            "time", "pipeline"]`
        :param chunk_lengths: max chunk lengths, e.g. `[1, 1, 2, 3, 3]`
        :return: chunks and their lengths updated from dictionary
        """
        hdbg.dassert_eq(len(chunks), len(chunk_lengths))
        #
        short_dir_mapping = {
            "im": "im",
            "helpers": "h",
            "dataflow": "dtf",
        }
        chunks_tmp = []
        chunk_lengths_tmp = []
        for i, (chunk, chunk_length) in enumerate(zip(chunks, chunk_lengths)):
            if chunk in short_dir_mapping:
                # Update the chunk and its length with the content of the dictionary.
                if chunk != "helpers" or i == 0:
                    # Override `helpers` only if it's a dir name (`helpers` as a dir
                    # name comes first in the `chunks` list).
                    chunk = short_dir_mapping[chunk]
                    chunk_length = len(chunk)
            # Accumulate.
            chunks_tmp.append(chunk)
            chunk_lengths_tmp.append(chunk_length)
        return chunks_tmp, chunk_lengths_tmp

    @staticmethod
    def _compute_short_import(chunks: Chunks, chunk_lengths: ChunkLengths) -> str:
        """
        Compute the short import from the chunks and the desired length for
        each chunk.

        :param chunks: long import chunks, e.g. `["dataflow", "amp", "real",
            "time", "pipeline"]`
        :param chunk_lengths: max chunk lengths, e.g. `[1, 1, 2, 3, 3]`
        :return: short import, e.g. "daretimpip"
        """
        chunks_tmp = []
        hdbg.dassert_eq(len(chunks), len(chunk_lengths))
        for chunk, length in zip(chunks, chunk_lengths):
            hdbg.dassert_lte(length, len(chunk))
            chunks_tmp.append(chunk[:length])
        return "".join(chunks_tmp)

    # TODO(*): Consider moving `max_import_len` and `max_chunk_len` to the class `__init__()`.
    @staticmethod
    def _compute_max_chunk_lengths(
        chunks: Chunks,
        max_import_len: int = 8,
        max_chunk_len: int = 3,
    ) -> ChunkLengths:
        """
        Compute the maximum length allowed for each chunk.

        The length is given by:
            - Linear interpolation between 1 and `max_chunk_length` in
              `len(chunks)` steps
            - Normalization of interpolated values so their sum equals
              `max_import_length`
            - Rounding values to the closest integer not less than 1
            - Due to the rounding the actual maximum import length could be less
              than or greater than `max_import_len`

        :param chunks: long import chunks, e.g. `["dataflow", "amp", "real",
            "time", "pipeline"]`
        :param max_import_len: desired max short import length
        :param max_chunk_len: max length of a chunk that may be used for import
        :return: max chunk lengths, e.g. `[1, 1, 2, 3, 3]`
        """
        # Compute the actual chunk lengths.
        chunk_lengths = [len(chunk) for chunk in chunks]
        # Compute the number of chunks.
        chunk_num = len(chunks)
        hdbg.dassert_lte(1, chunk_num)
        _LOG.debug("chunk_lengths=%s", str(chunk_lengths))
        if chunk_num == 1:
            # For one chunk, the length is up to `max_import_len`.
            length = min(max_import_len, len(chunks[0]))
            return [length]
        # TODO(*): Add a behavior for long imports with 2 chunks #262.
        # Create a Series with a linear interpolation between 1 and
        # `max_chunk_len` in `len(chunks)` steps.
        relative_chunk_lengths = pd.Series(
            [1] + [np.nan] * (chunk_num - 2) + [max_chunk_len]
        ).interpolate()
        # Normalize relative max chunk lengths so their sum equals
        # `max_import_len` and round them to the closest integer not less than 1.
        weighted_chunk_lengths = relative_chunk_lengths.apply(
            lambda x: max(
                1,
                round(x * max_import_len / sum(relative_chunk_lengths)),
            )
        )
        weighted_chunk_lengths = list(weighted_chunk_lengths)
        # Adjust max weighted chunk lengths so they are never above their
        # actual lengths. E.g.,
        # [2, 4, 2] <- chunk lengths ("ab.abcd.ab")
        # [1, 3, 4] <- weighted chunk lengths
        # [1, 3, 2] <- adj chunk lengths
        adj_chunk_lengths = [
            min(lengths) for lengths in zip(chunk_lengths, weighted_chunk_lengths)
        ]
        hdbg.dassert_eq(len(adj_chunk_lengths), len(chunks))
        _LOG.debug("-> chunk_lengths_tmp=%s", str(adj_chunk_lengths))
        return adj_chunk_lengths

    @staticmethod
    def _chunkify(long_import: str) -> Chunks:
        """
        Convert a long import into import chunks, breaking on `_` and `.`.

        :param long_import: long import, e.g. "dataflow_amp.real_time.pipeline"
        :return: long import split in chunks, e.g. `["dataflow", "amp", "real",
            "time", "pipeline"]`
        """
        _LOG.debug("long_import=%s", long_import)
        chunks = long_import.replace("_", ".").split(".")
        chunks = [chunk.lower() for chunk in chunks if len(chunk) > 0]
        _LOG.debug("chunks=%s", chunks)
        return chunks

    @staticmethod
    def _print_long_import_to_short(
        long_import_to_short: LongImportToShort,
    ) -> str:
        """
        Print a mapping from long import (e.g. "linter.amp_black") to short
        import (e.g. "lambla").

        :param long_import_to_short: long import to short import mappings
        :return: prettified long import to short import mappings for printing
        """
        res = []
        for key in sorted(long_import_to_short.keys()):
            value = long_import_to_short[key]
            res.append(f"{key} -> {value}")
        return "\n".join(res)

    @staticmethod
    def _print_short_import_to_long(
        short_import_to_long: ShortImportToLong,
    ) -> str:
        """
        Print a mapping from short import (e.g. "lambla") to long import (e.g.
        "linter.amp_black").

        :param short_import_to_long: short import to long import mappings
        :return: prettified short import to long import mappings for printing
        """
        res = []
        for value in sorted(short_import_to_long.keys()):
            keys = short_import_to_long[value]
            res.append(f"{value} -> ({len(keys)}) {str(keys)}")
        return "\n".join(res)

    def _shorten_import(
        self,
        long_import: str,
        long_import_to_short: LongImportToShort,
    ) -> Optional[str]:
        """
        Shorten an import if it is possible.

        :param long_import: long import
        :param long_import_to_short: existing long import to short import mappings
        :return: short import or None if it was not possible to shorten the long import
            (e.g., due to collision or a not supported name)
        """
        _LOG.debug("long_import=%s", long_import)
        # Apply custom mapping to the corresponding long imports.
        if long_import in _CUSTOM_SHORT_IMPORTS:
            # Get short import from custom short imports.
            short_import: Optional[str] = _CUSTOM_SHORT_IMPORTS[long_import]
            _LOG.debug(
                "Using custom short import='%s' for long_import='%s'",
                short_import,
                long_import,
            )
            return short_import
        # Chunkify the long import.
        # E.g., dataflow_amp.real_time.pipeline ->
        # ["dataflow", "amp", "real", "time", "pipeline"].
        chunks = self._chunkify(long_import)
        _LOG.debug("chunks=%s", chunks)
        # Compute maximum chunk length for each chunk.
        chunk_lengths = self._compute_max_chunk_lengths(chunks)
        # Come up with a unique short import if it is possible.
        short_import = self._search_for_unique_short_import(
            chunks,
            chunk_lengths,
            set(long_import_to_short.values()),
        )
        return short_import

    # The function is an naive implementation of `_shorten_import()`.
    # def _shorten_import_naive(long_import: str, target_num_chars: int = 8) -> str:
    #     """
    #     Shorten an import using a fixed number of characters per chunk.
    #     """
    #     _LOG.debug("long_import=%s", long_import)
    #     # Break in chunks.
    #     chunks = _chunkify(long_import)
    #     # Use an equal number of characters for each chunks, trying to obtain a short
    #     # import with the requested number of characters.
    #     num_chars_per_chunk = max(1, target_num_chars // len(chunks))
    #     # TODO(gp): Use `_compute_short_import()`.
    #     initials = [chunk[:num_chars_per_chunk] for chunk in chunks]
    #     short_import = "".join(initials)
    #     _LOG.debug("long=%s -> short=%s", long_import, short_import)
    #     return short_import

    def _search_for_unique_short_import(
        self,
        chunks: Chunks,
        chunk_lengths: ChunkLengths,
        short_imports: Set[str],
    ) -> Optional[str]:
        """
        Search for a short import created from `chunks` that is not in
        `short_imports` already.

        The short version for each `chunk` has a length <= than the
        corresponding `chunk_length`. We give priority to the last chunk and
        to longer chunks, that yield a unique shorter import.

        If it is impossible to create a unique short import, return None.

        :param chunks: long import chunks
        :param chunk_lengths: long import chunks' lengths
        :param short_imports: existing short imports
        :return: short import
        """
        _LOG.debug("chunks=%s", str(chunks))
        # Process short imports for `/helpers` file names that start with "h"
        # so there are no short imports that start with "hh" (e.g., "hhpandas").
        if chunks[0] == "helpers":
            if chunks[1][0] == "h":
                # Remove the 1st "h" from the 2nd chunk.
                chunks[1] = chunks[1][1:]
                # Adjust the 2nd chunk max length so it's not greater than its
                # actual length.
                # E.g. if `helpers.hnumpy` -> `helpers.numpy`, then
                # [2, 6] -> [2, 5], since "numpy" is only 5 chars long.
                chunk_lengths[1] = min(len(chunks[1]), chunk_lengths[1])
        #
        if self.use_special_abbreviations:
            # Override certain chunks and their lengths using a predefined dictionary.
            chunks, chunk_lengths = self._use_special_abbreviations(
                chunks, chunk_lengths
            )
        # Build the bounds for the length of each chunk.
        iter_space = []
        # Reverse the chunk lengths to give priority to the last chunk.
        for chunk_length in reversed(chunk_lengths):
            # Use range [chunk_length, 1] to give priority to longer imports.
            range_ = range(1, chunk_length + 1)
            range_ = reversed(range_)
            iter_space.append(list(range_))
        _LOG.debug("iter_space=%s", str(iter_space))
        # Iterate in the space given by the bounds.
        # E.g., [3, 2, 1] -> range(1, 3), range(1, 2), range(1, 1).
        for chunk_lengths_tmp in itertools.product(*iter_space):
            # Reverse again to account for the fact that we are scanning
            # the chunk lengths in reversed order.
            chunk_lengths = list(reversed(chunk_lengths_tmp))
            short_import = self._compute_short_import(chunks, chunk_lengths)
            _LOG.debug(
                hprint.to_str("chunk_lengths_tmp short_import chunk_lengths")
            )
            if short_import not in short_imports:
                # We found a unique import.
                _LOG.debug("  -> Found unique import '%s'", short_import)
                return short_import
        _LOG.debug(
            "Can't shorten chunks='%s' with chunk_lengths='%s', skipping",
            chunks,
            chunk_lengths,
        )
        return None

    def _build_reverse_mapping(
        self,
        long_import_to_short: LongImportToShort,
    ) -> ShortImportToLong:
        """
        Build the reverse mapping: value -> list of keys.

        :param long_import_to_short: long import to short import mappings, e.g.
            `{"long_import1": "short_import1", "long_import2": "short_import1"}`
        :return: short import to long import mappings, e.g.
            `{"short_import1": ["long_import1", "long_import2"]}`
        """
        short_import_to_long: ShortImportToLong = {}
        for key, value in long_import_to_short.items():
            if value not in short_import_to_long:
                short_import_to_long[value] = []
            short_import_to_long[value].append(key)
        _LOG.debug(
            "short_to_long_import=\n%s",
            self._print_short_import_to_long(short_import_to_long),
        )
        return short_import_to_long


# #############################################################################
# Replace imports in code
# #############################################################################


class CodeImportNormalizer:
    """
    Normalize short imports in files.
    """

    def replace_short_imports_in_file(
        self,
        file_path: str,
        long_to_short_imports: LongImportToShort,
    ) -> List[str]:
        """
        Replace short imports in a file with Python code.

        A correct short import for a given long import is taken from the
        pre-computed mapping in `long_to_short_imports`.

        The following situations are possible:
        1) A correct short import (e.g. `import helpers.cache as hcache`) is
           found once in the file.
           - Nothing is changed.
        2) A correct short import (e.g. `import helpers.cache as hcache`) is
           found more than once in the file.
           - Nothing is changed; a warning is issued that the same import is
             found multiple times.
        3) An incorrect short import (e.g. `import helpers.cache as hcac`) is
           found once in the file.
           - It is replaced with the correct one, unless it is in a comment or
             a (doc)string.
        4) An incorrect short import (e.g. `import helpers.cache as hcac`) is
           found more than once in the file.
           - They are replaced with the correct one, unless they are in a comment
             or a (doc)string; a warning is issued that the same import is
             found multiple times.
        5) Multiple imports of the same long import are found; the first one is
           correct (e.g. `import helpers.cache as hcache`), the second one is
           incorrect (e.g. `import helpers.cache as hcac`).
           - The incorrect one is replaced with the correct one, unless it is in
             a comment or a (doc)string; a warning is issued that the same import
             is found multiple times.
        6) Multiple imports of the same long import are found; the first one is
           incorrect (e.g. `import helpers.cache as hcac`), the second one is
           correct (e.g. `import helpers.cache as hcache`).
           - The incorrect one is replaced with the correct one, unless it is in
             a comment or a (doc)string; a warning is issued that the same import
             is found multiple times.

        :param file_path: path to the file to process
        :param long_to_short_imports: pre-computed long-to-short import mappings
        :return: warnings about imports, if any
        """
        _LOG.debug("Cleaning imports in '%s'.", file_path)
        # Extract code from the input file.
        code = hio.from_file(file_path)
        # Extract long-to-short import mappings from the current file.
        import_mappings_from_file, warnings = (
            self._extract_existing_import_mappings_from_code(code)
        )
        for long_import, short_import in import_mappings_from_file:
            if long_import not in long_to_short_imports.keys():
                # TODO(Grisha): add import normalization for 3rd party and native packages in #215.
                # TODO(Grisha): after #215 is done `_LOG.debug()` -> assertion.
                _LOG.debug(
                    "There is no long-to-short import mapping for file='%s'",
                    file_path,
                )
                continue
            old_short_import = short_import
            # Get short import from the pre-computed mapping.
            new_short_import = long_to_short_imports[long_import]
            if old_short_import == new_short_import:
                # Short import is OK, skip it.
                continue
            # Make sure that there are no conflicts of the new import with the existing
            # file code.
            conflict = self._is_short_import_used(
                code=code, short_import=new_short_import, long_import=long_import
            )
            hdbg.dassert(
                not conflict,
                msg=f"Short import '{new_short_import}' is already used in '{file_path}'",
            )
            # Replace all instances of the short import with the transformed short
            # import for that file.
            _LOG.debug(
                "Replacing short import '%s' with '%s' for '%s'",
                old_short_import,
                new_short_import,
                long_import,
            )
            code = self._replace_short_import_in_code(
                code=code,
                old_short_import=old_short_import,
                new_short_import=new_short_import,
            )
        # Save changes to the file.
        hio.to_file(file_path, code)
        return warnings

    @staticmethod
    def _replace_short_import_in_code(
        code: str, old_short_import: str, new_short_import: str
    ) -> str:
        """
        Replace an old short import with a new short import in the code.

        The import is not replaced if it is in a comment or a (doc)string.

        :param code: Python code
        :param old_short_import: short import to be replaced
        :param new_short_import: short import used as replacement
        :return: the updated code
        """
        _LOG.debug(
            "Replace import '%s' -> '%s'", old_short_import, new_short_import
        )
        # Ensure we are not replacing X with X.
        hdbg.dassert_ne(
            old_short_import,
            new_short_import,
            msg=f"short import '{new_short_import}' is unnecessary",
        )
        lines = code.split("\n")
        docstring_line_indices = hstring.get_docstring_line_indices(lines)
        upd_lines = []
        for i, line in enumerate(lines):
            if i in docstring_line_indices or liutils.is_comment(line):
                # Skip the data from docstrings and comments.
                upd_lines.append(line)
                continue
            # Detect strings in a line to be ignored.
            strings_spans = []
            for str_pattern in ['"(.*?)"', "'(.*?)'"]:
                for matched_string in re.finditer(str_pattern, line):
                    strings_spans.append(matched_string.span())

            def _replace(matchobj: re.Match) -> str:
                for string_span in strings_spans:
                    if (
                        matchobj.start() >= string_span[0]
                        and matchobj.end() <= string_span[1]
                    ):
                        # Do not replace an import if it is inside a string.
                        res: str = matchobj.group()
                        return res
                res = matchobj.group().replace(old_short_import, new_short_import)
                return res

            # Replace the short import in the imports section of the file.
            regex = rf"""
                (as\s+)     # Literal keyword "as" with spaces.
                {old_short_import} # Old short import.
                \b          # Boundary of the word.
            """
            try:
                line = re.sub(regex, _replace, line, flags=re.VERBOSE)
            except re.error:
                _LOG.exception(
                    "Failed to replace '%s' with '%s'",
                    old_short_import,
                    new_short_import,
                )
            # Replace the short import in the body of the file.
            regex = rf"""
                \b            # Boundary of the word.
                (?<!\.)       # Ensure that it is not a property of another object.
                (?<!/)        # Ensure that it is not a part of a file's path.
                (?<!import\s) # Ensure that it is not the start of another import.
                {old_short_import}   # Old short import.
                (?=\.|\[|\()  # Ensure that it is an invocation.
            """
            try:
                line = re.sub(regex, _replace, line, flags=re.VERBOSE)
            except re.error:
                _LOG.exception(
                    "Failed to replace '%s' with '%s'",
                    old_short_import,
                    new_short_import,
                )
            # Store the line after replacements.
            upd_lines.append(line)
        updated_code = "\n".join(upd_lines)
        return updated_code

    @staticmethod
    def _is_short_import_used(
        code: str, short_import: str, long_import: str
    ) -> bool:
        """
        Check if a short import is already used in the code.

        :param code: file content
        :param short_import: short import to check
        :param long_import: the long import that the short import is linked to
        :return: True if short import is used
        """
        # Make sure that this short import is not used with a different long import.
        # E.g., check that `pd` is not used with any long import other than `pandas`,
        # such as, for example, `import pydocstyle as pd`.
        import_regex = (
            rf"import\s+((?!(?:{long_import}))\S+)\s+as\s+{short_import}\b"
        )
        # Make sure that this short import is not a variable name, e.g.,
        # `pd = 2*2`.
        assignment_regex = rf"\b{short_import}\s*="
        all_regex = [import_regex, assignment_regex]
        # Iterate over the lines of the code to find short import pattern.
        lines = code.split("\n")
        docstring_line_indices = hstring.get_docstring_line_indices(lines)
        for i, line in enumerate(lines):
            if i in docstring_line_indices or liutils.is_comment(line):
                # Skip the data from docstrings and comments.
                continue
            # We don't want to check the content of the strings, so
            # remove them from the line.
            # Works both with oneline and multiline strings.
            for str_pattern in ['"(.*?)"', "'(.*?)'"]:
                line = re.sub(str_pattern, "", line)
            if any(re.search(regex, line) for regex in all_regex):
                # If the pattern exists in the line after the preprocessing,
                # inform that the short import was found in file.
                return True
        return False

    @staticmethod
    def _extract_existing_import_mappings_from_code(
        code: str,
    ) -> Tuple[List[Tuple[str, str]], List[str]]:
        """
        Extract long-to-short import mappings from the code.

        The code is parsed for constructions like `import long_import as shimp`.
        If the same import is found multiple times, a warning is returned.

        :param code: content of the file
        :return: 
            - long-to-short import mappings from the code
            - warnings about non-unique imports, if any 
        """
        # List of modules to exclude from import transformation.
        _EXCLUDED_IMPORT_REGEX = [r"IPython\.", r"notebook\."]
        regex = rf"import\s+((?!(?:{'|'.join(_EXCLUDED_IMPORT_REGEX)}))\S+)\s+as\s+(\S+\b)"
        # Matches are stored as a list of tuples, e.g. `[(long_import1, short_import1),
        # (long_import2, short_import2)]`.
        matches = re.findall(regex, code)
        #
        unique_matches: List[Tuple[str, str]] = []
        warnings: List[str] = []
        for match in matches:
            if any(match[0] == seen_match[0] for seen_match in unique_matches):
                warnings.append(f"'{match[0]}' is imported multiple times")
            if match not in unique_matches:
                # Keep only unique matches, preserving the order.
                unique_matches.append(match)
            else:
                warnings.append(f"Found the same import `import {match[0]} as {match[1]}` multiple times")
        return unique_matches, warnings


# #############################################################################
# Generate import docstring
# #############################################################################


class ImportDocstringGenerator:
    """
    Generate the import docstring for a Python file.
    """

    def process_file(
        self,
        file_path: str,
        long_to_short_import: LongImportToShort,
    ) -> str:
        """
        Generate the import line for the file.

        :param file_path: a file path to process
        :param long_to_short_import: long-to-short import mappings
        :return: an update content of the file
        """
        # Read the code in the Python file.
        code = hio.from_file(file_path)
        # Get the canonical import for the file path.
        long_import = LongToShortImportGenerator.get_long_import_from_file_path(
            file_path
        )
        hdbg.dassert_in(long_import, long_to_short_import.keys())
        short_import = long_to_short_import[long_import]
        # Get the code with the fixed import line.
        _LOG.debug(
            "Normalizing import docstring in file='%s'",
            file_path,
        )
        new_code = self._process_code(code, long_import, short_import)
        return new_code

    @staticmethod
    def _insert_docstring_if_needed(code: str) -> str:
        """
        Insert an empty import docstring at the beginning of the file, if
        missing.

        :param code: the text of the file
        :return: the code with the empty docstring at the beginning of the file
        """
        if (
            "Import as:\n\nimport" in code
            or code.startswith('"""')
            or code.startswith('r"""')
        ):
            # Check whether the file starts with the docstring. In this case,
            # the file already has an import docstring and no insertion is needed.
            return code
        # Insert an empty docstring in the beginning of the file.
        new_code = f'"""\n"""\n\n{code}'
        return new_code

    @staticmethod
    def _remove_import_from_docstring_text(docstring_text: str) -> str:
        """
        Remove the import line from the docstring text.

        :param docstring_text: the docstring text
        :return: the docstring text with the import line removed
        """
        # Split the docstring into lines.
        doc_lines = docstring_text.strip("\n").split("\n")
        # Get the index of the first line that starts with "import".
        # We want to remove the import statement and everything after.
        import_lines = [
            ind
            for ind, line in enumerate(doc_lines)
            if line.lower().startswith("import")
        ]
        if not import_lines:
            # Make sure that the docstring ends with two newlines.
            docstring_text_new_lines = docstring_text.rstrip("\n") + "\n\n"
            return docstring_text_new_lines
        # Get the index of the first import-line.
        first_import = import_lines[0]
        # Warn if there are the comments after the import line.
        if len(doc_lines) > first_import + 1:
            _LOG.warning(
                "The docstring must end with the import line: "
                "all comments after the import line will be removed."
            )
        # Select only the lines before the import line.
        valid_lines = doc_lines[:first_import]
        docstring_clean = "\n".join(valid_lines)
        # Make sure that the docstring ends with two newlines.
        docstring_clean_new_lines = "\n" + docstring_clean + "\n\n"
        return docstring_clean_new_lines

    @staticmethod
    def _normalize_newlines(docstring: str) -> str:
        """
        Normalize the newlines.

        Normalization includes:
            - Removing extra new lines, i.e. the max number of new lines is 2
            - Keeping only 1 new line at the beginning/end of the docstring

        :param docstring: the docstring
        :return: the docstring with the newlines normalized
        """
        # Normalize the maximum number of the newlines.
        docstring = re.sub("(\n){3,}", "\n\n", docstring, flags=re.S)
        # Normalize the newlines at the beginning of the docstring.
        docstring = re.sub('"""\n\nImport', '"""\nImport', docstring, flags=re.S)
        # Normalize the newlines at the end of the docstring.
        docstring = docstring.replace('\n\n"""', '\n"""')
        return docstring

    def _process_code(
        self, code: str, long_import: str, short_import: str
    ) -> str:
        """
        Update the import line with the correct short import in the code.

        :param code: the content of the file
        :param long_import: long import name, e.g. "helpers.git"
        :param short_import: short import name, e.g. "hgit"
        :return: processed content of the file
        """
        if liutils.is_shebang(code):
            # Check whether the file starts with the shebang. In this case,
            # the file is executable and no import docstring is needed.
            _LOG.debug(
                "The file starts with the shebang, no import docstring is needed.",
            )
            return code
        # Insert an import line at the beginning of the file.
        code = self._insert_docstring_if_needed(code)
        # Fill the docstring with the correct import or fix the existing one.
        new_content = self._fix_import(code, long_import, short_import)
        return new_content

    def _fix_import(
        self,
        code: str,
        long_import: str,
        short_import: str,
    ) -> str:
        """
        Update the docstring with the correct short import.

        :param code: the content of the file
        :param long_import: long import name
        :param short_import: short import name
        :return: the content with the import line fixed
        """
        # Extract the first docstring of the file.
        docstrings = re.findall(r'"""(.*?)"""', code, flags=re.S)
        # Make sure that there is at least one docstring.
        hdbg.dassert_lte(
            1, len(docstrings), msg="The code does not contain any docstrings"
        )
        original_docstring = docstrings[0]
        # Remove the '"""' to extract the text from the docstring.
        docstring_text = original_docstring.replace('"""', "")
        # Remove an import line from the docstring text.
        no_import = self._remove_import_from_docstring_text(docstring_text)
        # Create the new import line.
        new_import_line = (
            f"Import as:\n\nimport {long_import} as {short_import}\n"
        )
        # Update the docstring text with the new import line.
        new_docstring = no_import + new_import_line
        # Reproduce an actual look of the docstring, surrounding it with '"""'.
        original_docstring_quoted = f'"""{original_docstring}"""'
        new_docstring_quoted = f'"""{new_docstring}"""'
        # Normalize the newlines.
        new_docstring_quoted = self._normalize_newlines(new_docstring_quoted)
        # Replace the old docstring with the new one.
        new_code = code.replace(original_docstring_quoted, new_docstring_quoted)
        return new_code


# #############################################################################
# Normalize imports end-to-end
# #############################################################################


class _NormalizeImports(liaction.Action):
    """
    Use the canonical short imports and update the import docstring.
    """

    def __init__(self, py_files: List[str]) -> None:
        """
        Init the class with a 'root_dir'.

        :param py_files: list of Python files' paths
        :return:
        """
        # Save Python file names in a txt file.
        file_name = "tmp.amp_normalize_import.txt"
        txt = "\n".join(py_files)
        hio.to_file(file_name, txt)
        # Get long-to-short import mappings for all extracted files.
        short_import_generator = LongToShortImportGenerator()
        self.long_to_short_import = short_import_generator.shorten_import_names(
            py_files
        )
        super().__init__("")

    def check_if_possible(self) -> bool:
        """
        Check if the action can be executed.

        :return: True if action can be executed, False otherwise
        """
        return True

    def _execute(self, file_name: str, pedantic: int) -> List[str]:
        """
        Execute the action.

        :param file_name: path to the file to process
        :param pedantic: 1 if it needs to be run in angry mode, 0 otherwise
        :return: list of strings representing the output
        """
        _ = pedantic
        if not liutils.is_py_file(file_name):
            # Skip a file if it is not a Python file.
            _LOG.debug("Skipping file='%s'", file_name)
            return []
        #
        if os.path.basename(file_name) in liutils.FILES_TO_EXCLUDE:
            # Skip a file if it is in the list of files to exclude and
            # warn a user. E.g. "__init.py__".
            _LOG.warning(
                "Files '%s' are not processed by ImportNormalizer, skipping file='%s'",
                liutils.FILES_TO_EXCLUDE,
                file_name,
            )
            return []
        # Replace the short imports in the file.
        _LOG.debug("The short imports are fixed in %s'", file_name)
        short_import_normalizer = CodeImportNormalizer()
        warnings = short_import_normalizer.replace_short_imports_in_file(
            file_name, self.long_to_short_import
        )
        # Decorate warning messages.
        warnings_out = [f"{file_name}: {w}" for w in warnings]
        if (
            liutils.is_under_test_dir(file_name)
            or liutils.is_paired_jupytext_file(file_name)
            or liutils.is_executable(file_name)
        ):
            # Skip test Python files, paired jupytext Python files, and executables.
            _LOG.debug(
                "Import docstring is not inserted for Python test files, "
                "jupytext paired Python files, and Python executables, "
                "skipping file='%s'",
                file_name,
            )
            return warnings_out
        # Replace the import docstring in the file that is not a test
        # Python file, not a paired jupytext Python file nor an executable Python file.
        import_docstring_generator = ImportDocstringGenerator()
        fixed_content = import_docstring_generator.process_file(
            file_name,
            self.long_to_short_import,
        )
        if fixed_content is not None:
            _LOG.debug("The import line is fixed in %s'", file_name)
            hio.to_file(file_name, fixed_content)
        return warnings_out


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--generate_map",
        action="store_true",
        default=False,
        help="Generate the long-short import map, print it, and exit.",
    )
    parser.add_argument(
        "files", nargs="+", action="store", type=str, help="Files to process"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level)
    # Get the root of the Git repo.
    root_dir = hgit.get_client_root(super_module=False)
    _LOG.debug("root_dir = '%s'", root_dir)
    # Get the local file paths.
    py_files = liutils.get_python_files_to_lint(root_dir)
    if args.generate_map:
        # Generate the long-to-short import mapping, print it and exit.
        short_import_generator = LongToShortImportGenerator()
        long_to_short_import = short_import_generator.shorten_import_names(
            py_files
        )
        print(long_to_short_import)
        sys.exit(0)
    # Run the import normalization pipeline.
    action = _NormalizeImports(py_files)
    action.run(args.files)


if __name__ == "__main__":
    _main(_parse())
