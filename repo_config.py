# """
# Contain info specific of this repo.
# """
#
# import logging
# from typing import Dict, List
#
# import helpers.hserver as hserver
#
# _LOG = logging.getLogger(__name__)
#
#
# _WARNING = "\033[33mWARNING\033[0m"
#
#
# def _print(msg: str) -> None:
#     # _LOG.info(msg)
#     if False:
#         print(msg)
#
#
# # We can't use `__file__` since this file is imported with an exec.
# # _print("Importing //cmamp/repo_config.py")
#
#
# # #############################################################################
# # Repo info.
# # #############################################################################
#
#
# # To customize: xyz
# #_REPO_NAME = "xyz"
# _REPO_NAME = "helpers"
#
# # To customize: xyz
# _GITHUB_REPO_ACCOUNT = "kaizen-ai"
#
# # To customize: xyz
# #_DOCKER_IMAGE_NAME = "xyz"
# _DOCKER_IMAGE_NAME = "helpers"
#
# def get_name() -> str:
#     return f"//{_REPO_NAME}"
#
#
# def get_repo_map() -> Dict[str, str]:
#     """
#     Return a mapping of short repo name -> long repo name.
#     """
#     repo_map: Dict[str, str] = {_REPO_NAME: f"{_GITHUB_REPO_ACCOUNT}/{_REPO_NAME}"}
#     return repo_map
#
#
# def get_extra_amp_repo_sym_name() -> str:
#     return f"{_GITHUB_REPO_ACCOUNT}/{_REPO_NAME}"
#
#
# # TODO(gp): -> get_github_host_name
# def get_host_name() -> str:
#     return "github.com"
#
#
# def get_invalid_words() -> List[str]:
#     return []
#
#
# def get_docker_base_image_name() -> str:
#     """
#     Return a base name for docker image.
#     """
#     return _DOCKER_IMAGE_NAME
#
#
# # TODO(gp): Convert in variables.
#
# def get_unit_test_bucket_path() -> str:
#     """
#     Return the path to the unit test bucket.
#     """
#
#     assert 0, f"Not supported by '{_REPO_NAME}'"
#     unit_test_bucket = "cryptokaizen-unit-test"
#     # We do not use `os.path.join` since it converts `s3://` to `s3:/`.
#     unit_test_bucket_path = "s3://" + unit_test_bucket
#     return unit_test_bucket_path
#
#
# def get_html_bucket_path() -> str:
#     """
#     Return the path to the bucket where published HTMLs are stored.
#     """
#     assert 0, f"Not supported by '{_REPO_NAME}'"
#     html_bucket = "cryptokaizen-html"
#     # We do not use `os.path.join` since it converts `s3://` to `s3:/`.
#     html_bucket_path = "s3://" + html_bucket
#     return html_bucket_path
#
#
# def get_html_dir_to_url_mapping() -> Dict[str, str]:
#     """
#     Return a mapping between directories mapped on URLs.
#
#     This is used when we have web servers serving files from specific
#     directories.
#     """
#     assert 0, f"Not supported by '{_REPO_NAME}'"
#     dir_to_url = {"s3://cryptokaizen-html": "http://172.30.2.44"}
#     return dir_to_url
#
#
#
#
# # #############################################################################
#
# # Copied from hprint to avoid import cycles.
#
#
# # TODO(gp): It should use *.
# def indent(txt: str, num_spaces: int = 2) -> str:
#     """
#     Add `num_spaces` spaces before each line of the passed string.
#     """
#     spaces = " " * num_spaces
#     txt_out = []
#     for curr_line in txt.split("\n"):
#         if curr_line.lstrip().rstrip() == "":
#             # Do not prepend any space to a line with only white characters.
#             txt_out.append("")
#             continue
#         txt_out.append(spaces + curr_line)
#     res = "\n".join(txt_out)
#     return res
#
#
# # End copy.
#
#
