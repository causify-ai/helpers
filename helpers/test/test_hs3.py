import logging
import os
from typing import Generator, Tuple

import pytest

import helpers.hio as hio
import helpers.hmoto as hmoto
import helpers.hs3 as hs3
import helpers.hserver as hserver
import helpers.hunit_test as hunitest

_LOG = logging.getLogger(__name__)


# #############################################################################
# TestReplaceStarWithDoubleStar
# #############################################################################


class TestReplaceStarWithDoubleStar(hunitest.TestCase):
    def test1(self) -> None:
        """
        Test non replacement of a single asterisk at the end of the path.
        """
        pattern_to_modify = "s3://bucket/path/*"
        new_pattern = hs3._replace_star_with_double_star(pattern_to_modify)
        self.assert_equal(new_pattern, "s3://bucket/path/*")

    def test2(self) -> None:
        """
        Test replacement of a single asterisk within the path.
        """
        pattern_to_modify = "s3://bucket/path/*/file"
        new_pattern = hs3._replace_star_with_double_star(pattern_to_modify)
        self.assert_equal(new_pattern, "s3://bucket/path/**/*/file")

    def test3(self) -> None:
        """
        Test no replacement when there are no asterisks in the path.
        """
        pattern_to_modify = "s3://bucket/path/file"
        new_pattern = hs3._replace_star_with_double_star(pattern_to_modify)
        self.assert_equal(new_pattern, "s3://bucket/path/file")

    def test4(self) -> None:
        """
        Test replacement when multiple asterisk are in the path.
        """
        pattern_to_modify = "s3://bucket/*/path/*"
        new_pattern = hs3._replace_star_with_double_star(pattern_to_modify)
        self.assert_equal(new_pattern, "s3://bucket/**/*/path/*")

    def test5(self) -> None:
        """
        Test non-replacement of asterisk at the end of the path in a special
        case.
        """
        pattern_to_modify = "s3://bucket/*/path/csv*"
        new_pattern = hs3._replace_star_with_double_star(pattern_to_modify)
        self.assert_equal(new_pattern, "s3://bucket/**/*/path/csv*")


# #############################################################################
# TestToFileAndFromFile1
# #############################################################################


@pytest.mark.requires_ck_infra
@pytest.mark.requires_aws
@pytest.mark.skipif(
    not hserver.is_CK_S3_available(),
    reason="Run only if CK S3 is available",
)
class TestToFileAndFromFile1(hmoto.S3Mock_TestCase):
    def write_read_helper(self, file_name: str, force_flush: bool) -> None:
        # Prepare inputs.
        file_content = "line_mock1\nline_mock2\nline_mock3"
        moto_s3fs = hs3.get_s3fs(self.mock_aws_profile)
        s3_path = f"s3://{self.bucket_name}/{file_name}"
        # Save file.
        # TODO(Nikola): Is it possible to verify `force_flush`?
        hs3.to_file(
            file_content,
            s3_path,
            aws_profile=moto_s3fs,
            force_flush=force_flush,
        )
        # Read file.
        saved_content = hs3.from_file(s3_path, aws_profile=moto_s3fs)
        # Check output.
        expected = r"""line_mock1
        line_mock2
        line_mock3"""
        self.assert_equal(saved_content, expected, fuzzy_match=True)

    # #########################################################################

    def test_to_file_and_from_file1(self) -> None:
        """
        Verify that regular `.txt` file is saved/read on S3.
        """
        # Prepare inputs.
        regular_file_name = "mock.txt"
        force_flush = False
        self.write_read_helper(regular_file_name, force_flush)

    def test_to_file_and_from_file2(self) -> None:
        """
        Verify that compressed (e.g,`.gz`,`gzip`) file is saved/read on S3.
        """
        # Prepare inputs.
        gzip_file_name = "mock.gzip"
        force_flush = True
        self.write_read_helper(gzip_file_name, force_flush)

    def test_to_file_invalid1(self) -> None:
        """
        Verify that only binary mode is allowed.
        """
        # Prepare inputs.
        regular_file_name = "mock.txt"
        regular_file_content = "line_mock1\nline_mock2\nline_mock3"
        moto_s3fs = hs3.get_s3fs(self.mock_aws_profile)
        s3_path = f"s3://{self.bucket_name}/{regular_file_name}"
        # Save file with `t` mode.
        with self.assertRaises(ValueError) as fail:
            hs3.to_file(
                regular_file_content, s3_path, mode="wt", aws_profile=moto_s3fs
            )
        # Check output.
        actual = str(fail.exception)
        expected = r"S3 only allows binary mode!"
        self.assert_equal(actual, expected)

    def test_from_file_invalid1(self) -> None:
        """
        Verify that encoding is not allowed.
        """
        # Prepare inputs.
        regular_file_name = "mock.txt"
        moto_s3fs = hs3.get_s3fs(self.mock_aws_profile)
        s3_path = f"s3://{self.bucket_name}/{regular_file_name}"
        # Read with encoding.
        with self.assertRaises(ValueError) as fail:
            hs3.from_file(s3_path, encoding=True, aws_profile=moto_s3fs)
        # Check output.
        actual = str(fail.exception)
        expected = r"Encoding is not supported when reading from S3!"
        self.assert_equal(actual, expected)


# #############################################################################
# TestListdir1
# #############################################################################


@pytest.mark.requires_ck_infra
@pytest.mark.requires_aws
@pytest.mark.skipif(
    not hserver.is_CK_S3_available(),
    reason="Run only if CK S3 is available",
)
class TestListdir1(hmoto.S3Mock_TestCase):
    def prepare_test_data(self) -> Tuple[str, hs3.AwsProfile]:
        bucket_s3_path = f"s3://{self.bucket_name}"
        depth_one_s3_path = f"{bucket_s3_path}/depth_one"
        # Prepare test files.
        moto_s3fs = hs3.get_s3fs(self.mock_aws_profile)
        first_s3_path = f"{depth_one_s3_path}/mock1.txt"
        lines = [b"line_mock1"]
        with moto_s3fs.open(first_s3_path, "wb") as s3_file:
            s3_file.writelines(lines)
        second_s3_path = f"{depth_one_s3_path}/mock2.gzip"
        with moto_s3fs.open(second_s3_path, "wb") as s3_file:
            s3_file.writelines(lines)
        # Prepare test directories.
        # `moto_s3fs.mkdir` is useless as empty directory is not visible.
        # There must be at least one file in the directory to be visible.
        regular_dir_s3_path = f"{depth_one_s3_path}/mock"
        additional_file_s3_path = f"{regular_dir_s3_path}/regular_mock3.txt"
        with moto_s3fs.open(additional_file_s3_path, "wb") as s3_file:
            s3_file.writelines(lines)
        git_dir_s3_path = f"s3://{bucket_s3_path}/.git"
        additional_file_s3_path = f"{git_dir_s3_path}/git_mock3.txt"
        with moto_s3fs.open(additional_file_s3_path, "wb") as s3_file:
            s3_file.writelines(lines)
        return bucket_s3_path, moto_s3fs

    # #########################################################################

    def test_listdir1(self) -> None:
        """
        Verify that all paths are found.
        """
        bucket_s3_path, moto_s3fs = self.prepare_test_data()
        pattern = "*"
        only_files = False
        use_relative_paths = False
        paths = hs3.listdir(
            bucket_s3_path,
            pattern,
            only_files,
            use_relative_paths,
            aws_profile=moto_s3fs,
            exclude_git_dirs=False,
        )
        paths.sort()
        expected_paths = [
            "mock_bucket/.git",
            "mock_bucket/.git/git_mock3.txt",
            "mock_bucket/depth_one",
            "mock_bucket/depth_one/mock",
            "mock_bucket/depth_one/mock/regular_mock3.txt",
            "mock_bucket/depth_one/mock1.txt",
            "mock_bucket/depth_one/mock2.gzip",
        ]
        self.assertListEqual(paths, expected_paths)

    def test_listdir2(self) -> None:
        """
        Verify that all relative paths are found.
        """
        bucket_s3_path, moto_s3fs = self.prepare_test_data()
        # Exclude `.git` by going level below.
        bucket_s3_path = os.path.join(bucket_s3_path, "depth_one")
        pattern = "*"
        only_files = False
        use_relative_paths = True
        paths = hs3.listdir(
            bucket_s3_path,
            pattern,
            only_files,
            use_relative_paths,
            aws_profile=moto_s3fs,
            exclude_git_dirs=False,
        )
        paths.sort()
        expected_paths = [
            "mock",
            "mock/regular_mock3.txt",
            "mock1.txt",
            "mock2.gzip",
        ]
        self.assertListEqual(paths, expected_paths)

    def test_listdir3(self) -> None:
        """
        Verify that all paths are found, except `.git` ones.
        """
        bucket_s3_path, moto_s3fs = self.prepare_test_data()
        pattern = "*"
        only_files = False
        use_relative_paths = False
        paths = hs3.listdir(
            bucket_s3_path,
            pattern,
            only_files,
            use_relative_paths,
            aws_profile=moto_s3fs,
        )
        paths.sort()
        expected_paths = [
            "mock_bucket/depth_one",
            "mock_bucket/depth_one/mock",
            "mock_bucket/depth_one/mock/regular_mock3.txt",
            "mock_bucket/depth_one/mock1.txt",
            "mock_bucket/depth_one/mock2.gzip",
        ]
        self.assertListEqual(paths, expected_paths)

    def test_listdir4(self) -> None:
        """
        Verify that all file paths are found.
        """
        bucket_s3_path, moto_s3fs = self.prepare_test_data()
        pattern = "*"
        only_files = True
        use_relative_paths = False
        paths = hs3.listdir(
            bucket_s3_path,
            pattern,
            only_files,
            use_relative_paths,
            aws_profile=moto_s3fs,
            exclude_git_dirs=False,
        )
        paths.sort()
        expected_paths = [
            "mock_bucket/.git/git_mock3.txt",
            "mock_bucket/depth_one/mock/regular_mock3.txt",
            "mock_bucket/depth_one/mock1.txt",
            "mock_bucket/depth_one/mock2.gzip",
        ]
        self.assertListEqual(paths, expected_paths)


# #############################################################################
# TestDu1
# #############################################################################


@pytest.mark.requires_ck_infra
@pytest.mark.requires_aws
@pytest.mark.skipif(
    not hserver.is_CK_S3_available(),
    reason="Run only if CK S3 is available",
)
class TestDu1(hmoto.S3Mock_TestCase):
    def test_du1(self) -> None:
        """
        Verify that total file size is returned.
        """
        bucket_s3_path = f"s3://{self.bucket_name}"
        depth_one_s3_path = f"{bucket_s3_path}/depth_one"
        # Prepare test files.
        moto_s3fs = hs3.get_s3fs(self.mock_aws_profile)
        first_s3_path = f"{bucket_s3_path}/mock1.txt"
        lines = [b"line_mock\n"] * 150
        with moto_s3fs.open(first_s3_path, "wb") as s3_file:
            s3_file.writelines(lines)
        second_s3_path = f"{depth_one_s3_path}/mock2.txt"
        with moto_s3fs.open(second_s3_path, "wb") as s3_file:
            # One level deeper to test recursive `du`.
            s3_file.writelines(lines)
        # Get multiple files.
        size = hs3.du(bucket_s3_path, aws_profile=moto_s3fs)
        expected_size = 3000
        self.assertEqual(size, expected_size)
        size = hs3.du(depth_one_s3_path, aws_profile=moto_s3fs)
        expected_size = 1500
        self.assertEqual(size, expected_size)
        # Get exactly one file.
        size = hs3.du(second_s3_path, aws_profile=moto_s3fs)
        self.assertEqual(size, expected_size)
        # Verify size in human-readable form.
        size = hs3.du(bucket_s3_path, human_format=True, aws_profile=moto_s3fs)
        expected_size = r"2.9 KB"
        self.assert_equal(size, expected_size)


# #############################################################################
# TestGenerateAwsFiles
# #############################################################################


class TestGenerateAwsFiles(hunitest.TestCase):
    # This will be run before and after each test.
    @pytest.fixture(autouse=True)
    def setup_teardown_test(self) -> Generator:
        # Run before each test.
        self.set_up_test()
        yield
        # Run after each test.
        self.tear_down_test()

    def set_up_test(self) -> None:
        self.setUp()
        os.environ["MOCK_AWS_ACCESS_KEY_ID"] = "mock_access_key"
        os.environ["MOCK_AWS_SECRET_ACCESS_KEY"] = "mock_secret_access_key"
        os.environ["MOCK_AWS_S3_BUCKET"] = "mock_s3_bucket"
        os.environ["MOCK_AWS_DEFAULT_REGION"] = "mock_default_region"
        #
        os.environ["TEST_AWS_ACCESS_KEY_ID"] = "test_access_key"
        os.environ["TEST_AWS_SECRET_ACCESS_KEY"] = "test_secret_access_key"
        os.environ["TEST_AWS_S3_BUCKET"] = "test_s3_bucket"
        os.environ["TEST_AWS_DEFAULT_REGION"] = "test_default_region"
        # Generate AWS files with mock AWS profiles.
        self._scratch_test_dir = self.get_scratch_space()
        aws_profiles = ["mock", "test"]
        hs3.generate_aws_files(
            home_dir=self._scratch_test_dir, aws_profiles=aws_profiles
        )

    def tear_down_test(self) -> None:
        del os.environ["MOCK_AWS_ACCESS_KEY_ID"]
        del os.environ["MOCK_AWS_SECRET_ACCESS_KEY"]
        del os.environ["MOCK_AWS_S3_BUCKET"]
        del os.environ["MOCK_AWS_DEFAULT_REGION"]
        #
        del os.environ["TEST_AWS_ACCESS_KEY_ID"]
        del os.environ["TEST_AWS_SECRET_ACCESS_KEY"]
        del os.environ["TEST_AWS_S3_BUCKET"]
        del os.environ["TEST_AWS_DEFAULT_REGION"]

    def helper(self, file_name: str, expected: str) -> None:
        # Check.
        target_dir = os.path.join(self._scratch_test_dir, ".aws")
        actual = hio.from_file(os.path.join(target_dir, file_name))
        self.assert_equal(actual, expected, fuzzy_match=True)

    def test1(self) -> None:
        """
        Check that AWS credentials file is generated correctly.
        """
        file_name = "credentials"
        expected = r"""
        [mock]
        aws_access_key_id=mock_access_key
        aws_secret_access_key=mock_secret_access_key
        aws_s3_bucket=mock_s3_bucket

        [test]
        aws_access_key_id=test_access_key
        aws_secret_access_key=test_secret_access_key
        aws_s3_bucket=test_s3_bucket
        """
        self.helper(file_name, expected)

    def test2(self) -> None:
        """
        Check that AWS config file is generated correctly.
        """
        file_name = "config"
        expected = """
        [profile mock]
        region=mock_default_region

        [profile test]
        region=test_default_region
        """
        self.helper(file_name, expected)


# #############################################################################


# #############################################################################
# Test_get_s3_bucket_from_stage
# #############################################################################


class Test_get_s3_bucket_from_stage(hunitest.TestCase):
    def test1(self) -> None:
        """
        Check for a valid stage.
        """
        # Define arguments.
        stage = "test"
        # Run.
        actual = hs3.get_s3_bucket_from_stage(stage)
        expected = "cryptokaizen-data-test"
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Check for a valid stage and optional suffix.
        """
        # Define arguments.
        stage = "preprod"
        suffix = "suffix_test"
        # Run.
        actual = hs3.get_s3_bucket_from_stage(stage, add_suffix=suffix)
        expected = "cryptokaizen-data.preprod/suffix_test"
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Check Invalid stage.
        """
        # Define arguments.
        stage = "Invalid"
        # Run.
        with self.assertRaises(AssertionError) as cm:
            hs3.get_s3_bucket_from_stage(stage)
        actual = str(cm.exception)
        expected = r"""
            * Failed assertion *
            'Invalid' in '{'test': 'cryptokaizen-data-test', 'preprod': 'cryptokaizen-data.preprod', 'prod': 'cryptokaizen-data'}'
             """
        self.assert_equal(actual, expected, fuzzy_match=True)


_AWS_PROFILE = "ck"


# #############################################################################
# Test_s3_get_credentials1
# #############################################################################


@pytest.mark.requires_aws
@pytest.mark.requires_ck_infra
class Test_s3_get_credentials1(hunitest.TestCase):
    def test1(self) -> None:
        res = hs3.get_aws_credentials(_AWS_PROFILE)
        _LOG.debug("res=%s", str(res))


# #############################################################################
# Test_s3_functions1
# #############################################################################


class Test_s3_functions1(hunitest.TestCase):
    def test_extract_bucket_from_path1(self) -> None:
        path = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "tmp/TestCachingOnS3.test_with_caching1/joblib",
        )
        bucket, path = hs3.split_path(path)
        self.assert_equal(bucket, "cryptokaizen-unit-test")
        self.assert_equal(path, "/tmp/TestCachingOnS3.test_with_caching1/joblib")


# #############################################################################
# Test_s3_1
# #############################################################################


@pytest.mark.requires_aws
@pytest.mark.requires_ck_infra
class Test_s3_1(hunitest.TestCase):
    def test_ls1(self) -> None:
        file_path = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "alphamatic-data",
            "README.md",
        )
        _LOG.debug("file_path=%s", file_path)
        # > aws s3 ls s3://*****
        #                   PRE data/
        # 2021-04-06 1:17:44 48 README.md
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_names = s3fs.ls(file_path)
        _LOG.debug("file_names=%s", file_names)
        self.assertGreater(len(file_names), 0)

    @pytest.mark.requires_aws
    @pytest.mark.requires_ck_infra
    def test_glob1(self) -> None:
        # > aws s3 ls s3://alphamatic-data/data/ib/metadata/
        # 2021-04-26 08:39:00      18791 exchanges-2021-04-01-134738089177.csv
        # 2021-04-26 08:39:00      18815 exchanges-2021-04-01-143112738505.csv
        # 2021-04-26 08:39:00   61677776 symbols-2021-04-01-134738089177.csv
        # 2021-04-26 08:39:00   61677776 symbols-2021-04-01-143112738505.csv
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_path = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "alphamatic-data",
            "data/ib/metadata",
        )
        glob_pattern = file_path + "/exchanges-*"
        _LOG.debug("glob_pattern=%s", glob_pattern)
        file_names = s3fs.glob(glob_pattern)
        _LOG.debug("file_names=%s", file_names)
        self.assertGreater(len(file_names), 0)

    @pytest.mark.requires_aws
    @pytest.mark.requires_ck_infra
    def test_exists1(self) -> None:
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_path = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "alphamatic-data",
            "README.md",
        )
        _LOG.debug("file_path=%s", file_path)
        actual = s3fs.exists(file_path)
        expected = True
        self.assertEqual(actual, expected)

    @pytest.mark.requires_aws
    @pytest.mark.requires_ck_infra
    def test_exists2(self) -> None:
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_path = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "alphamatic-data",
            "README_does_not_exist.md",
        )
        _LOG.debug("file_path=%s", file_path)
        actual = s3fs.exists(file_path)
        expected = False
        self.assertEqual(actual, expected)

    @pytest.mark.requires_aws
    @pytest.mark.requires_ck_infra
    def test_exists3(self) -> None:
        # > aws s3 ls alphamatic-data/data/ib/metadata/symbols-2021-04-01-143112738505.csv
        # 2021-04-26 08:39:00   61677776 symbols-2021-04-01-143112738505.csv
        s3fs = hs3.get_s3fs(_AWS_PROFILE)
        file_path = os.path.join(
            hs3.get_s3_bucket_path_unit_test(_AWS_PROFILE),
            "alphamatic-data",
            "data/ib/metadata/symbols-2021-04-01-143112738505.csv",
        )
        _LOG.debug("file_path=%s", file_path)
        actual = s3fs.exists(file_path)
        expected = True
        self.assertEqual(actual, expected)
