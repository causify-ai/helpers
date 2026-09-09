import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import linters2.find_private_functions as lfindpriv


class Test_find_private_functions(hunitest.TestCase):
    """Test static private-function discovery."""

    def _write_file(self, file_name: str, content: str) -> str:
        """Write a dedented Python fixture and return its absolute path."""
        file_path = os.path.join(self.get_scratch_space(), file_name)
        hio.to_file(file_path, hprint.dedent(content))
        return file_path

    def test_local_reference(self) -> None:
        """Find a public function referenced by a sibling in one file."""
        file_path = self._write_file(
            "module.py",
            """
            def helper():
                return 1

            def caller():
                return helper()
            """,
        )
        actual = lfindpriv.find_private_functions([file_path])
        self.assertEqual(
            [(item.name, item.lineno) for item in actual],
            [("helper", 1)],
        )

    def test_cross_file_import_is_not_candidate(self) -> None:
        """Keep a function public when another file imports it."""
        source_file = self._write_file(
            "source.py",
            """
            def helper():
                return 1

            def caller():
                return helper()
            """,
        )
        consumer_file = self._write_file(
            "consumer.py",
            """
            from source import helper as imported_helper

            imported_helper()
            """,
        )
        actual = lfindpriv.find_private_functions([source_file, consumer_file])
        self.assertEqual(actual, [])

    def test_module_attribute_import_is_not_candidate(self) -> None:
        """Resolve a function referenced through an imported module alias."""
        source_file = self._write_file(
            "source.py",
            """
            def helper():
                return 1

            def caller():
                return helper()
            """,
        )
        consumer_file = self._write_file(
            "consumer.py",
            """
            import source as imported_source

            imported_source.helper()
            """,
        )
        actual = lfindpriv.find_private_functions([source_file, consumer_file])
        self.assertEqual(actual, [])

    def test_alias_and_decorator_references(self) -> None:
        """Count aliases and decorators as references without parsing strings."""
        file_path = self._write_file(
            "module.py",
            """
            def helper():
                return 1

            alias = helper

            @alias
            def decorated():
                return 2

            text = "helper()"
            """,
        )
        actual = lfindpriv.find_private_functions([file_path])
        self.assertEqual([item.name for item in actual], ["helper"])

    def test_exported_and_wildcard_names_are_skipped(self) -> None:
        """Do not report explicit or wildcard exports as private."""
        source_file = self._write_file(
            "source.py",
            """
            __all__ = ["exported"]

            def exported():
                return 1

            def local_helper():
                return 2

            def caller():
                return local_helper()
            """,
        )
        consumer_file = self._write_file(
            "consumer.py",
            """
            from source import *
            """,
        )
        actual = lfindpriv.find_private_functions([source_file, consumer_file])
        self.assertEqual(actual, [])

    def test_fix_only_changes_identifiers(self) -> None:
        """Rename a candidate while preserving strings and comments."""
        file_path = self._write_file(
            "module.py",
            """
            def helper():
                return 1

            def caller():
                # helper() remains in this comment.
                return helper()

            text = "helper()"
            """,
        )
        candidates = lfindpriv.find_private_functions([file_path])
        changed = lfindpriv.fix_private_functions(candidates)
        self.assertEqual([item.name for item in changed], ["helper"])
        actual = hio.from_file(file_path)
        expected = hprint.dedent(
            """
            def _helper():
                return 1

            def caller():
                # helper() remains in this comment.
                return _helper()

            text = "helper()"
            """
        )
        self.assertEqual(actual, expected)
