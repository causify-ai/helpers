import logging

import helpers.hunit_test as hunitest
import helpers.hversion as hversio

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestVersioning1
# #############################################################################


class TestVersioning1(hunitest.TestCase):

    def test_get_changelog_version1(self) -> None:
        """
        Test `cmamp` version.
        """
        container_dir_name = "."
        code_version = hversio.get_changelog_version(container_dir_name)
        _LOG.debug("code_version=%s", code_version)

    def test_get_container_version1(self) -> None:
        container_version = hversio.get_container_version()
        _LOG.debug("container_version=%s", container_version)

    def test_check_version1(self) -> None:
        container_dir_name = "."
        hversio.check_version(container_dir_name)

    def test__check_version1(self) -> None:
        code_version = "1.0.0"
        container_version = "1.0.2"
        is_ok = hversio._check_version(code_version, container_version)
        self.assertFalse(is_ok)

    def test__check_version2(self) -> None:
        code_version = "1.0.0"
        container_version = "1.0.0"
        is_ok = hversio._check_version(code_version, container_version)
        self.assertTrue(is_ok)

    def test__check_version3(self) -> None:
        code_version = "1.0.0"
        container_version = "amp-1.0.0"
        is_ok = hversio._check_version(code_version, container_version)
        self.assertTrue(is_ok)

    def test_bump_version1(self) -> None:
        """
        Test major version bump.
        """
        version = "2.2.0"
        result = hversio.bump_version(version, bump_type="major")
        expected = "3.0.0"
        self.assertEqual(result, expected)

    def test_bump_version2(self) -> None:
        """
        Test minor version bump.
        """
        version = "2.2.0"
        result = hversio.bump_version(version, bump_type="minor")
        expected = "2.3.0"
        self.assertEqual(result, expected)

    def test_bump_version3(self) -> None:
        """
        Test patch version bump.
        """
        version = "2.2.0"
        result = hversio.bump_version(version, bump_type="patch")
        expected = "2.2.1"
        self.assertEqual(result, expected)
