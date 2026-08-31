import logging
from typing import List
from unittest import mock

import dev_scripts_helpers.system_tools.docker_cleanup as dsstdocl
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__cleanup_engine
# #############################################################################


class Test__cleanup_engine(hunitest.TestCase):
    """
    End-to-end tests for the `_cleanup_engine()` function.
    """

    def test1(self) -> None:
        """
        Test that a dry run on the docker engine only issues read-only
        commands.
        """
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
            dsstdocl._cleanup_engine("docker", dry_run=True)
        # Check outputs.
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test2(self) -> None:
        """
        Test that a real run on the docker engine issues the destructive
        prune commands.
        """
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
            dsstdocl._cleanup_engine("docker", dry_run=False)
        # Check outputs.
        hunteuti.assert_sys_calls(self, invocations, expected)

    def test3(self) -> None:
        """
        Test that a dry run on the apple engine skips the unsupported
        network and build-cache steps.
        """
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
            dsstdocl._cleanup_engine("apple", dry_run=True)
        # Check outputs.
        hunteuti.assert_sys_calls(self, invocations, expected)


# #############################################################################
# Test__parse_docker_size_to_bytes
# #############################################################################


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
        actual = dsstdocl._parse_docker_size_to_bytes(size_str)
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
        actual = dsstdocl._format_bytes(num_bytes)
        # Check outputs.
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
        actual = dsstdocl._parse_docker_system_df(output)
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
        actual = dsstdocl._parse_docker_system_df(output)
        # Check outputs.
        self.assertEqual(actual, expected)


# #############################################################################
# Test__format_images_table
# #############################################################################


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
        actual = dsstdocl._format_images_table(images)
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
        actual = dsstdocl._format_images_table(images)
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
        actual = dsstdocl._format_images_table(images)
        # Check outputs.
        self.assert_equal(actual, expected, fuzzy_match=True)


# #############################################################################
# Test__get_engines
# #############################################################################


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
        actual = dsstdocl._get_engines(docker_engine)
        # Check outputs.
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


class Test__is_engine_available(hunitest.TestCase):
    """
    Test `docker_cleanup._is_engine_available()`.
    """

    # TODO(ai_gp): Factor out common code.
    def test1(self) -> None:
        """
        Test that a missing CLI is reported as unavailable.
        """
        # Run test.
        with (
            mock.patch("helpers.hsystem.check_exec", return_value=False),
            mock.patch(
                "helpers.hdocker.is_docker_running", return_value=True
            ),
        ):
            actual = dsstdocl._is_engine_available("docker")
        # Check outputs.
        self.assertFalse(actual)

    def test2(self) -> None:
        """
        Test that a non-running engine is reported as unavailable.
        """
        # Run test.
        with (
            mock.patch("helpers.hsystem.check_exec", return_value=True),
            mock.patch(
                "helpers.hdocker.is_docker_running", return_value=False
            ),
        ):
            actual = dsstdocl._is_engine_available("docker")
        # Check outputs.
        self.assertFalse(actual)

    def test3(self) -> None:
        """
        Test that an installed, running engine is reported as available.
        """
        # Run test.
        with (
            mock.patch("helpers.hsystem.check_exec", return_value=True),
            mock.patch(
                "helpers.hdocker.is_docker_running", return_value=True
            ),
        ):
            actual = dsstdocl._is_engine_available("docker")
        # Check outputs.
        self.assertTrue(actual)


# #############################################################################
# Test__cleanup_dangling_volumes
# #############################################################################


class Test__cleanup_dangling_volumes(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_dangling_volumes()`.
    """

    # TODO(ai_gp): Factor out common code and use mock_sys_call.
    def test1(self) -> None:
        """
        Test that a dry run does not remove dangling volumes.
        """
        # Prepare inputs.
        list_output = """
        vol1
        vol2
        """
        list_output = hprint.dedent(list_output).strip()
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_dangling_volumes("docker", dry_run=True)
        # Check outputs.
        system_mock.assert_not_called()

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
        list_output = hprint.dedent(list_output).strip()
        # Prepare outputs.
        expected_cmd = "docker volume rm vol1 vol2"
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_dangling_volumes("docker", dry_run=False)
        # Check outputs.
        system_mock.assert_called_once_with(expected_cmd)

    def test3(self) -> None:
        """
        Test that an empty dangling volume list triggers no removal.
        """
        # Prepare inputs.
        list_output = ""
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_dangling_volumes("docker", dry_run=False)
        # Check outputs.
        system_mock.assert_not_called()


# #############################################################################
# Test__cleanup_dangling_images
# #############################################################################


class Test__cleanup_dangling_images(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_dangling_images()`.
    """

    # TODO(ai_gp): Factor out common code and use mock_sys_call.
    def test1(self) -> None:
        """
        Test that a dry run does not remove dangling images.
        """
        # Prepare inputs.
        list_output = """
        img1
        img2
        """
        list_output = hprint.dedent(list_output).strip()
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_dangling_images("docker", dry_run=True)
        # Check outputs.
        system_mock.assert_not_called()

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
        list_output = hprint.dedent(list_output).strip()
        # Prepare outputs.
        expected_cmd = "docker rmi -f img1 img2"
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_dangling_images("docker", dry_run=False)
        # Check outputs.
        system_mock.assert_called_once_with(expected_cmd)

    def test3(self) -> None:
        """
        Test that an empty dangling image list triggers no removal.
        """
        # Prepare inputs.
        list_output = ""
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, list_output),
            ),
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_dangling_images("docker", dry_run=False)
        # Check outputs.
        system_mock.assert_not_called()


# #############################################################################
# Test__cleanup_unused_networks
# #############################################################################


class Test__cleanup_unused_networks(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_unused_networks()`.
    """

    # TODO(ai_gp): Factor out common code and use mock_sys_call.
    def test1(self) -> None:
        """
        Test that the docker engine issues network prune on non-dry run.
        """
        # Prepare outputs.
        expected_cmd = "docker network prune -f"
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, ""),
            ) as system_to_string_mock,
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_unused_networks("docker", dry_run=False)
        # Check outputs.
        system_mock.assert_called_once_with(expected_cmd)

    def test2(self) -> None:
        """
        Test that the apple engine skips network pruning without issuing
        any system call.
        """
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string"
            ) as system_to_string_mock,
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_unused_networks("apple", dry_run=False)
        # Check outputs.
        system_to_string_mock.assert_not_called()
        system_mock.assert_not_called()


# #############################################################################
# Test__cleanup_build_cache
# #############################################################################


class Test__cleanup_build_cache(hunitest.TestCase):
    """
    Test `docker_cleanup._cleanup_build_cache()`.
    """

    # TODO(ai_gp): Factor out common code and use mock_sys_call.
    def test1(self) -> None:
        """
        Test that the apple engine skips build-cache pruning without
        issuing any system call.
        """
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string"
            ) as system_to_string_mock,
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_build_cache(
                "apple", dry_run=False, system_df={}
            )
        # Check outputs.
        system_to_string_mock.assert_not_called()
        system_mock.assert_not_called()

    def test2(self) -> None:
        """
        Test that a dry run does not remove the build cache on the docker
        engine.
        """
        # Prepare inputs.
        system_df = {"Build Cache": {"reclaimable": "2.541GB"}}
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string"
            ) as system_to_string_mock,
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_build_cache(
                "docker", dry_run=True, system_df=system_df
            )
        # Check outputs.
        system_to_string_mock.assert_not_called()
        system_mock.assert_not_called()

    def test3(self) -> None:
        """
        Test that a non-dry run removes the build cache on the docker
        engine.
        """
        # Prepare inputs.
        system_df = {"Build Cache": {"reclaimable": "2.541GB"}}
        # Prepare outputs.
        expected_cmd = "docker builder prune -a -f"
        # Run test.
        with (
            mock.patch(
                "helpers.hsystem.system_to_string",
                return_value=(0, ""),
            ) as system_to_string_mock,
            mock.patch("helpers.hsystem.system") as system_mock,
        ):
            dsstdocl._cleanup_build_cache(
                "docker", dry_run=False, system_df=system_df
            )
        # Check outputs.
        system_mock.assert_called_once_with(expected_cmd)
