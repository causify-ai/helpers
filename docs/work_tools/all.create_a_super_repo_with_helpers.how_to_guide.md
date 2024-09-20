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

- To configure a super-repo, conceptually we need to copy from `helpers`
  and customize for the super-repo
  1) the files in `dev_scripts/thin_client` (to run tmux, setenv.sh)
  2) the files in the top dir
  3) the files in `devops`
  3) the files in `.github`

- The script `dev_scripts_helpers/thin_client/sync_super_repo.sh`
  allows to vimdiff / cp files across a super-repo and its `helpers` dir
- From a super repo the path is 
  `./helpers_root/dev_scripts_helpers/thin_client/sync_super_repo.sh`

- After copying the files you can search for the string `xyz` to customize
  the files

### 1) Copy and customize files in `thin_client`

- Create the `dev_script` dir based off the template from `helpers`
  ```bash
  # Use a prefix based on the repo name, e.g., `tutorials`, `sports_analytics`.
  > DST_PREFIX="sports_analytics"
  > DST_DIR="dev_scripts_${DST_PREFIX}/thin_client"; echo $DST_DIR; ls $DST_DIR
  ...
  ```

- TODO(gp): When we want to create a new thin env we need to also copy
  `dev_scripts/thin_client/build.py` and `requirements.txt`. Add instructions

- The resulting `dev_script` should look like:
  ```bash
  > ls -1 $DST_DIR
  dev_scripts_sports_analytics/thin_client/setenv.sh
  dev_scripts_sports_analytics/thin_client/tmux.py
  ```

- Customize the `dev_scripts` dir
  ```bash
  > vi $DST_DIR/*
  ```
  - Customize `DIR_TAG`
  - Set `VENV_TAG` to create a new thin environment or reuse an existing one
    (e.g., `helpers`)

### Tmux links

- Create the global link
  ```bash
  > ${DST_DIR}/tmux.py --create_global_link
  ```

- Create the tmux session
  ```bash
  > ${DST_DIR}/tmux.py --index 1 --force_restart
  ```

### How to test

- Test `helpers` `setenv.sh`
  ```bash
  > (cd helpers_root; source dev_scripts_helpers/thin_client/setenv.sh)
  ```

- Test super-repo `setenv`
  ```bash
  > source dev_scripts_sports_analytics/thin_client/setenv.sh
  ```

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

# Create a releasable dir

```
> mkdir dir
> cd dir
> cp -r ../helpers_root/devops .
```
