

<!-- toc -->

- [How to create a super-repo with `helpers`](#how-to-create-a-super-repo-with-helpers)
  * [Create a new (super) repo in the desired organization](#create-a-new-super-repo-in-the-desired-organization)
  * [Add helpers sub-repo](#add-helpers-sub-repo)
  * [Copy and customize files](#copy-and-customize-files)
  * [1) Copy and customize files in `thin_client`](#1-copy-and-customize-files-in-thin_client)
    + [Create the thin environment](#create-the-thin-environment)
    + [Test the thin environment](#test-the-thin-environment)
    + [Create the tmux links](#create-the-tmux-links)
    + [Maintain the files in sync with the template](#maintain-the-files-in-sync-with-the-template)
  * [2) Copy and customize files in the top dir](#2-copy-and-customize-files-in-the-top-dir)
  * [3) Copy and customize files in `devops`](#3-copy-and-customize-files-in-devops)
    + [Build a container for a super-repo](#build-a-container-for-a-super-repo)
    + [Check if the regressions are passing](#check-if-the-regressions-are-passing)
  * [Configure regressions via GitHub actions](#configure-regressions-via-github-actions)
    + [Set repository secrets/variables](#set-repository-secretsvariables)
    + [Create GitHub actions workflow files](#create-github-actions-workflow-files)
  * [Configure GitHub repo](#configure-github-repo)

<!-- tocstop -->

# How to create a super-repo with `helpers`

## Create a new (super) repo in the desired organization

- E.g. https://github.com/organizations/causify-ai/repositories/new
  - The repository is set to private by default

## Add helpers sub-repo

- Clone the super-repo locally
  ```
  > git clone git@github.com:causify-ai/repo_name.git ~/src/repo_name1
  ```

- Add `helpers` as sub-repo

  ```bash
  > cd ~/src/repo_name1
  > git submodule add git@github.com:causify-ai/helpers.git helpers_root
  > git submodule init
  > git submodule update
  > git add .gitmodules helpers_root
  > git commit -am "Add helpers subrepo" && git push
  ```

- In one line:
  ```bash
  > git submodule add git@github.com:causify-ai/helpers.git helpers_root && git submodule init && git submodule update && (cd helpers_root && git checkout master && git pull) && git add .gitmodules helpers_root
  ```

## Copy and customize files

- Conceptually we need to copy and customize the files in

  1. `thin_client` (one can reuse the thin client across repos)
  2. The top dir (to run `pytest`, ...)
  3. `devops` (to build the dev and prod containers)
  4. `.github/workflows` (to run the GitHub regressions)

- After copying the files you can search for the string `xyz` to customize

- If there is a problem with phases 3) and 4) due to the thin environment not
  being completely configured, you can keep moving and then re-run the command
  later

- You can follow the directions to perform the step manually or run the script
  `dev_scripts_helpers/thin_client/sync_super_repo.sh` which allows to vimdiff /
  cp files across a super-repo and its `helpers` dir

## 1) Copy and customize files in `thin_client`

- Create the `dev_script` dir based off the template from `helpers`

  ```bash
  # Use a prefix based on the repo name, e.g., `tutorials`, `sports_analytics`.
  > SRC_DIR="helpers_root/dev_scripts_helpers/thin_client"; ls $SRC_DIR
  > DST_PREFIX="xyz"
  > DST_DIR="dev_scripts_${DST_PREFIX}/thin_client"; echo $DST_DIR
  > mkdir -p $DST_DIR
  > cp -r $SRC_DIR/{build.py,requirements.txt,setenv.sh,tmux.py} $DST_DIR
  ```

- The resulting `dev_script` should look like:

  ```bash
  > ls -1 $DST_DIR
  build.py
  requirements.txt
  setenv.sh
  tmux.py
  ```

- Customize the files looking for `$DIR_TAG` and `$IS_SUPER_REPO`
  ```
  > vi $DST_DIR/*
  ```

- If we don't need to create a new thin env you can delete the files
  `dev_scripts/thin_client/build.py` and `requirements.txt`

### Create the thin environment

> cp -r $SRC_DIR/{build.py,requirements.txt,setenv.sh,tmux.py} $DST_DIR

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

### Test the thin environment

- Test `//helpers` `setenv.sh`

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

### Create the tmux links

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

### Maintain the files in sync with the template

- Check the difference between the super-repo and `helpers`
  ```bash
  > helpers_root/dev_scripts_helpers/thin_client/sync_super_repo.sh
  ```

## 2) Copy and customize files in the top dir

- Some files need to be copied from `helpers` to the root of the super-repo to
  configure various tools (e.g., dev container workflow, `pytest`, `invoke`)
  - `changelog.txt`: this is copied from the repo that builds the used container
    or started from scratch for a new container
  - `conftest.py`: configure `pytest`
  - `pytest.ini`: configure `pytest` preferences
  - `invoke.yaml`: configure `invoke`
  - `repo_config.py`: stores information about this specific repo (e.g., name,
    used container)
    - This needs to be modified
  - `tasks.py`: the `invoke` tasks available in this container
    - This needs to be modified
  - TODO(gp): Some files (e.g., `conftest.py`, `invoke.yaml`) should be links to
    `helpers`

  ```bash
  > cp helpers_root/{changelog.txt,conftest.py,invoke.yaml,pytest.ini,repo_config.py,tasks.py} .
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
- If we don't need to build a container and just we can reuse, then we can
  delete the corresponding `build` directory

  ```bash
  > rm -rf devops/docker_build
  ```

- Follow the instructions in `docs/work_tools/all.devops_docker.reference.md`
  and `docs/work_tools/all.devops_docker.how_to_guide.md`

- TODO
  - If it's a super-repo container you need to switch in
    devops/docker_run/docker_setenv.sh grep IS_SUPER_REPO

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

- If you wish to push the dev image to a remote registry, contact the infra team
  to add new registry with default settings
  - Make sure the registry name matches the repo name for consistency
  - By default we add new containers to Stockholm region (`eu-north-1`)

### Check if the regressions are passing

- Run the tests, if needed
  ```bash
  > i docker_bash
  > pytest
  ```

## Configure regressions via GitHub actions

### Set repository secrets/variables

- Some secrets/variables are shared in an organization wide storage
  - E.g. for [Causify](https://github.com/organizations/causify-ai) at
    https://github.com/organizations/causify-ai/settings/secrets/actions
  - These values are shared across all repos in the organization so we don't
    need to create them on a per-repo basis
    - The access method is the same as for per-repo variables - via actions
      context `${{ secrets.MY_TOKEN }}` or ``${{ vars.MY_TOKEN }}`
  - Once a `secret` is set it's read-only for everybody. To preview all of the
    raw values that are currently used, visit
    [1password > Shared vault > Causify org GH actions secrets](https://causify.1password.com/app#/everything/AllItems/ofre2i2yhv2lyf7ggvv2a4uouaaxvzjzaomv3hol24txn2an5imq)

- Before adding a new secret/variables for a repo, consider the following:
  - If it's already present in the global storage for an organization, no action
    is required
  - If it's not, check if the newly added value is not needed in all of the
    repos, if so, add it to the global storage to facilitate reusability
    - If you lack permissions for this operation, contact your TL

- Should a repo need some additional secret values/variables, follow the
  procedure below

1. Login to 1password https://causify.1password.com/home
   - Ask your TL if you don't have access to 1password
2. Navigate to the `Shared Vault`
3. Search for `Github actions secrets JSON` secret
4. Copy the JSON from 1password to a temporary local file `vars.json`
5. Run the script to set the secrets/variables
   ```bash
   > cd ~/src/<REPO_NAME>
   > ./helpers_root/dev_scripts_helpers/github/set_secrets_and_variables.py \
        --file `vars.json' \
        --repo '<ORG_NAME>/<REPO_NAME>'
   ```
6. Make sure not to commit the raw `vars.json` file or the
   `dev_scripts_helpers/github/set_secrets_and_variables.py.log` file

- Delete those files locally

### Create GitHub actions workflow files

1. Create a directory `./github/workflows` in the super-repo
2. Copy an example flow from helpers
   - E.g. `helpers_root/.github/workflows/fast_tests.yml
   - Modify it based on your needs
     - Find and replace mentions of `helpers` with the name of super repo for
       consistency
     - Replace `invoke run_fast_tests` with your desired action

3. TODO(Shayan): #HelpersTask90

## Configure GitHub repo

**Disclaimer**: the following set-up requires paid GitHub version
(Pro/Team/Enterprise)

1. Set-up branch protection rule for master

- Navigate to `https://github.com/<your org>/<<your-repo>>/settings/branches`
- Click "Add rule"
  - Specify branch name pattern `master`
  - Check the following options:
    - `Require a pull request before merging` (do not check the sub-options)
    - `Require status checks to pass before merging`
      - Check the `Require branches to be up to date before merging` sub-option
      - In the `Status checks that are required` table specify the workflows you
        want to pass before merging each PR
        - Depends on which workflows were set-up in the step above
        - Usually its `run_fast_tests` and `run_slow_tests`
    - `Require conversation resolution before merging`
  - Click "Save changes" button
