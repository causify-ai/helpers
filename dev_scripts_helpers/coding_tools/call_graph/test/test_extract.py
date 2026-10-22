import json
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


def _create_call_graph(symbols: list[dsccgex.Symbol]) -> dsccgex.CallGraph:
    """
    Build a call graph from symbols, without running `jedi`.

    :param symbols: symbols of the graph, all defined in the file `m.py`
    :return: call graph with no edges, so a test can add its own
    """
    symbol_map: dict[str, dsccgex.Symbol] = {s.id: s for s in symbols}
    cg = dsccgex.CallGraph(root_dir="r", project_root="r", symbols=symbol_map)
    return cg


def _create_symbol(sym_id: str, kind: str, parent: str) -> dsccgex.Symbol:
    """
    Build a symbol with the minimal fields.

    :param sym_id: qualified name, e.g., `m.A.f`
    :param kind: one of `module`, `class`, `function`, `method`
    :param parent: id of the enclosing module or class
    """
    symbol = dsccgex.Symbol(
        id=sym_id,
        kind=kind,
        name=sym_id.split(".")[-1],
        parent=parent,
        file="m.py",
        line_start=1,
        line_end=2,
    )
    return symbol


# #############################################################################
# Test_get_project_root
# #############################################################################


class Test_get_project_root(hunitest.TestCase):
    """
    Test `extract.get_project_root()` function.
    """

    def test1(self) -> None:
        """
        Test that the project root is the closest ancestor containing `.git`.
        """
        # Prepare inputs.
        repo_dir = os.path.join(self.get_scratch_space(), "repo")
        hio.to_file(os.path.join(repo_dir, ".git"), "gitdir: ../elsewhere")
        code_dir = os.path.join(repo_dir, "src", "pkg")
        hio.create_dir(code_dir, incremental=True)
        # Prepare outputs.
        expected = os.path.realpath(repo_dir)
        # Run test.
        actual = dsccgex.get_project_root(code_dir)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_find_python_files
# #############################################################################


class Test_find_python_files(hunitest.TestCase):
    """
    Test `extract.find_python_files()` function.
    """

    def helper(self, exclude_tests: bool, expected: str) -> None:
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
        # Prepare inputs.
        exclude_tests = False
        # Prepare outputs.
        expected = """
        pkg/__init__.py
        pkg/base.py
        pkg/test/test_zoo.py
        pkg/zoo.py
        """
        # Run test.
        self.helper(exclude_tests, expected)

    def test2(self) -> None:
        """
        Test that the tests are skipped.
        """
        # Prepare inputs.
        exclude_tests = True
        # Prepare outputs.
        expected = """
        pkg/__init__.py
        pkg/base.py
        pkg/zoo.py
        """
        # Run test.
        self.helper(exclude_tests, expected)


# #############################################################################
# Test_extract_call_graph
# #############################################################################


class Test_extract_call_graph(hunitest.TestCase):
    """
    Test `extract.extract_call_graph()` function.
    """

    def helper1(self, exclude_tests: bool) -> dsccgex.CallGraph:
        """
        Extract the call graph of the fixture package.

        :param exclude_tests: whether to skip the tests
        :return: extracted call graph
        """
        root_dir = self.get_scratch_space()
        dsccgtcgf.create_fixture_package(root_dir)
        cg = dsccgex.extract_call_graph(
            root_dir, project_root=root_dir, exclude_tests=exclude_tests
        )
        return cg

    def helper2(self, cg: dsccgex.CallGraph) -> str:
        """
        Dump the symbols of a call graph, one per line.

        :param cg: extracted call graph
        :return: kind, id, line range, and signature of each symbol
        """
        lines = [
            f"{s.kind} {s.id} {s.line_start}-{s.line_end} {s.signature}".rstrip()
            for s in cg.symbols.values()
        ]
        return "\n".join(lines)

    def helper3(self, cg: dsccgex.CallGraph) -> str:
        """
        Dump the edges of a call graph, one per line.

        :param cg: extracted call graph
        :return: kind, source, destination, and call sites of each edge, sorted
        """
        edges = sorted(cg.edges, key=lambda e: (e.kind, e.src, e.dst))
        lines = [f"{e.kind} {e.src} -> {e.dst} {e.lines}" for e in edges]
        return "\n".join(lines)

    def test1(self) -> None:
        """
        Test the symbols: kinds, names, line ranges, and signatures.
        """
        # Prepare inputs.
        exclude_tests = True
        # Prepare outputs.
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
        # Run test.
        cg = self.helper1(exclude_tests)
        actual = self.helper2(cg)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test2(self) -> None:
        """
        Test the edges: calls resolved through `self`, an import alias, and a
        local variable, plus inheritance, composition, and instantiation.
        """
        # Prepare inputs.
        exclude_tests = True
        # Prepare outputs.
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
        # Run test.
        cg = self.helper1(exclude_tests)
        actual = self.helper3(cg)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test3(self) -> None:
        """
        Test the attributes, bases, and decorators of a class.
        """
        # Prepare inputs.
        exclude_tests = True
        # Prepare outputs.
        expected = """
        Animal.attrs=['name', 'legs: int']
        Dog.bases=['pbase.Animal']
        Dog.attrs=['toy']
        kingdom.decorators=['staticmethod']
        _sound.visibility=#
        """
        # Run test.
        cg = self.helper1(exclude_tests)
        animal = cg.symbols["pkg.base.Animal"]
        dog = cg.symbols["pkg.zoo.Dog"]
        kingdom = cg.symbols["pkg.base.Animal.kingdom"]
        sound = cg.symbols["pkg.zoo.Dog._sound"]
        actual = "\n".join(
            [
                f"Animal.attrs={animal.attrs}",
                f"Dog.bases={dog.bases}",
                f"Dog.attrs={dog.attrs}",
                f"kingdom.decorators={kingdom.decorators}",
                f"_sound.visibility={sound.visibility}",
            ]
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)

    def test4(self) -> None:
        """
        Test that a test file is included by default and links to the code.
        """
        # Prepare inputs.
        exclude_tests = False
        # Prepare outputs.
        expected = "call pkg.test.test_zoo.test_main -> pkg.zoo.main [5]"
        # Run test.
        cg = self.helper1(exclude_tests)
        edges = self.helper3(cg).split("\n")
        # Keep only the edges of the test file.
        actual = "\n".join(e for e in edges if "pkg.test." in e)
        # Check outputs.
        self.assert_equal(actual, expected)


# #############################################################################
# Test_build_nx_graph
# #############################################################################


class Test_build_nx_graph(hunitest.TestCase):
    """
    Test `extract.build_nx_graph()` function.
    """

    def test1(self) -> None:
        """
        Test one node per symbol and one edge per relation, with two relations
        between the same pair of symbols.
        """
        # Prepare inputs.
        symbols = [
            _create_symbol("m", "module", ""),
            _create_symbol("m.A", "class", "m"),
            _create_symbol("m.B", "class", "m"),
            _create_symbol("m.f", "function", "m"),
        ]
        cg = _create_call_graph(symbols)
        cg.edges = [
            dsccgex.Edge("m.A", "m.B", "inherit"),
            dsccgex.Edge("m.A", "m.B", "compose"),
            dsccgex.Edge("m.f", "m.A", "instantiate"),
        ]
        # Prepare outputs.
        expected = """
        nodes=[('m', 'module'), ('m.A', 'class'), ('m.B', 'class'), ('m.f', 'function')]
        edges=[('m.A', 'm.B', 'compose'), ('m.A', 'm.B', 'inherit'), ('m.f', 'm.A', 'instantiate')]
        """
        # Run test.
        graph = dsccgex.build_nx_graph(cg)
        actual = "\n".join(
            [
                f"nodes={sorted(graph.nodes(data='kind'))}",
                f"edges={sorted(graph.edges(keys=True))}",
            ]
        )
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test_find_symbol_id
# #############################################################################


class Test_find_symbol_id(hunitest.TestCase):
    """
    Test `extract.find_symbol_id()` function.
    """

    def helper(self, query: str, expected: str) -> None:
        """
        Resolve a name in the fixture call graph.

        :param query: full id or dotted suffix of a symbol
        :param expected: expected symbol id
        """
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
        # Prepare inputs.
        query = "pkg.zoo.Toy.play"
        # Prepare outputs.
        expected = query
        # Run test.
        self.helper(query, expected)

    def test2(self) -> None:
        """
        Test a unique dotted suffix.
        """
        # Prepare inputs.
        query = "zoo.main"
        # Prepare outputs.
        expected = "pkg.zoo.main"
        # Run test.
        self.helper(query, expected)

    def test3(self) -> None:
        """
        Test a unique bare name.
        """
        # Prepare inputs.
        query = "kingdom"
        # Prepare outputs.
        expected = "pkg.base.Animal.kingdom"
        # Run test.
        self.helper(query, expected)


# #############################################################################
# Test_prune_call_graph
# #############################################################################


class Test_prune_call_graph(hunitest.TestCase):
    """
    Test `extract.prune_call_graph()` function.
    """

    def helper(self, focus: str, radius: int, expected: str) -> None:
        """
        Prune the fixture call graph and check the ids of the kept symbols.

        :param focus: symbol to center on
        :param radius: max number of connections
        :param expected: expected ids of the kept symbols, one per line, sorted
        """
        # Prepare inputs.
        root_dir = self.get_scratch_space()
        dsccgtcgf.create_fixture_package(root_dir)
        cg = dsccgex.extract_call_graph(
            root_dir, project_root=root_dir, exclude_tests=True
        )
        # Run test.
        pruned = dsccgex.prune_call_graph(cg, focus, radius)
        # Check outputs.
        actual = "\n".join(sorted(pruned.symbols))
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test one connection around a method, keeping the enclosing classes and
        modules.
        """
        # Prepare inputs.
        focus = "Toy.play"
        radius = 1
        # Prepare outputs.
        expected = """
        pkg.zoo
        pkg.zoo.Dog
        pkg.zoo.Dog.fetch
        pkg.zoo.Toy
        pkg.zoo.Toy.bounce
        pkg.zoo.Toy.play
        """
        # Run test.
        self.helper(focus, radius, expected)

    def test2(self) -> None:
        """
        Test that radius 0 keeps everything.
        """
        # Prepare inputs.
        focus = "Toy.play"
        radius = 0
        # Prepare outputs.
        expected = """
        pkg
        pkg.base
        pkg.base.Animal
        pkg.base.Animal.__init__
        pkg.base.Animal._sound
        pkg.base.Animal.kingdom
        pkg.base.Animal.speak
        pkg.base.helper
        pkg.zoo
        pkg.zoo.Dog
        pkg.zoo.Dog.__init__
        pkg.zoo.Dog._sound
        pkg.zoo.Dog.fetch
        pkg.zoo.Toy
        pkg.zoo.Toy.bounce
        pkg.zoo.Toy.play
        pkg.zoo.main
        """
        # Run test.
        self.helper(focus, radius, expected)

    def test3(self) -> None:
        """
        Test that the seeds of a class include its methods.

        `Dog.fetch` is kept since it calls `Toy.play`, a method of the focus.
        `main` is dropped since it instantiates `Dog`, not `Toy`, so it is out of
        reach.
        """
        # Prepare inputs.
        focus = "Toy"
        radius = 1
        # Prepare outputs.
        expected = """
        pkg.zoo
        pkg.zoo.Dog
        pkg.zoo.Dog.__init__
        pkg.zoo.Dog.fetch
        pkg.zoo.Toy
        pkg.zoo.Toy.bounce
        pkg.zoo.Toy.play
        """
        # Run test.
        self.helper(focus, radius, expected)


# #############################################################################
# Test_call_graph_to_dict
# #############################################################################


class Test_call_graph_to_dict(hunitest.TestCase):
    """
    Test `extract.call_graph_to_dict()` function.
    """

    def test1(self) -> None:
        """
        Test that the dict has the root dir, the stats, the symbols, and the
        edges, and that it is JSON-serializable.
        """
        # Prepare inputs.
        cg = _create_call_graph([_create_symbol("m.f", "function", "m")])
        cg.edges = [dsccgex.Edge("m.f", "m.f", "call", lines=[7])]
        cg.stats = {"resolved": 1}
        # Prepare outputs.
        expected = """
        {
          "root_dir": "r",
          "stats": {
            "resolved": 1
          },
          "symbols": [
            {
              "id": "m.f",
              "kind": "function",
              "name": "f",
              "parent": "m",
              "file": "m.py",
              "line_start": 1,
              "line_end": 2,
              "signature": "",
              "doc": "",
              "decorators": [],
              "bases": [],
              "attrs": [],
              "visibility": "+"
            }
          ],
          "edges": [
            {
              "src": "m.f",
              "dst": "m.f",
              "kind": "call",
              "lines": [
                7
              ]
            }
          ]
        }
        """
        # Run test.
        data = dsccgex.call_graph_to_dict(cg)
        actual = json.dumps(data, indent=2)
        # Check outputs.
        self.assert_equal(actual, expected, dedent=True)
