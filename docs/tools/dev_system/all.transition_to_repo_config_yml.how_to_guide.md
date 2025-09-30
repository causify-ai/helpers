<!-- toc -->

- [How to switch from `repo_config.py` to `repo_config.yml`](#how-to-switch-from-repo_configpy-to-repo_configyml)
  * [Patching up an existing repo](#patching-up-an-existing-repo)

<!-- tocstop -->

# How to switch from `repo_config.py` to `repo_config.yml`

- Design choice is discussed in
  [Managing repo configurations](/docs/tools/dev_system/all.runnable_repo.reference.md#managing-repo-configurations)

- Changelog
  - The `repo_config.py` is removed in favor of `repo_config.yml`
  - The `henv.execute_repo_config_code("func")` layer here is also completely
    removed in favor of direct access to the config either through the interface
    from `hserver` (for server related config) or `repo_config_utils` (for repo
    related config)
  - Some config variables are also moved between `repo_config` and `hserver` for
    better organization and reflection of their purposes
  - The `IS_SUPER_REPO` variable is renamed to `USE_HELPERS_AS_NESTED_MODULE`
    for better clarity
  - Files with identical content are replaced with symbolic links to their
    counterparts in the //helpers

## Patching up an existing repo

- Copy the new `repo_config.yml` template from //helpers

  ```bash
  cp ./helpers_root/repo_config.yaml .
  # Modify the values to match the setting in the current `repo_config.py`
  ```

- Remove the old `repo_config.py` file

  ```bash
  > rm repo_config.py
  ```

- Copy the updated `setenv.sh` script from //helpers

  ```bash
  cp ./helpers_root/dev_scripts_helpers/thin_client/setenv.sh ./dev_scripts_cmamp/thin_client/setenv.sh
  ```

- Replace `setenv.sh` file with symoblic link reference to the file in //helpers
  - Except for when amp is the first level submodule (instead of //helpers). See
    CmampTask11623
    - TODO (heanh): Generalize amp path resolution in setenv.sh when amp is the
      first level submodule (CmampTask11623)

  ```bash
  python3 ./helpers_root/helpers/create_links.py --src_dir ./helpers_root/dev_scripts_helpers/thin_client --dst_dir ./dev_scripts_cmamp/thin_client --replace_links --use_relative_paths
  ```

- Replace all references of `henv.execute_repo_config_code` and `rconf` to their
  corresponding functions in either `hrecouti.get_repo_config()` or `hserver`
  - For example,
    - `rconf.get_docker_base_image_name()` ->
      `hrecouti.get_repo_config().get_docker_base_image_name()`
    - `henv.execute_repo_config_code("get_html_bucket_path()")` ->
      `hrecouti.get_repo_config().get_html_bucket_path()`
    - `henv.execute_repo_config_code("is_CK_S3_available()")` ->
      `hserver.is_CK_S3_available()`
  - While the following script helps automate the replacement, it's worth to
    double check that all the references are correctly replaced.
    ```bash
    > ./helpers_root/dev_scripts_helpers/cleanup_scripts/HelpersTask88_Improve_repo_config.sh
    ```
  - Import statements in the modified files will need to be added or updated as
    well

- Rename `IS_SUPER_REPO` to `USE_HELPERS_AS_NESTED_MODULE`
  - While the following script helps automate the replacement, it's worth to
    double check that all the references are correctly replaced.
    ```bash
    > ./helpers_root/dev_scripts_helpers/cleanup_scripts/HelpersTask135_Rename_IS_SUPER_REPO_var.sh
    ```

- Replace identical files with symbolic links to their counterparts in //helpers
  ```bash
  python3 ./helpers_root/helpers/create_links.py --src_dir ./helpers_root/ --dst_dir . --replace_links --use_relative_paths
  ```
