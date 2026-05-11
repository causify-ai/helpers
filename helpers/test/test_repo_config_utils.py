import logging
import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test_repo_config1
# #############################################################################


class Test_repo_config1(hunitest.TestCase):
    def _create_test_file(self) -> str:
        yaml_txt = """
        repo_info:
          repo_name: helpers
          github_repo_account: causify-ai
          github_host_name: github.com
          invalid_words:
          issue_prefix: HelpersTask

        docker_info:
          docker_image_name: helpers

        s3_bucket_info:
          unit_test_bucket_name: s3://cryptokaizen-unit-test
          html_bucket_name: s3://cryptokaizen-html
          html_ip: http://172.30.2.44

        container_registry_info:
          ecr: 623860924167.dkr.ecr.eu-north-1.amazonaws.com
          ghcr: ghcr.io/cryptokaizen

        runnable_dir_info:
          use_helpers_as_nested_module: False
          venv_tag: helpers
          dir_suffix: helpers
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "yaml.txt")
        hio.to_file(file_name, yaml_txt)
        return file_name

    def _get_repo_config(self) -> hrecouti.RepoConfig:
        file_name = self._create_test_file()
        return hrecouti.RepoConfig.from_file(file_name)

    def test1(self) -> None:
        """
        Test get_name() method.
        """
        # Prepare inputs.
        repo_config = self._get_repo_config()
        expected = "//helpers"
        # Run test.
        actual = repo_config.get_name()
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test get_repo_map() method.
        """
        # Prepare inputs.
        repo_config = self._get_repo_config()
        expected = {
            "helpers": "causify-ai/helpers",
        }
        # Run test.
        actual = repo_config.get_repo_map()
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    # TODO(gp): Test all the methods of the RepoConfig class.


# #############################################################################
# Test__read_yaml_file
# #############################################################################


class Test__read_yaml_file(hunitest.TestCase):
    """
    Test the _read_yaml_file() function.
    """

    def _helper(self, yaml_txt: str, expected: dict, test_name: str) -> None:
        """
        Helper method to test YAML file parsing.

        :param yaml_txt: YAML content to test
        :param expected: expected parsed result
        :param test_name: name for the test file
        """
        # Prepare inputs.
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), f"{test_name}.yaml")
        hio.to_file(file_name, yaml_txt)
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test1(self) -> None:
        """
        Test basic string values parsing.
        """
        yaml_txt = """
        name: test
        repo: helpers
        """
        expected = {
            "name": "test",
            "repo": "helpers",
        }
        self._helper(yaml_txt, expected, "test1")

    def test2(self) -> None:
        """
        Test nested dictionary parsing.
        """
        yaml_txt = """
        repo_info:
          repo_name: helpers
          github_repo_account: causify-ai
        docker_info:
          docker_image_name: helpers
        """
        expected = {
            "repo_info": {
                "repo_name": "helpers",
                "github_repo_account": "causify-ai",
            },
            "docker_info": {
                "docker_image_name": "helpers",
            },
        }
        self._helper(yaml_txt, expected, "test2")

    def test3(self) -> None:
        """
        Test boolean and null value parsing.
        """
        yaml_txt = """
        enabled: True
        disabled: False
        empty_value:
        null_value: null
        none_value: None
        """
        expected = {
            "enabled": True,
            "disabled": False,
            "empty_value": None,
            "null_value": None,
            "none_value": None,
        }
        self._helper(yaml_txt, expected, "test3")

    def test4(self) -> None:
        """
        Test numeric value parsing (int and float).
        """
        yaml_txt = """
        integer_value: 42
        float_value: 3.14
        negative_int: -100
        """
        expected = {
            "integer_value": 42,
            "float_value": 3.14,
            "negative_int": -100,
        }
        self._helper(yaml_txt, expected, "test4")

    def test5(self) -> None:
        """
        Test comments and empty lines are ignored.
        """
        yaml_txt = """
        # This is a comment
        name: test

        # Another comment
        repo: helpers
        """
        expected = {
            "name": "test",
            "repo": "helpers",
        }
        self._helper(yaml_txt, expected, "test5")

    def test6(self) -> None:
        """
        Test complex nested structure with all types.
        """
        yaml_txt = """
        repo_info:
          repo_name: helpers
          enabled: True
          count: 42
        s3_bucket_info:
          unit_test_bucket_name: s3://test-bucket
          html_ip: http://172.30.2.44
          shared_configs_bucket_name:
            prod: s3://prod-bucket
            test:
        """
        expected = {
            "repo_info": {
                "repo_name": "helpers",
                "enabled": True,
                "count": 42,
            },
            "s3_bucket_info": {
                "unit_test_bucket_name": "s3://test-bucket",
                "html_ip": "http://172.30.2.44",
                "shared_configs_bucket_name": {
                    "prod": "s3://prod-bucket",
                    "test": None,
                },
            },
        }
        self._helper(yaml_txt, expected, "test6")

    def test7(self) -> None:
        """
        Test with the actual repo_config.yaml structure.
        """
        # Prepare inputs.
        yaml_txt = """
        repo_info:
          repo_name: helpers
          github_repo_account: causify-ai
          github_host_name: github.com
          invalid_words:
          issue_prefix: HelpersTask
          enable_git_commit_hook: True

        docker_info:
          docker_image_name: helpers
          use_sibling_container_in_unit_tests: True
          release_team: dev_system

        s3_bucket_info:
          unit_test_bucket_name: s3://cryptokaizen-unit-test
          html_bucket_name: s3://cryptokaizen-html
          html_ip: http://172.30.2.44
          shared_configs_bucket_name:
            prod:
            preprod:
            test:

        container_registry_info:
          ecr: 623860924167.dkr.ecr.eu-north-1.amazonaws.com
          ghcr: ghcr.io/causify-ai

        runnable_dir_info:
          use_helpers_as_nested_module: False
          venv_tag: helpers
          dir_suffix: helpers
        """
        expected = {
            "repo_info": {
                "repo_name": "helpers",
                "github_repo_account": "causify-ai",
                "github_host_name": "github.com",
                "invalid_words": None,
                "issue_prefix": "HelpersTask",
                "enable_git_commit_hook": True,
            },
            "docker_info": {
                "docker_image_name": "helpers",
                "use_sibling_container_in_unit_tests": True,
                "release_team": "dev_system",
            },
            "s3_bucket_info": {
                "unit_test_bucket_name": "s3://cryptokaizen-unit-test",
                "html_bucket_name": "s3://cryptokaizen-html",
                "html_ip": "http://172.30.2.44",
                "shared_configs_bucket_name": {
                    "prod": None,
                    "preprod": None,
                    "test": None,
                },
            },
            "container_registry_info": {
                "ecr": "623860924167.dkr.ecr.eu-north-1.amazonaws.com",
                "ghcr": "ghcr.io/causify-ai",
            },
            "runnable_dir_info": {
                "use_helpers_as_nested_module": False,
                "venv_tag": "helpers",
                "dir_suffix": "helpers",
            },
        }
        self._helper(yaml_txt, expected, "repo_config")
