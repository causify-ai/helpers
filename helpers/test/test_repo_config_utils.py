import logging
import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.repo_config_utils as hrecouti

_LOG = logging.getLogger(__name__)


class Test_repo_config1(hunitest.TestCase):
    def create_test_file(self) -> str:
        yaml_txt = """
        repo_info:
          repo_name: helpers
          github_repo_account: kaizen-ai
          github_host_name: github.com
          invalid_words:

        docker_info:
          docker_image_name: helpers

        s3_bucket_info:
          unit_test_bucket_name: s3//cryptokaizen-unit-test
          html_bucket_name: s3//cryptokaizen-html
          html_ip: http://172.30.2.44
        """
        yaml_txt = hprint.dedent(yaml_txt)
        file_name = os.path.join(self.get_scratch_space(),
                                 "yaml.txt")
        hio.to_file(file_name, yaml_txt)
        return file_name

    def test1(self) -> None:
        file_name = self.create_test_file()
        repo_config = hrecouti.RepoConfig.from_file(file_name)
        act = repo_config.get_name()
        exp = "//helpers"
        self.assert_equal(act, exp)
