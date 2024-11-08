# How to create a super-repo with `helpers`

## Add helpers sub-repo

- Create the super-repo
  ```
  > git clone ...
  ```

- Add `helpers` as sub-repo
  ```bash
  > git submodule add git@github.com:kaizen-ai/helpers.git helpers_root
  > git submodule init
  > git submodule update
  > git add .gitmodules helpers_root
  > git commit -am "Add helpers subrepo" && git push
  ```

## Copy and customize files

- The script `dev_scripts_helpers/thin_client/sync_super_repo.sh`
  allows to vimdiff / cp files across a super-repo and its `helpers` dir
- Conceptually we need to copy and customize the files in
  1) `thin_client` (one can reuse the thin client across repos)
  2) the top dir (to run `pytest`, ...)
  3) `devops` (to build the dev and prod containers)
  4) `.github/workflows` (to run the GitHub regressions)

- After copying the files you can search for the string `xyz` to customize

- If there is a problem with phases 3) and 4) due to the thin environment not
  being completely configured, you can keep moving and then re-run the command
  later

## 1) Copy and customize files in thin_client

- Create the `dev_script` dir based off the template from `helpers`
  ```bash
  # Use a prefix based on the repo name, e.g., `tutorials`, `sports_analytics`.
  > SRC_DIR="dev_scripts_helpers/thin_client"; echo $SRC_DIR
  > DST_PREFIX="xyz"
  > DST_DIR="dev_scripts_${DST_PREFIX}/thin_client"; echo $DST_DIR
  ```

- TODO(gp): When we want to create a new thin env we need to also copy
  `dev_scripts/thin_client/build.py` and `requirements.txt`. Add instructions

- The resulting `dev_script` should look like:
  ```bash
  > ls -1 $DST_DIR
  build.py
  requirements.txt
  setenv.sh
  tmux.py
  ```

## Create the thin environment

- Create the thin environment
  ```
  > $DST_DIR/build.py
  ... ==> `brew cleanup` has not been run in the last 30 days, running now...
  ... Disable this behaviour by setting HOMEBREW_NO_INSTALL_CLEANUP.
  ... Hide these hints with HOMEBREW_NO_ENV_HINTS (see `man brew`).
  14:37:37 - INFO  build.py _main:94                  # gh version=gh version 2.58.0 (2024-10-01)
  https://github.com/cli/cli/releases/tag/v2.58.0
  14:37:37 - INFO  build.py _main:100                 /Users/saggese/src/quant_dashboard1/dev_scripts_quant_dashboard/thin_client/build.py successful
  ```

- Customize the `dev_scripts` dir, if necessary
  ```bash
  > vi $DST_DIR/*
  ```
  - Customize `DIR_TAG`
  - Set `VENV_TAG` to create a new thin environment or reuse an existing one
    (e.g., `helpers`)

## Test the thin environment

- Test `helpers` `setenv.sh`
  ```bash
  > (cd helpers_root; source dev_scripts_helpers/thin_client/setenv.sh)
  ...
  alias w='which'
  INFO: dev_scripts_helpers/thin_client/setenv.sh successful
  ```

- Test super-repo `setenv`
  ```bash
  > source dev_scripts_${DST_PREFIX}/thin_client/setenv.sh
  ...
  alias w='which'
  INFO: dev_scripts_quant_dashboard/thin_client/setenv.sh successful
  ```

## Create the tmux links

- Create the global link
  ```bash
  > ${DST_DIR}/tmux.py --create_global_link
  ...
  ################################################################################
  ln -sf /Users/saggese/src/quant_dashboard1/dev_scripts_quant_dashboard/thin_client/tmux.py ~/go_quant_dashboard.py
  ################################################################################
  14:42:53 - INFO  thin_client_utils.py create_tmux_session:203           Link created: exiting
  ```

- Create the tmux session
  ```bash
  > ${DST_DIR}/tmux.py --index 1 --force_restart
  ```

- You should see the tmux windows with the views on the super repo and the
  subrepo
  - Double check that the `setenv.sh` succeeded in all the windows

- Test `tmux`
  ```bash
  > dev_scripts_sports_analytics/thin_client/tmux.py --create_global_link
  > dev_scripts_sports_analytics/thin_client/tmux.py --index 1
  ```

## Maintain the files in sync with the template

- Check the difference between the super-repo and `helpers`
  ```bash
  > helpers_root/dev_scripts_helpers/thin_client/sync_super_repo.sh
  ```

## 2) Copy and customize files in the top dir

- Some files need to be copied from `helpers` to the root of the super-repo to
  configure various tools (e.g., dev container workflow, `pytest`, `invoke`)
  - `changelog.txt`: this is copied from the repo that builds the used container or
    started from scratch for a new container
  - `conftest.py`: configure `pytest`
  - `pytest.ini`: configure `pytest` preferences
  - `invoke.yaml`: configure `invoke`
  - `repo_config.py`: stores information about this specific repo (e.g., name, used
    container)
    - This needs to be modified
  - `tasks.py`: the `invoke` tasks available in this container
    - This needs to be modified
  - TODO(gp): Some files (e.g., `conftest.py`, `invoke.yaml`) should be links to `helpers`

  ```bash
  > vim changelog.txt conftest.py invoke.yaml pytest.ini repo_config.py tasks.py
  ```

- You can run to copy/diff the files
  ```bash
  > ${TEMPLATE_DIR}/merge.sh
  ```

## 3) Copy and customize files in `devops`

### Build a container for a super-repo

- Copy the `devops` template dir
  ```bash
  > (cd helpers_root; git pull)
  > cp -r helpers_root/devops devops
  ```
- If we don't need to build a container and just we can reuse, then we can delete
  the corresponding `build` directory
  ```bash
  > rm -rf devops/docker_build
  ```

- Follow the instructions in
  docs/work_tools/all.devops_docker.reference.md and
  docs/work_tools/all.devops_docker.how_to_guide.md

- TODO
  - if it's a super-repo container you neeed to switch in devops/docker_run/docker_setenv.sh
  grep IS_SUPER_REPO

- Run the single-arch flow
  ```bash
  > i docker_build_local_image --version 1.0.0 && i docker_tag_local_image_as_dev --version 1.0.0
  > i docker_bash --skip-pull
  > i docker_jupyter
  ```

- Run the multi-arch flow
  ```bash
  > i docker_build_local_image --version 1.0.0 --multi-arch "linux/amd64,linux/arm64"
  > i docker_tag_local_image_as_dev --version 1.0.0
  ```
