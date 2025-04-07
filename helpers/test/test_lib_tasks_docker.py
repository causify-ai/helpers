import logging
import os
import re
import unittest.mock as umock
from typing import Dict, Optional

import pytest

import helpers.hgit as hgit
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.lib_tasks_docker as hlitadoc
import helpers.test.test_lib_tasks as httestlib

_LOG = logging.getLogger(__name__)


# pylint: disable=protected-access


# #############################################################################
# Test_generate_compose_file1
# #############################################################################


class Test_generate_compose_file1(hunitest.TestCase):

    def helper(
        self,
        stage: str,
        *,
        use_privileged_mode: bool = False,
        use_sibling_container: bool = False,
        shared_data_dirs: Optional[Dict[str, str]] = None,
        mount_as_submodule: bool = False,
        use_network_mode_host: bool = True,
        use_main_network: bool = False,
    ) -> None:
        txt = []
        #
        params = [
            "stage",
            "use_privileged_mode",
            "use_sibling_container",
            "shared_data_dirs",
            "mount_as_submodule",
            "use_network_mode_host",
        ]
        txt_tmp = hprint.to_str(" ".join(params))
        txt.append(txt_tmp)
        #
        file_name = None
        txt_tmp = hlitadoc._generate_docker_compose_file(
            stage,
            use_privileged_mode,
            use_sibling_container,
            shared_data_dirs,
            mount_as_submodule,
            use_network_mode_host,
            use_main_network,
            file_name,
        )
        # Remove all the env variables that are function of the host.
        txt_tmp = hunitest.filter_text("CSFY_HOST_", txt_tmp)
        txt_tmp = hunitest.filter_text("CSFY_GIT_ROOT_PATH", txt_tmp)
        txt_tmp = hunitest.filter_text("CSFY_HELPERS_ROOT_PATH", txt_tmp)
        txt_tmp = hunitest.filter_text(
            "CSFY_USE_HELPERS_AS_NESTED_MODULE", txt_tmp
        )
        txt_tmp = hunitest.filter_text("OPENAI_API_KEY", txt_tmp)
        txt.append(txt_tmp)
        #
        txt = "\n".join(txt)
        txt = hunitest.filter_text(r"working_dir", txt)
        self.check_string(txt)

    def test1(self) -> None:
        self.helper(stage="prod", use_privileged_mode=True)

    def test2(self) -> None:
        self.helper(
            stage="prod", shared_data_dirs={"/data/shared": "/shared_data"}
        )

    def test3(self) -> None:
        self.helper(stage="prod", use_main_network=True)

    # TODO(ShaopengZ): This hangs outside CK infra, so we skip it.
    @pytest.mark.requires_ck_infra
    @pytest.mark.skipif(
        hgit.is_in_amp_as_submodule(), reason="Only run in amp directly"
    )
    def test4(self) -> None:
        self.helper(stage="dev")

    # TODO(ShaopengZ): This hangs outside CK infra, so we skip it.
    @pytest.mark.requires_ck_infra
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(), reason="Only run in amp as submodule"
    )
    def test5(self) -> None:
        self.helper(stage="dev")


# #############################################################################
# Test_generate_compose_file2
# #############################################################################


class Test_generate_compose_file2(hunitest.TestCase):

    def helper(
        self,
        mock_getcwd: str,
        mock_find_git_root: str,
        mock_find_helpers_root: str,
        mock_is_in_helpers_as_supermodule: bool,
        *,
        stage: str = "prod",
        use_privileged_mode: bool = True,
        use_sibling_container: bool = False,
        shared_data_dirs: Optional[Dict[str, str]] = None,
        mount_as_submodule: bool = False,
        use_network_mode_host: bool = True,
        use_main_network: bool = False,
    ) -> None:
        txt = []
        #
        params = [
            "stage",
            "use_privileged_mode",
            "use_sibling_container",
            "shared_data_dirs",
            "mount_as_submodule",
            "use_network_mode_host",
        ]
        txt_tmp = hprint.to_str(" ".join(params))
        txt.append(txt_tmp)
        #
        file_name = None
        with umock.patch.object(
            os, "getcwd", return_value=mock_getcwd
        ), umock.patch.object(
            hgit, "find_git_root", return_value=mock_find_git_root
        ), umock.patch.object(
            hgit, "find_helpers_root", return_value=mock_find_helpers_root
        ), umock.patch.object(
            hgit,
            "is_in_helpers_as_supermodule",
            return_value=mock_is_in_helpers_as_supermodule,
        ):
            txt_tmp = hlitadoc._generate_docker_compose_file(
                stage,
                use_privileged_mode,
                use_sibling_container,
                shared_data_dirs,
                mount_as_submodule,
                use_network_mode_host,
                use_main_network,
                file_name,
            )
        # Remove all the env variables that are function of the host.
        txt_tmp = hunitest.filter_text("CSFY_HOST_", txt_tmp)
        txt_tmp = hunitest.filter_text("OPENAI_API_KEY", txt_tmp)
        txt.append(txt_tmp)
        #
        txt = "\n".join(txt)
        self.check_string(txt)

    def test1(self) -> None:
        """
        Check that file is generated correctly when the repo is `//cmamp`.
        """
        self.helper(
            mock_getcwd="/data/dummy/src/cmamp1",
            mock_find_git_root="/data/dummy/src/cmamp1",
            mock_find_helpers_root="/data/dummy/src/cmamp1/helpers_root",
            mock_is_in_helpers_as_supermodule=False,
        )

    def test2(self) -> None:
        """
        Check that file is generated correctly when the repo is `//helpers`.
        """
        self.helper(
            mock_getcwd="/data/dummy/src/helpers1",
            mock_find_git_root="/data/dummy/src/helpers1",
            mock_find_helpers_root="/data/dummy/src/helpers1",
            mock_is_in_helpers_as_supermodule=True,
        )

    def test3(self) -> None:
        """
        Check that file is generated correctly when the repo is `//cmamp` and
        `//cmamp/ck.infra` is a runnable dir.
        """
        self.helper(
            mock_getcwd="/data/dummy/src/cmamp1/ck.infra",
            mock_find_git_root="/data/dummy/src/cmamp1",
            mock_find_helpers_root="/data/dummy/src/cmamp1/helpers_root",
            mock_is_in_helpers_as_supermodule=False,
        )

    def test4(self) -> None:
        """
        Check that file is generated correctly when the repo is `//orange`.
        """
        self.helper(
            mock_getcwd="/data/dummy/src/orange1",
            mock_find_git_root="/data/dummy/src/orange1",
            mock_find_helpers_root="/data/dummy/src/orange1/amp/helpers_root",
            mock_is_in_helpers_as_supermodule=False,
        )


# #############################################################################


# #############################################################################
# TestLibTasksGetDockerCmd1
# #############################################################################


# TODO(ShaopengZ): This hangs outside CK infra, so we skip it.
@pytest.mark.requires_ck_infra
class TestLibTasksGetDockerCmd1(httestlib._LibTasksTestCase):
    """
    Test `_get_docker_compose_cmd()`.
    """

    def check(self, act: str, exp: str) -> None:
        # Remove current timestamp (e.g., `20220317_232120``) from the `--name`
        # so that the tests pass.
        timestamp_regex = r"\.\d{8}_\d{6}"
        act = re.sub(timestamp_regex, "", act)
        act = hunitest.purify_txt_from_client(act)
        # This is required when different repos run Docker with user vs root / remap.
        act = hunitest.filter_text("--user", act)
        self.assert_equal(act, exp, fuzzy_match=True)

    @pytest.mark.requires_ck_infra
    # TODO(gp): After using a single docker file as part of AmpTask2308
    #  "Update_amp_container" we can probably run these tests in any repo, so
    #  we should be able to remove this `skipif`.
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(), reason="Only run in amp as submodule"
    )
    def test_docker_bash1(self) -> None:
        """
        Command for docker_bash target.
        """
        base_image = ""
        stage = "dev"
        version = "1.0.0"
        cmd = "bash"
        service_name = "app"
        use_entrypoint = False
        print_docker_config = False
        act = hlitadoc._get_docker_compose_cmd(
            base_image,
            stage,
            version,
            cmd,
            service_name=service_name,
            use_entrypoint=use_entrypoint,
            print_docker_config=print_docker_config,
        )
        exp = r"""
        IMAGE=$CSFY_ECR_BASE_PATH/amp_test:dev-1.0.0 \
            docker compose \
            --file $GIT_ROOT/devops/compose/docker-compose.yml \
            --env-file devops/env/default.env \
            run \
            --rm \
            --name $USER_NAME.amp_test.app.app \
            --entrypoint bash \
            app
        """
        self.check(act, exp)

    @pytest.mark.requires_ck_infra
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(), reason="Only run in amp as submodule"
    )
    def test_docker_bash2(self) -> None:
        """
        Command for docker_bash with entrypoint.
        """
        base_image = ""
        stage = "local"
        version = "1.0.0"
        cmd = "bash"
        print_docker_config = False
        act = hlitadoc._get_docker_compose_cmd(
            base_image,
            stage,
            version,
            cmd,
            print_docker_config=print_docker_config,
        )
        exp = r"""IMAGE=$CSFY_ECR_BASE_PATH/amp_test:local-$USER_NAME-1.0.0 \
                docker compose \
                --file $GIT_ROOT/devops/compose/docker-compose.yml \
                --env-file devops/env/default.env \
                run \
                --rm \
                --name $USER_NAME.amp_test.app.app \
                app \
                bash """
        self.check(act, exp)

    @pytest.mark.requires_ck_infra
    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(), reason="Only run in amp as submodule"
    )
    def test_docker_bash3(self) -> None:
        """
        Command for docker_bash with some env vars.
        """
        base_image = ""
        stage = "local"
        version = "1.0.0"
        cmd = "bash"
        extra_env_vars = ["PORT=9999", "SKIP_RUN=1"]
        print_docker_config = False
        act = hlitadoc._get_docker_compose_cmd(
            base_image,
            stage,
            version,
            cmd,
            extra_env_vars=extra_env_vars,
            print_docker_config=print_docker_config,
        )
        exp = r"""
        IMAGE=$CSFY_ECR_BASE_PATH/amp_test:local-$USER_NAME-1.0.0 \
        PORT=9999 \
        SKIP_RUN=1 \
            docker compose \
            --file $GIT_ROOT/devops/compose/docker-compose.yml \
            --env-file devops/env/default.env \
            run \
            --rm \
            --name $USER_NAME.amp_test.app.app \
            app \
            bash
        """
        self.check(act, exp)

    if False:

        @pytest.mark.skipif(
            not hgit.is_in_amp_as_supermodule(),
            reason="Only run in amp as supermodule",
        )
        def test_docker_bash4(self) -> None:
            base_image = ""
            stage = "dev"
            version = "1.0.0"
            cmd = "bash"
            entrypoint = False
            print_docker_config = False
            act = hlitadoc._get_docker_compose_cmd(
                base_image,
                stage,
                version,
                cmd,
                entrypoint=entrypoint,
                print_docker_config=print_docker_config,
            )
            exp = r"""
            IMAGE=$CSFY_ECR_BASE_PATH/amp_test:dev-1.0.0 \
            docker compose \
            --file $GIT_ROOT/devops/compose/docker-compose.yml \
            --env-file devops/env/default.env \
            run \
            --rm \
            --name $USER_NAME.amp_test.app.app \
            --entrypoint bash \
            app
            """
            self.check(act, exp)

    @pytest.mark.skipif(
        not hgit.is_in_amp_as_submodule(), reason="Only run in amp as submodule"
    )
    def test_docker_jupyter1(self) -> None:
        base_image = ""
        stage = "dev"
        version = "1.0.0"
        port = 9999
        self_test = True
        print_docker_config = False
        act = hlitadoc._get_docker_jupyter_cmd(
            base_image,
            stage,
            version,
            port,
            self_test,
            print_docker_config=print_docker_config,
        )
        exp = r"""
        IMAGE=$CSFY_ECR_BASE_PATH/amp_test:dev-1.0.0 \
        PORT=9999 \
            docker compose \
            --file $GIT_ROOT/devops/compose/docker-compose.yml \
            --env-file devops/env/default.env \
            run \
            --rm \
            --name $USER_NAME.amp_test.jupyter_server_test.app \
            --service-ports \
            jupyter_server_test
        """
        self.check(act, exp)


# #############################################################################


# #############################################################################
# Test_dassert_is_image_name_valid1
# #############################################################################


class Test_dassert_is_image_name_valid1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Check that valid images pass the assertion.
        """
        valid_images = [
            "12345.dkr.ecr.us-east-1.amazonaws.com/amp:dev",
            "abcde.dkr.ecr.us-east-1.amazonaws.com/amp:local-saggese-1.0.0",
            "12345.dkr.ecr.us-east-1.amazonaws.com/amp:dev-1.0.0",
            "sorrentum/cmamp",
        ]
        for image in valid_images:
            hlitadoc.dassert_is_image_name_valid(image)

    def test2(self) -> None:
        """
        Check that invalid images do not pass the assertion.
        """
        invalid_images = [
            # Missing required parts.
            "invalid-image-name",
            # Missing stage/version.
            "12345.dkr.ecr.us-east-1.amazonaws.com/amp:",
            # Invalid version.
            "12345.dkr.ecr.us-east-1.amazonaws.com/amp:prod-1.0.0-invalid",
        ]
        # TODO(gp): Add a check for the output.
        for image in invalid_images:
            with self.assertRaises(AssertionError):
                hlitadoc.dassert_is_image_name_valid(image)


# #############################################################################


# #############################################################################
# Test_dassert_is_base_image_name_valid1
# #############################################################################


class Test_dassert_is_base_image_name_valid1(hunitest.TestCase):

    def test1(self) -> None:
        """
        Check that valid base images pass the assertion.
        """
        valid_base_images = [
            "12345.dkr.ecr.us-east-1.amazonaws.com/amp",
            "sorrentum/cmamp",
            "ghcr.io/cryptokaizen/cmamp",
        ]
        for base_image in valid_base_images:
            hlitadoc._dassert_is_base_image_name_valid(base_image)

    def test2(self) -> None:
        """
        Check that invalid base images do not pass the assertion.
        """
        invalid_base_images = [
            # Missing required parts.
            "invalid-base-image",
            # Extra character at the end.
            "abcde.dkr.ecr.us-east-1.amazonaws.com/amp:",
            # Extra part in the name.
            "ghcr.io/cryptokaizen/cmamp/invalid",
        ]
        for base_image in invalid_base_images:
            with self.assertRaises(AssertionError):
                hlitadoc._dassert_is_base_image_name_valid(base_image)
