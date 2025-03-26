#!/bin/bash -xe

# Replace the following:
# rconf.get_docker_base_image_name() -> hrecouti.get_repo_config().get_docker_base_image_name()
# henv.execute_repo_config_code("get_name()") -> hrecouti.get_repo_config().get_name()
# henv.execute_repo_config_code("get_html_bucket_path()") -> hrecouti.get_repo_config().get_html_bucket_path()
# henv.execute_repo_config_code("get_html_dir_to_url_mapping()") -> hrecouti.get_repo_config().get_html_dir_to_url_mapping()
# henv.execute_repo_config_code("get_unit_test_bucket_path()") -> hrecouti.get_repo_config().get_unit_test_bucket_path()
# henv.execute_repo_config_code("get_docker_base_image_name()") -> hrecouti.get_repo_config().get_docker_base_image_name()
# henv.execute_repo_config_code("get_repo_map()") -> hrecouti.get_repo_config().get_repo_map()
# henv.execute_repo_config_code("get_extra_amp_repo_sym_name()") -> hrecouti.get_repo_config().get_extra_amp_repo_sym_name()
# henv.execute_repo_config_code("get_host_name()") -> hrecouti.get_repo_config().get_host_name()
# henv.execute_repo_config_code("get_invalid_words()") -> hrecouti.get_repo_config().get_invalid_words()
# henv.execute_repo_config_code("get_shared_data_dirs()") -> hserver.get_shared_data_dirs()
# henv.execute_repo_config_code("has_dind_support()") -> hserver.has_dind_support()
# henv.execute_repo_config_code("use_docker_sibling_containers()") -> hserver.use_docker_sibling_containers()
# henv.execute_repo_config_code("use_main_network()") -> hserver.use_main_network()
# henv.execute_repo_config_code("use_docker_db_container_name_to_connect()") -> hserver.use_docker_db_container_name_to_connect()
# henv.execute_repo_config_code("enable_privileged_mode()") -> hserver.enable_privileged_mode()
# henv.execute_repo_config_code("use_docker_network_mode_host()") -> hserver.use_docker_network_mode_host()
# henv.execute_repo_config_code("get_docker_user()") -> hserver.get_docker_user()
# henv.execute_repo_config_code("get_docker_shared_group()") -> hserver.get_docker_shared_group()
# henv.execute_repo_config_code("skip_submodules_test()") -> hserver.skip_submodules_test()
# henv.execute_repo_config_code("is_CK_S3_available()") -> hserver.is_CK_S3_available()
# henv.execute_repo_config_code("config_func_to_str()") -> hserver.config_func_to_str()
# henv.execute_repo_config_code("has_docker_sudo()") -> hserver.has_docker_sudo()
# henv.execute_repo_config_code("_is_mac_version_with_sibling_containers()") -> hserver._is_mac_version_with_sibling_containers()
# henv.execute_repo_config_code("run_docker_as_root()") -> hserver.run_docker_as_root()

# We need to execlude the file that we are running this script on,
# otherwise it will be replaced with the new values.
find . -type f \( -name "*.py" -o -name "*.sh" \) -not -name "HelpersTask88_Improve_repo_config.sh" -exec perl -i -pe '
s/rconf\.get_docker_base_image_name\(\)/hrecouti.get_repo_config().get_docker_base_image_name()/g;
s/henv\.execute_repo_config_code\("get_name\(\)"\)/hrecouti.get_repo_config().get_name()/g;
s/henv\.execute_repo_config_code\("get_html_bucket_path\(\)"\)/hrecouti.get_repo_config().get_html_bucket_path()/g;
s/henv\.execute_repo_config_code\("get_html_dir_to_url_mapping\(\)"\)/hrecouti.get_repo_config().get_html_dir_to_url_mapping()/g;
s/henv\.execute_repo_config_code\("get_unit_test_bucket_path\(\)"\)/hrecouti.get_repo_config().get_unit_test_bucket_path()/g;
s/henv\.execute_repo_config_code\("get_docker_base_image_name\(\)"\)/hrecouti.get_repo_config().get_docker_base_image_name()/g;
s/henv\.execute_repo_config_code\("get_repo_map\(\)"\)/hrecouti.get_repo_config().get_repo_map()/g;
s/henv\.execute_repo_config_code\("get_extra_amp_repo_sym_name\(\)"\)/hrecouti.get_repo_config().get_extra_amp_repo_sym_name()/g;
s/henv\.execute_repo_config_code\("get_host_name\(\)"\)/hrecouti.get_repo_config().get_host_name()/g;
s/henv\.execute_repo_config_code\("get_invalid_words\(\)"\)/hrecouti.get_repo_config().get_invalid_words()/g;
s/henv\.execute_repo_config_code\("get_shared_data_dirs\(\)"\)/hserver.get_shared_data_dirs()/g;
s/henv\.execute_repo_config_code\("has_dind_support\(\)"\)/hserver.has_dind_support()/g;
s/henv\.execute_repo_config_code\("use_docker_sibling_containers\(\)"\)/hserver.use_docker_sibling_containers()/g;
s/henv\.execute_repo_config_code\("use_main_network\(\)"\)/hserver.use_main_network()/g;
s/henv\.execute_repo_config_code\("use_docker_db_container_name_to_connect\(\)"\)/hserver.use_docker_db_container_name_to_connect()/g;
s/henv\.execute_repo_config_code\("enable_privileged_mode\(\)"\)/hserver.enable_privileged_mode()/g;
s/henv\.execute_repo_config_code\("use_docker_network_mode_host\(\)"\)/hserver.use_docker_network_mode_host()/g;
s/henv\.execute_repo_config_code\("get_docker_user\(\)"\)/hserver.get_docker_user()/g;
s/henv\.execute_repo_config_code\("get_docker_shared_group\(\)"\)/hserver.get_docker_shared_group()/g;
s/henv\.execute_repo_config_code\("skip_submodules_test\(\)"\)/hserver.skip_submodules_test()/g;
s/henv\.execute_repo_config_code\("is_CK_S3_available\(\)"\)/hserver.is_CK_S3_available()/g;
s/henv\.execute_repo_config_code\("config_func_to_str\(\)"\)/hserver.config_func_to_str()/g;
s/henv\.execute_repo_config_code\("has_docker_sudo\(\)"\)/hserver.has_docker_sudo()/g;
s/henv\.execute_repo_config_code\("_is_mac_version_with_sibling_containers\(\)"\)/hserver._is_mac_version_with_sibling_containers()/g;
s/henv\.execute_repo_config_code\("run_docker_as_root\(\)"\)/hserver.run_docker_as_root()/g;
s/^import repo_config as rconf\s*$//g
' {} \;
