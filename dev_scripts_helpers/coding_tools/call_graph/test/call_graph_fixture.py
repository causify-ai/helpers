"""
Create a small Python package used as input by the call graph tests.

The package has inheritance (`Dog` -> `Animal`), composition (`Dog` has a `Toy`),
calls through `self`, through an import alias (`pbase.helper()`), and through a
local variable (`d.speak()`).

Import as:

import dev_scripts_helpers.coding_tools.call_graph.test.call_graph_fixture as dsccgtcgf
"""

import logging
import os

from helpers import hio, hprint

_LOG = logging.getLogger(__name__)


def create_fixture_package(root_dir: str) -> None:
    """
    Write the package `pkg` under a directory.

    :param root_dir: directory that becomes the project root, so the modules are
        named `pkg.base` and `pkg.zoo`
    """
    _LOG.debug(hprint.to_str("root_dir"))
    pkg_dir = os.path.join(root_dir, "pkg")
    hio.to_file(os.path.join(pkg_dir, "__init__.py"), "")
    # Base module with a function and the `Animal` class.
    base = '''
    """
    Base module.
    """


    def helper(x: int) -> int:
        """
        Double a number.
        """
        return x * 2


    class Animal:
        """
        An animal.
        """

        def __init__(self, name: str, *, legs: int = 4) -> None:
            self.name = name
            self.legs: int = legs

        def speak(self) -> str:
            return self._sound()

        def _sound(self) -> str:
            return "..."

        @staticmethod
        def kingdom() -> str:
            return "animalia"
    '''
    hio.to_file(os.path.join(pkg_dir, "base.py"), hprint.dedent(base) + "\n")
    # Module with the `Dog` and `Toy` classes and a `main()` using them.
    zoo = """
    import pkg.base as pbase


    class Dog(pbase.Animal):
        def __init__(self, name: str) -> None:
            super().__init__(name)
            self.toy = Toy()

        def _sound(self) -> str:
            return "woof" + str(pbase.helper(2))

        def fetch(self) -> str:
            toy = Toy()
            return toy.play()


    class Toy:
        def play(self) -> str:
            return self.bounce()

        def bounce(self) -> str:
            return "boing"


    def main() -> None:
        d = Dog("rex")
        print(d.speak())
        d.fetch()
    """
    hio.to_file(os.path.join(pkg_dir, "zoo.py"), hprint.dedent(zoo) + "\n")
    # A test file, to check `exclude_tests`.
    test_zoo = """
    import pkg.zoo as pzoo


    def test_main() -> None:
        pzoo.main()
    """
    test_dir = os.path.join(pkg_dir, "test")
    hio.to_file(
        os.path.join(test_dir, "test_zoo.py"), hprint.dedent(test_zoo) + "\n"
    )
