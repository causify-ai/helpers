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
    def create_test_file(self) -> str:
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

    def test1(self) -> None:
        file_name = self.create_test_file()
        repo_config = hrecouti.RepoConfig.from_file(file_name)
        actual = repo_config.get_name()
        expected = "//helpers"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        file_name = self.create_test_file()
        repo_config = hrecouti.RepoConfig.from_file(file_name)
        actual = repo_config.get_repo_map()
        expected = {
            "helpers": "causify-ai/helpers",
        }
        self.assert_equal(str(actual), str(expected))

    # TODO(gp): Test all the methods of the RepoConfig class.


# #############################################################################
# Test__read_yaml_file
# #############################################################################


class Test__read_yaml_file(hunitest.TestCase):
    """
    Test the _read_yaml_file() function.
    """

    def test1(self) -> None:
        """
        Test basic string values parsing.
        """
        # Prepare inputs.
        yaml_txt = """
        name: test
        repo: helpers
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "test1.yaml")
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
        expected = {
            "name": "test",
            "repo": "helpers",
        }
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test2(self) -> None:
        """
        Test nested dictionary parsing.
        """
        # Prepare inputs.
        yaml_txt = """
        repo_info:
          repo_name: helpers
          github_repo_account: causify-ai
        docker_info:
          docker_image_name: helpers
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "test2.yaml")
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
        expected = {
            "repo_info": {
                "repo_name": "helpers",
                "github_repo_account": "causify-ai",
            },
            "docker_info": {
                "docker_image_name": "helpers",
            },
        }
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test3(self) -> None:
        """
        Test boolean and null value parsing.
        """
        # Prepare inputs.
        yaml_txt = """
        enabled: True
        disabled: False
        empty_value:
        null_value: null
        none_value: None
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "test3.yaml")
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
        expected = {
            "enabled": True,
            "disabled": False,
            "empty_value": None,
            "null_value": None,
            "none_value": None,
        }
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test4(self) -> None:
        """
        Test numeric value parsing (int and float).
        """
        # Prepare inputs.
        yaml_txt = """
        integer_value: 42
        float_value: 3.14
        negative_int: -100
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "test4.yaml")
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
        expected = {
            "integer_value": 42,
            "float_value": 3.14,
            "negative_int": -100,
        }
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test5(self) -> None:
        """
        Test comments and empty lines are ignored.
        """
        # Prepare inputs.
        yaml_txt = """
        # This is a comment
        name: test

        # Another comment
        repo: helpers
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "test5.yaml")
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
        expected = {
            "name": "test",
            "repo": "helpers",
        }
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test6(self) -> None:
        """
        Test complex nested structure with all types.
        """
        # Prepare inputs.
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
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(), "test6.yaml")
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
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
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assert_equal(str(actual), str(expected))

    def test7(self) -> None:
        """
        Test with the actual repo_config.yaml structure.
        """
        # Prepare inputs.
        file_name = os.path.join(
            self.get_scratch_space(), "repo_config.yaml"
        )
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
        yaml_txt = hprint.dedent(yaml_txt)
        hio.to_file(file_name, yaml_txt)
        # Prepare outputs.
        expected_repo_name = "helpers"
        expected_docker_image = "helpers"
        expected_bucket_name = "s3://cryptokaizen-unit-test"
        expected_ecr = "623860924167.dkr.ecr.eu-north-1.amazonaws.com"
        # Run test.
        actual = hrecouti._read_yaml_file(file_name)
        # Check outputs.
        self.assertEqual(
            actual["repo_info"]["repo_name"],
            expected_repo_name,
        )
        self.assertEqual(
            actual["docker_info"]["docker_image_name"],
            expected_docker_image,
        )
        self.assertEqual(
            actual["s3_bucket_info"]["unit_test_bucket_name"],
            expected_bucket_name,
        )
        self.assertEqual(
            actual["container_registry_info"]["ecr"],
            expected_ecr,
        )
        self.assertFalse(
            actual["runnable_dir_info"]["use_helpers_as_nested_module"]
        )
