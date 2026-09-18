import logging
from typing import Dict, List, Optional
from unittest import mock

import dev_scripts_helpers.system_tools.docker_cleanup as dshstdocl
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__cleanup_engine
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)
# TODO(ai_gp): Add edge case tests for empty/malformed command outputs
# (testing.rules.md:## What to Test)

class Test__cleanup_engine(hunitest.TestCase):
    """
    End-to-end tests for the `_cleanup_engine()` function.
    """

    def test1(self) -> None:
        """
        Test that a dry run on the docker engine only issues read-only
        commands.
        """
        # Prepare inputs.
        engine = "docker"
        dry_run = True
        images_order = "size"
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system_to_string,
        'args': ('docker system df',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker ps -a --filter "status=running" --filter "status=paused" --filter "status=restarting"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker ps -a --filter "status=exited" --filter "status=created" --filter "status=dead" --format "{{.ID}}: {{.Names}} ({{.Status}})"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker network ls --filter "dangling=true" --format "{{.ID}}: {{.Name}}"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker volume ls --filter "dangling=true" -q',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker images --format "{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker images --filter "dangling=true" -q',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker images --format "{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker system df',),
        'kwargs': {'abort_on_error': False},
        },
        ]"""
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_sys_calls() as invocations:
            dshstdocl._cleanup_engine(
                engine, dry_run=dry_run, images_order=images_order
            )
        # Check outputs.
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test2(self) -> None:
        """
        Test that a real run on the docker engine issues the destructive
        prune commands.
        """
        # Prepare inputs.
        engine = "docker"
        dry_run = False
        images_order = "size"
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system_to_string,
        'args': ('docker system df',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker ps -a --filter "status=running" --filter "status=paused" --filter "status=restarting"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker ps -a --filter "status=exited" --filter "status=created" --filter "status=dead" --format "{{.ID}}: {{.Names}} ({{.Status}})"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker container prune -f',),
        'kwargs': {},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker network ls --filter "dangling=true" --format "{{.ID}}: {{.Name}}"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker network prune -f',),
        'kwargs': {},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker volume ls --filter "dangling=true" -q',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker builder prune -a -f',),
        'kwargs': {},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker images --format "{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker images --filter "dangling=true" -q',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker images --format "{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}"',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('docker system df',),
        'kwargs': {'abort_on_error': False},
        },
        ]"""
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_sys_calls() as invocations:
            dshstdocl._cleanup_engine(
                engine, dry_run=dry_run, images_order=images_order
            )
        # Check outputs.
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test3(self) -> None:
        """
        Test that a dry run on the apple engine skips the unsupported
        network step and the destructive build-cache step (the builder
        status is still checked, since that check is not gated on
        `dry_run`).
        """
        # Prepare inputs.
        engine = "apple"
        dry_run = True
        images_order = "size"
        # Prepare outputs.
        expected = r"""[
        {
        'function': hsystem.system_to_string,
        'args': ('container system df',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('container list --all',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('container builder status',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('container image list --format json',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('container image list --format json',),
        'kwargs': {'abort_on_error': False},
        },
        {
        'function': hsystem.system_to_string,
        'args': ('container system df',),
        'kwargs': {'abort_on_error': False},
        },
        ]"""
        expected = hprint.dedent(expected)
        # Run test.
        with hunteuti.capture_sys_calls() as invocations:
            dshstdocl._cleanup_engine(engine, dry_run=dry_run, images_order=images_order)
        # Check outputs.
        hunteuti.assert_sys_calls(self, invocations, expected)


# #############################################################################
# Test__parse_docker_size_to_bytes
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__parse_docker_size_to_bytes(hunitest.TestCase):
    """
    Test `docker_cleanup._parse_docker_size_to_bytes()`.
    """

    def helper(self, size_str: str, expected: float) -> None:
        """
        Test helper for `_parse_docker_size_to_bytes()`.

        :param size_str: Docker human-readable size to parse
        :param expected: expected size in bytes
        """
        # Run test.
        actual = dshstdocl._parse_docker_size_to_bytes(size_str)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test parsing a GB-scale size.
        """
        # Prepare inputs.
        size_str = "25.21GB"
        # Prepare outputs.
        expected = 25.21e9
        # Run test and check outputs.
        self.helper(size_str, expected)

    def test2(self) -> None:
        """
        Test parsing a zero-byte size.
        """
        # Prepare inputs.
        size_str = "0B"
        # Prepare outputs.
        expected = 0.0
        # Run test and check outputs.
        self.helper(size_str, expected)

    def test3(self) -> None:
        """
        Test parsing an MB-scale size.
        """
        # Prepare inputs.
        size_str = "500MB"
        # Prepare outputs.
        expected = 500e6
        # Run test and check outputs.
        self.helper(size_str, expected)


# #############################################################################
# Test__format_bytes
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__format_bytes(hunitest.TestCase):
    """
    Test `docker_cleanup._format_bytes()`.
    """

    def helper(self, num_bytes: float, expected: str) -> None:
        """
        Test helper for `_format_bytes()`.

        :param num_bytes: size in bytes to format
        :param expected: expected human-readable size
        """
        # Run test.
        actual = dshstdocl._format_bytes(num_bytes)
        # Check outputs.
        # TODO(ai_gp): Use assert_equal() for string comparison instead of
        # assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test formatting a byte-scale size.
        """
        # Prepare inputs.
        num_bytes = 512
        # Prepare outputs.
        expected = "512.00B"
        # Run test and check outputs.
        self.helper(num_bytes, expected)

    def test2(self) -> None:
        """
        Test formatting a GB-scale size.
        """
        # Prepare inputs.
        num_bytes = 1.2e9
        # Prepare outputs.
        expected = "1.20GB"
        # Run test and check outputs.
        self.helper(num_bytes, expected)

    def test3(self) -> None:
        """
        Test formatting a zero-byte size.
        """
        # Prepare inputs.
        num_bytes = 0
        # Prepare outputs.
        expected = "0.00B"
        # Run test and check outputs.
        self.helper(num_bytes, expected)


# #############################################################################
# Test__parse_docker_system_df
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__parse_docker_system_df(hunitest.TestCase):
    """
    Test `docker_cleanup._parse_docker_system_df()`.
    """

    def test1(self) -> None:
        """
        Test parsing a full `docker system df` table.
        """
        # Prepare inputs.
        output = """
        TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
        Images          26        1         25.21GB   13.03GB (51%)
        Containers      130       0         0B        0B
        Local Volumes   6         0         15.59GB   15.59GB (100%)
        Build Cache     91        0         6.317GB   2.541GB
        """
        output = hprint.dedent(output)
        # Prepare outputs.
        expected = """
        {'Images': {'total': '26', 'active': '1', 'size': '25.21GB', 'reclaimable': '13.03GB'}, 'Containers': {'total': '130', 'active': '0', 'size': '0B', 'reclaimable': '0B'}, 'Local Volumes': {'total': '6', 'active': '0', 'size': '15.59GB', 'reclaimable': '15.59GB'}, 'Build Cache': {'total': '91', 'active': '0', 'size': '6.317GB', 'reclaimable': '2.541GB'}}
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = dshstdocl._parse_docker_system_df(output)
        # Check outputs.
        self.assert_equal(str(actual), expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test parsing empty output.
        """
        # Prepare inputs.
        output = ""
        # Prepare outputs.
        expected = {}
        # Run test.
        actual = dshstdocl._parse_docker_system_df(output)
        # Check outputs.
        # TODO(ai_gp): Use assert_equal() for dict comparison instead of
        # assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual, expected)


# #############################################################################
# Test__format_images_table
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__format_images_table(hunitest.TestCase):
    """
    Test `docker_cleanup._format_images_table()`.
    """

    def test1(self) -> None:
        """
        Test formatting an empty list of images.
        """
        # Prepare inputs.
        images = []
        # Prepare outputs.
        expected = ""
        # Run test.
        actual = dshstdocl._format_images_table(images)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test2(self) -> None:
        """
        Test formatting a single image.
        """
        # Prepare inputs.
        images = [
            {
                "name": "repo1:latest",
                "created": "2024-01-01T00:00:00Z",
                "size_bytes": 1.2e9,
            },
        ]
        # Prepare outputs.
        expected = """
        repo1:latest 1.20GB 2024-01-01T00:00:00Z
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = dshstdocl._format_images_table(images)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test3(self) -> None:
        """
        Test formatting a list of images into a table.
        """
        # Prepare inputs.
        images = [
            {
                "name": "repo1:latest",
                "created": "2024-01-01T00:00:00Z",
                "size_bytes": 1.2e9,
            },
            {
                "name": "repo2:latest",
                "created": "2024-02-01T00:00:00Z",
                "size_bytes": 500e6,
            },
        ]
        # Prepare outputs.
        expected = """
        repo1:latest 1.20GB 2024-01-01T00:00:00Z
        repo2:latest 500.00MB 2024-02-01T00:00:00Z
        """
        expected = hprint.dedent(expected)
        # Run test.
        actual = dshstdocl._format_images_table(images)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test__get_engines
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__get_engines(hunitest.TestCase):
    """
    Test `docker_cleanup._get_engines()`.
    """

    def helper(self, docker_engine: str, expected: List[str]) -> None:
        """
        Test helper for `_get_engines()`.

        :param docker_engine: value of `--docker_engine` to resolve
        :param expected: expected list of engine names
        """
        # Run test.
        actual = dshstdocl._get_engines(docker_engine)
        # Check outputs.
        # TODO(ai_gp): Use assert_equal() for list comparison instead of
        # assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that "all" resolves to both engines.
        """
        # Prepare inputs.
        docker_engine = "all"
        # Prepare outputs.
        expected = ["docker", "apple"]
        # Run test and check outputs.
        self.helper(docker_engine, expected)

    def test2(self) -> None:
        """
        Test that "docker" resolves to a single engine.
        """
        # Prepare inputs.
        docker_engine = "docker"
        # Prepare outputs.
        expected = ["docker"]
        # Run test and check outputs.
        self.helper(docker_engine, expected)

    def test3(self) -> None:
        """
        Test that "apple" resolves to a single engine.
        """
        # Prepare inputs.
        docker_engine = "apple"
        # Prepare outputs.
        expected = ["apple"]
        # Run test and check outputs.
        self.helper(docker_engine, expected)


# #############################################################################
# Test__is_engine_available
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__is_engine_available(hunitest.TestCase):
    """
    Test `docker_cleanup._is_engine_available()`.
    """

    def helper(
        self,
        check_exec_available: bool,
        docker_running: bool,
        expected: bool,
    ) -> None:
        """
        Test helper for `_is_engine_available()`.

        :param check_exec_available: mocked return value of
            `hsystem.check_exec()`
        :param docker_running: mocked return value of
            `hdocker.is_docker_running()`
        :param expected: expected result of `_is_engine_available()`
        """
        # Prepare inputs.
        engine = "docker"
        # Run test.
        # TODO(ai_gp): Mock external dependencies (subprocess, etc.) instead of
        # internal helpers hsystem.check_exec and hdocker.is_docker_running
        # (testing.rules.md:## Mock Only External Dependencies)
        with (
            mock.patch(
                "helpers.hsystem.check_exec",
                return_value=check_exec_available,
            ),
            mock.patch(
                "helpers.hdocker.is_docker_running",
                return_value=docker_running,
            ),
        ):
            actual = dshstdocl._is_engine_available(engine)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test that a missing CLI is reported as unavailable.
        """
        # Prepare inputs.
        check_exec_available = False
        docker_running = True
        # Prepare outputs.
        expected = False
        # Run test and check outputs.
        self.helper(check_exec_available, docker_running, expected)

    def test2(self) -> None:
        """
        Test that a non-running engine is reported as unavailable.
        """
        # Prepare inputs.
        check_exec_available = True
        docker_running = False
        # Prepare outputs.
        expected = False
        # Run test and check outputs.
        self.helper(check_exec_available, docker_running, expected)

    def test3(self) -> None:
        """
        Test that an installed, running engine is reported as available.
        """
        # Prepare inputs.
        check_exec_available = True
        docker_running = True
        # Prepare outputs.
        expected = True
        # Run test and check outputs.
        self.helper(check_exec_available, docker_running, expected)


# #############################################################################
# Test__cleanup_dangling_volumes
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__cleanup_dangling_volumes(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_dangling_volumes()`.
    """

    def helper(
        self, list_output: str, dry_run: bool, expected_cmds: List[str]
    ) -> None:
        """
        Test helper for `_cleanup_dangling_volumes()`.

        :param list_output: mocked output of the dangling-volume list
            command
        :param dry_run: `dry_run` value to pass through
        :param expected_cmds: expected `system()` commands, empty if no
            removal is expected
        """
        # Prepare inputs.
        list_output = hprint.dedent(list_output).strip()
        engine = "docker"
        # Run test.
        # TODO(ai_gp): Mock external dependencies (subprocess, etc.) instead of
        # internal helper hsystem.system_to_string
        # (testing.rules.md:## Mock Only External Dependencies)
        with (
            hunteuti.capture_sys_calls() as sys_calls,
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
        ):
            dshstdocl._cleanup_dangling_volumes(engine, dry_run=dry_run)
        # Check outputs.
        actual_cmds = [
            call["args"][0]
            for call in sys_calls
            if call["function"] == "hsystem.system"
        ]
        # TODO(ai_gp): Use assert_equal() for list comparison instead of
        # assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual_cmds, expected_cmds)

    def test1(self) -> None:
        """
        Test that a dry run does not remove dangling volumes.
        """
        # Prepare inputs.
        list_output = """
        vol1
        vol2
        """
        dry_run = True
        # Prepare outputs.
        expected_cmds: List[str] = []
        # Run test and check outputs.
        self.helper(list_output, dry_run, expected_cmds)

    def test2(self) -> None:
        """
        Test that a non-empty dangling volume list is removed when not a
        dry run.
        """
        # Prepare inputs.
        list_output = """
        vol1
        vol2
        """
        dry_run = False
        # Prepare outputs.
        expected_cmds = ["docker volume rm vol1 vol2"]
        # Run test and check outputs.
        self.helper(list_output, dry_run, expected_cmds)

    def test3(self) -> None:
        """
        Test that an empty dangling volume list triggers no removal.
        """
        # Prepare inputs.
        list_output = ""
        dry_run = False
        # Prepare outputs.
        expected_cmds: List[str] = []
        # Run test and check outputs.
        self.helper(list_output, dry_run, expected_cmds)


# #############################################################################
# Test__cleanup_dangling_images
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__cleanup_dangling_images(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_dangling_images()`.
    """

    def helper(
        self, list_output: str, dry_run: bool, expected_cmds: List[str]
    ) -> None:
        """
        Test helper for `_cleanup_dangling_images()`.

        :param list_output: mocked output of the dangling-image list
            command
        :param dry_run: `dry_run` value to pass through
        :param expected_cmds: expected `system()` commands, empty if no
            removal is expected
        """
        # Prepare inputs.
        list_output = hprint.dedent(list_output).strip()
        engine = "docker"
        # Run test.
        # TODO(ai_gp): Mock external dependencies (subprocess, etc.) instead of
        # internal helper hsystem.system_to_string
        # (testing.rules.md:## Mock Only External Dependencies)
        with (
            hunteuti.capture_sys_calls() as sys_calls,
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
        ):
            dshstdocl._cleanup_dangling_images(engine, dry_run=dry_run)
        # Check outputs.
        actual_cmds = [
            call["args"][0]
            for call in sys_calls
            if call["function"] == "hsystem.system"
        ]
        # TODO(ai_gp): Use assert_equal() for list comparison instead of
        # assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(actual_cmds, expected_cmds)

    def test1(self) -> None:
        """
        Test that a dry run does not remove dangling images.
        """
        # Prepare inputs.
        list_output = """
        img1
        img2
        """
        dry_run = True
        # Prepare outputs.
        expected_cmds: List[str] = []
        # Run test and check outputs.
        self.helper(list_output, dry_run, expected_cmds)

    def test2(self) -> None:
        """
        Test that a non-empty dangling image list is removed when not a
        dry run.
        """
        # Prepare inputs.
        list_output = """
        img1
        img2
        """
        dry_run = False
        # Prepare outputs.
        expected_cmds = ["docker rmi -f img1 img2"]
        # Run test and check outputs.
        self.helper(list_output, dry_run, expected_cmds)

    def test3(self) -> None:
        """
        Test that an empty dangling image list triggers no removal.
        """
        # Prepare inputs.
        list_output = ""
        dry_run = False
        # Prepare outputs.
        expected_cmds: List[str] = []
        # Run test and check outputs.
        self.helper(list_output, dry_run, expected_cmds)


# #############################################################################
# Test__cleanup_unused_networks
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)
# TODO(ai_gp): Add edge case tests for empty network list output
# (testing.rules.md:## What to Test)

class Test__cleanup_unused_networks(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_unused_networks()`.
    """

    def helper(
        self, engine: str, dry_run: bool, expected_last_cmd: Optional[str]
    ) -> None:
        """
        Test helper for `_cleanup_unused_networks()`.

        :param engine: `"docker"` or `"apple"`
        :param dry_run: `dry_run` value to pass through
        :param expected_last_cmd: expected command of the most recent
            `system_to_string()` call, or `None` if no call is expected
            - `system_to_string()` is also called to list dangling
              networks before the prune call, so this checks the most
              recent (prune) call rather than requiring it to be the only
              call
        """
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshstdocl._cleanup_unused_networks(engine, dry_run=dry_run)
        # Check outputs.
        system_to_string_calls = [
            call
            for call in sys_calls
            if call["function"] == "hsystem.system_to_string"
        ]
        # TODO(ai_gp): Replace piecewise checking with whole output comparison
        # using assert_equal() instead of multiple assertEqual() calls
        # (testing.rules.md:## Compare Whole Output with `assert_equal`, Not
        # Piecewise)
        if expected_last_cmd is None:
            # TODO(ai_gp): Use assert_equal() for list comparison instead of
            # assertEqual() (testing.rules.md:## Assertion Patterns)
            self.assertEqual(system_to_string_calls, [])
        else:
            # TODO(ai_gp): Use assert_equal() for tuple/dict comparison instead
            # of assertEqual() (testing.rules.md:## Assertion Patterns)
            self.assertEqual(
                system_to_string_calls[-1]["args"], (expected_last_cmd,)
            )
        system_calls = [
            call for call in sys_calls if call["function"] == "hsystem.system"
        ]
        # TODO(ai_gp): Use assert_equal() for list comparison instead of
        # assertEqual() (testing.rules.md:## Assertion Patterns)
        self.assertEqual(system_calls, [])

    def test1(self) -> None:
        """
        Test that the docker engine issues network prune on non-dry run.
        """
        # Prepare inputs.
        engine = "docker"
        dry_run = False
        # Prepare outputs.
        expected_last_cmd = "docker network prune -f"
        # Run test and check outputs.
        self.helper(engine, dry_run, expected_last_cmd)

    def test2(self) -> None:
        """
        Test that the apple engine skips network pruning without issuing
        any system call.
        """
        # Prepare inputs.
        engine = "apple"
        dry_run = False
        # Prepare outputs.
        expected_last_cmd = None
        # Run test and check outputs.
        self.helper(engine, dry_run, expected_last_cmd)


# #############################################################################
# Test__cleanup_build_cache
# #############################################################################

# TODO(ai_gp): Test the public-facing command-line interface via _main()
# or similar public functions before testing internal helper functions
# (testing.rules.md:## Test From the Outside-In)

class Test__cleanup_build_cache(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_build_cache()`.
    """

    def helper(
        self,
        engine: str,
        dry_run: bool,
        system_df: Dict[str, Dict[str, str]],
        expected_calls: str,
    ) -> None:
        """
        Test helper for `_cleanup_build_cache()`.

        :param engine: `"docker"` or `"apple"`
        :param dry_run: `dry_run` value to pass through
        :param system_df: parsed `docker system df` snapshot to pass
            through
        :param expected_calls: expected captured system calls, formatted
            as in `hunteuti.assert_sys_calls()`
        """
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dshstdocl._cleanup_build_cache(
                engine, dry_run=dry_run, system_df=system_df
            )
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected_calls)

    def test1(self) -> None:
        """
        Test that the apple engine checks the builder status and, finding
        no builder container, skips pruning without issuing any further
        system call.
        """
        # Prepare inputs.
        engine = "apple"
        dry_run = False
        system_df: Dict[str, Dict[str, str]] = {}
        # Prepare outputs.
        expected_calls = r"""[
        {
        'function': hsystem.system_to_string,
        'args': ('container builder status',),
        'kwargs': {'abort_on_error': False},
        },
        ]"""
        # Run test and check outputs.
        self.helper(engine, dry_run, system_df, expected_calls)

    def test2(self) -> None:
        """
        Test that a dry run does not remove the build cache on the docker
        engine.
        """
        # Prepare inputs.
        engine = "docker"
        dry_run = True
        system_df = {"Build Cache": {"reclaimable": "2.541GB"}}
        # Prepare outputs.
        expected_calls = "[]"
        # Run test and check outputs.
        self.helper(engine, dry_run, system_df, expected_calls)

    def test3(self) -> None:
        """
        Test that a non-dry run removes the build cache on the docker
        engine.
        """
        # Prepare inputs.
        engine = "docker"
        dry_run = False
        system_df = {"Build Cache": {"reclaimable": "2.541GB"}}
        # Prepare outputs.
        expected_calls = r"""[
        {
        'function': hsystem.system_to_string,
        'args': ('docker builder prune -a -f',),
        'kwargs': {},
        },
        ]"""
        # Run test and check outputs.
        self.helper(engine, dry_run, system_df, expected_calls)
