# How to create a super-repo with `helpers`

## Add helpers subrepo

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

## Create build, setenv, and tmux flow

- Create the `dev_script` dir based off the template from `helpers`
  ``` bash
  > TEMPLATE_DIR="helpers_root/dev_scripts/thin_client/templates"
  > ls -1 $TEMPLATE_DIR
  __init__.py
  setenv.template.sh
  tmux.template.py

  # Use a prefix based on the repo name, e.g., `tutorials`, `sports_analytics`.
  > PREFIX="sports_analytics"
  > DST_DIR="dev_scripts_${PREFIX}/thin_client"; echo $DST_DIR
  > mkdir -p $DST_DIR
  > ls helpers_root/dev_scripts/thin_client/templates/
  > cp -r ${TEMPLATE_DIR}/setenv.template.sh ${DST_DIR}/setenv.${PREFIX}.sh
  > cp -r ${TEMPLATE_DIR}/tmux.template.py ${DST_DIR}/tmux.${PREFIX}.py
  ```

- TODO(gp): When we want to create a new thin env we need to also copy
  `dev_scripts/thin_client/build.py` and `requirements.txt`. Add instructions

- The resulting `dev_script` should look like:
  ```bash
  > ls -1 $DST_DIR
  dev_scripts_sports_analytics/thin_client/setenv.sports_analytics.sh
  dev_scripts_sports_analytics/thin_client/tmux.sports_analytics.py
  ```

- Customize the `dev_scripts` dir
  ```bash
  > vi $DST_DIR/*
  ```
  - Customize `DIR_TAG`
  - Set `VENV_TAG` to create a new thin environment or reuse an existing one
    (e.g., `helpers`)

## How to test setenv

- Make sure the setenv works
  ```bash
  > source ${DST_DIR}/setenv.${PREFIX}.sh
  # E.g., `source dev_scripts_sports_analytics/thin_client/setenv.sports_analytics.sh`
  ```

## Tmux links

- Create the global link
  ```bash
  > ${DST_DIR}/tmux.${PREFIX}.py --create_global_link
  ```

- Create the tmux session
  ```bash
  > ${DST_DIR}/tmux.${PREFIX}.py --index 1 --force_restart
  ```

## Maintain the files in sync with the template

- Keep files in sync between `helpers`, template, and a super-repo
  ```bash
  > ${TEMPLATE_DIR}/merge.sh
  ```

- The script conceptually does:
  ```bash
  > vimdiff ${TEMPLATE_DIR}/setenv.template.sh ${DST_DIR}/setenv.${PREFIX}.sh
  > vimdiff ${TEMPLATE_DIR}/tmux.template.py ${DST_DIR}/tmux.${PREFIX}.py
  > vimdiff ${TEMPLATE_DIR}/setenv.template.sh dev_scripts/thin_client/setenv.helpers.sh
  > vimdiff ${TEMPLATE_DIR}/tmux.template.py dev_scripts/thin_client/tmux.helpers.py
  ```

## Create files

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
  - TODO(gp): Some (e.g., `conftest.py`, `invoke.yaml`) should be links to `helpers`

  ```bash
  > vim changelog.txt conftest.py invoke.yaml pytest.ini repo_config.py tasks.py
  ```

- You can run to copy/diff the files
  ```bash
  > ${TEMPLATE_DIR}/merge.sh
  ```

## Build a container for a super-repo

- Copy the `devops` template dir
  ```bash
  > (cd helpers_root; git pull)
  > cp -r helpers_root/devops/templates/devops_with_build_stage devops
  ```
- If we don't need to build a container, but just reuse one we can delete
  the corresponding directory
  ```bash
  > rm -rf devops/docker_build
  ```
