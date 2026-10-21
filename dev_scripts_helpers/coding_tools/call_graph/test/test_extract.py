import logging
import os

import pytest

# Skip this test suite if the `uv run` dependencies of the script are missing.
pytest.importorskip("jedi")
pytest.importorskip("networkx")

import dev_scripts_helpers.coding_tools.call_graph.extract as dsccgex
import dev_scripts_helpers.coding_tools.call_graph.test.call_graph_fixture as dsccgtcgf
import helpers.hunit_test as hunitest
from helpers import hio

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_get_project_root
# #############################################################################


class Test_get_project_root(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test that the project root is the closest ancestor containing `.git`.
        """
        # Prepare inputs.
        repo_dir = os.path.join(self.get_scratch_space(), "repo")
        hio.to_file(os.path.join(repo_dir, ".git"), "gitdir: ../elsewhere")
        code_dir = os.path.join(repo_dir, "src", "pkg")
        hio.create_dir(code_dir, incremental=True)
        # Run test.
        actual = dsccgex.get_project_root(code_dir)
        # Check outputs.
        self.assert_equal(actual, os.path.realpath(repo_dir))


# #############################################################################
# Test_find_python_files
# #############################################################################


class Test_find_python_files(hunitest.TestCase):
    def helper(self, *, exclude_tests: bool, expected: str) -> None:
        """
        Check the files found in the fixture package.

        :param exclude_tests: whether to skip the tests
        :param expected: expected paths, relative to the root dir
        """
        # Prepare inputs.
        root_dir = os.path.realpath(self.get_scratch_space())
        dsccgtcgf.create_fixture_package(root_dir)
        # Run test.
        files = dsccgex.find_python_files(root_dir, exclude_tests=exclude_tests)
        # Check outputs.
        actual = "\n".join(os.path.relpath(f, root_dir) for f in files)
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test that all the files are found.
        """
        expected = """
        pkg/__init__.py
        pkg/base.py
        pkg/test/test_zoo.py
        pkg/zoo.py
        """
        self.helper(exclude_tests=False, expected=expected)

    def test2(self) -> None:
        """
        Test that the tests are skipped.
        """
        expected = """
        pkg/__init__.py
        pkg/base.py
        pkg/zoo.py
        """
        self.helper(exclude_tests=True, expected=expected)


# #############################################################################
# Test_extract_call_graph
# #############################################################################


class Test_extract_call_graph(hunitest.TestCase):
    def _extract(self, *, exclude_tests: bool) -> dsccgex.CallGraph:
        """
        Extract the call graph of the fixture package.
        """
        root_dir = self.get_scratch_space()
        dsccgtcgf.create_fixture_package(root_dir)
        cg = dsccgex.extract_call_graph(
            root_dir, project_root=root_dir, exclude_tests=exclude_tests
        )
        return cg

    def _dump_symbols(self, cg: dsccgex.CallGraph) -> str:
        lines = [
            f"{s.kind} {s.id} {s.line_start}-{s.line_end} {s.signature}".rstrip()
            for s in cg.symbols.values()
        ]
        return "\n".join(lines)

    def _dump_edges(self, cg: dsccgex.CallGraph) -> str:
        edges = sorted(cg.edges, key=lambda e: (e.kind, e.src, e.dst))
        lines = [f"{e.kind} {e.src} -> {e.dst} {e.lines}" for e in edges]
        return "\n".join(lines)

    def test1(self) -> None:
        """
        Test the symbols: kinds, names, line ranges, and signatures.
        """
        # Run test.
        cg = self._extract(exclude_tests=True)
        # Check outputs.
        actual = self._dump_symbols(cg)
        expected = """
        module pkg 1-1
        module pkg.base 1-30
        function pkg.base.helper 6-10 (x: int) -> int
        class pkg.base.Animal 13-30
        method pkg.base.Animal.__init__ 18-20 (name: str, *, legs: int=4) -> None
        method pkg.base.Animal.speak 22-23 () -> str
        method pkg.base.Animal._sound 25-26 () -> str
        method pkg.base.Animal.kingdom 29-30 () -> str
        module pkg.zoo 1-28
        class pkg.zoo.Dog 4-14
        method pkg.zoo.Dog.__init__ 5-7 (name: str) -> None
        method pkg.zoo.Dog._sound 9-10 () -> str
        method pkg.zoo.Dog.fetch 12-14 () -> str
        class pkg.zoo.Toy 17-22
        method pkg.zoo.Toy.play 18-19 () -> str
        method pkg.zoo.Toy.bounce 21-22 () -> str
        function pkg.zoo.main 25-28 () -> None
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test the edges: calls resolved through `self`, an import alias, and a
        local variable, plus inheritance, composition, and instantiation.
        """
        # Run test.
        cg = self._extract(exclude_tests=True)
        # Check outputs.
        actual = self._dump_edges(cg)
        expected = """
        call pkg.base.Animal.speak -> pkg.base.Animal._sound [23]
        call pkg.zoo.Dog.__init__ -> pkg.base.Animal.__init__ [6]
        call pkg.zoo.Dog._sound -> pkg.base.helper [10]
        call pkg.zoo.Dog.fetch -> pkg.zoo.Toy.play [14]
        call pkg.zoo.Toy.play -> pkg.zoo.Toy.bounce [19]
        call pkg.zoo.main -> pkg.base.Animal.speak [27]
        call pkg.zoo.main -> pkg.zoo.Dog.fetch [28]
        compose pkg.zoo.Dog -> pkg.zoo.Toy [7]
        inherit pkg.zoo.Dog -> pkg.base.Animal [4]
        instantiate pkg.zoo.Dog.__init__ -> pkg.zoo.Toy [7]
        instantiate pkg.zoo.Dog.fetch -> pkg.zoo.Toy [13]
        instantiate pkg.zoo.main -> pkg.zoo.Dog [26]
        """
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test the attributes, bases, and decorators of a class.
        """
        # Run test.
        cg = self._extract(exclude_tests=True)
        # Check outputs.
        animal = cg.symbols["pkg.base.Animal"]
        dog = cg.symbols["pkg.zoo.Dog"]
        kingdom = cg.symbols["pkg.base.Animal.kingdom"]
        actual = "\n".join(
            [
                f"Animal.attrs={animal.attrs}",
                f"Dog.bases={dog.bases}",
                f"Dog.attrs={dog.attrs}",
                f"kingdom.decorators={kingdom.decorators}",
                f"_sound.visibility={cg.symbols['pkg.zoo.Dog._sound'].visibility}",
            ]
        )
        expected = """
        Animal.attrs=['name', 'legs: int']
        Dog.bases=['pbase.Animal']
        Dog.attrs=['toy']
        kingdom.decorators=['staticmethod']
        _sound.visibility=#
        """
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test that a test file is included by default and links to the code.
        """
        # Run test.
        cg = self._extract(exclude_tests=False)
        # Check outputs.
        actual = self._dump_edges(cg).split("\n")[1]
        expected = "call pkg.test.test_zoo.test_main -> pkg.zoo.main [5]"
        self.assert_equal(actual, expected)


# #############################################################################
# Test_find_symbol_id
# #############################################################################


class Test_find_symbol_id(hunitest.TestCase):
    def helper(self, query: str, expected: str) -> None:
        # Prepare inputs.
        root_dir = self.get_scratch_space()
        dsccgtcgf.create_fixture_package(root_dir)
        cg = dsccgex.extract_call_graph(
            root_dir, project_root=root_dir, exclude_tests=True
        )
        # Run test.
        actual = dsccgex.find_symbol_id(cg, query)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test a full symbol id.
        """
        self.helper("pkg.zoo.Toy.play", "pkg.zoo.Toy.play")

    def test2(self) -> None:
        """
        Test a unique dotted suffix.
        """
        self.helper("zoo.main", "pkg.zoo.main")

    def test3(self) -> None:
        """
        Test a unique bare name.
        """
        self.helper("kingdom", "pkg.base.Animal.kingdom")


# #############################################################################
# Test_prune_call_graph
# #############################################################################


class Test_prune_call_graph(hunitest.TestCase):
    def helper(self, focus: str, radius: int) -> list[str]:
        """
        Prune the fixture call graph and return the ids of the kept symbols.
        """
        # Prepare inputs.
        root_dir = self.get_scratch_space()
        dsccgtcgf.create_fixture_package(root_dir)
        cg = dsccgex.extract_call_graph(
            root_dir, project_root=root_dir, exclude_tests=True
        )
        # Run test.
        pruned = dsccgex.prune_call_graph(cg, focus, radius)
        return sorted(pruned.symbols)

    def test1(self) -> None:
        """
        Test one connection around a method, keeping the enclosing classes and
        modules.
        """
        symbols = self.helper("Toy.play", 1)
        actual = "\n".join(symbols)
        expected = """
        pkg.zoo
        pkg.zoo.Dog
        pkg.zoo.Dog.fetch
        pkg.zoo.Toy
        pkg.zoo.Toy.bounce
        pkg.zoo.Toy.play
        """
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test that radius 0 keeps everything.
        """
        symbols = self.helper("Toy.play", 0)
        self.assertEqual(len(symbols), 17)

    def test3(self) -> None:
        """
        Test that the seeds of a class include its methods.
        """
        symbols = self.helper("Toy", 1)
        # `main` instantiates `Dog`, not `Toy`, so it is out of reach.
        self.assertNotIn("pkg.zoo.main", symbols)
        # `Dog.fetch` calls `Toy.play`, a method of the focus.
        self.assertIn("pkg.zoo.Dog.fetch", symbols)
