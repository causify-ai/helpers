

<!-- toc -->

- [Creating a new repository from the web UI](#creating-a-new-repository-from-the-web-ui)
- [Set up the repo locally](#set-up-the-repo-locally)
- [Transfer required files from other repos](#transfer-required-files-from-other-repos)
- [Confirm that the development set up works](#confirm-that-the-development-set-up-works)
- [File a PR and merge it into `master`](#file-a-pr-and-merge-it-into-master)

<!-- tocstop -->

This a document that helps organization admins to set up a new GH repo.

# Creating a new repository from the web UI

TODO(Grisha): consider using repository
[templates](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)

- Create a repo within the [`causify-ai`
  organization](https://github.com/causify-ai)
- Follow the
  [offical guide](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository#creating-a-new-repository-from-the-web-ui)
- Recommended options:
  - Owner: `causify-ai`
  - Repository-name: provide a valid short name, e.g., `algo_trading`
  - Visibility: by default choose `Private`
  - Add a README file
  - `.gitignore template: None`
  - License: `General Public Licenve v3.0`

# Set up the repo locally

Skip steps 3-5 in case you don't want to add an existing repo as a submodule.

1. Clone the repository locally
   ```bash
   > git clone --recursive git@github.com:causify-ai/{repo_name}.git ~/src/{repo_name}{index}
   ```
2. Checkout to a new branch
   ```
   > git checkout -b repo_init
   ```
3. Add a submodule
   ```bash
   # In general form.
   > git submodule add {submodule_url} {submodule_path}
   # Example for `cmamp`.
   > git submodule add git@github.com:causify-ai/cmamp.git amp
   # The cmd will create a `.gitsubmodules` file that we need to check-in.
   [submodule "amp"]
   path = amp
   url = git@github.com:causify-ai/cmamp.git
   ```
4. Init submodules within the added submodule. This is needed when the added
   submodule contains another submodule inside. E.g., `amp` is a submodule level
   1, but it also contains `helpers_root` as submodule level 2
   ```bash
   > cd {submodule_level_1}
   > git submodule init
   > git submodule update
   > cd {submodule_level_2}
   > git checkout master
   > git pull
   ```
5. Commit and push the changes
   ```
   > git add -u
   > git commit -m "add sumbodules"
   > git push
   ```

# Transfer required files from other repos

Prerequisite:

- You have a local copy of `cmamp` and `orange`. We use `cmamp` as a "base" repo
  and `orange` as an example of a repo with `cmamp` as submodule
- You are on a feature branch

Example for a repo with `cmamp` as submodule:

1. Copy `repo_config.py` from `orange` into the current repo and change
   `_REPO_NAME = "orange"` to the current repo name
2. Copy `tasks.py` from `orange` into the current repo
3. Copy `pytest.ini` from `orange` into the current repo
4. Create soft links for the following files:
   ```bash
   > ln -s amp/conftest.py conftest.py
   > ln -s amp/invoke.yaml invoke.yaml
   > ln -s amp/mypy.ini mypy.ini
   > ln -s amp/changelog.txt changelog.txt
   ```
5. Copy the entire `devops` dir from `orange` into the current repo
6. Copy `dev_scripts_orange/thin_client` into the current repo
   - Rename the dir like so `dev_scripts_orange` -> `dev_scripts_{repo_name}`
   - Transfer files from `dev_scripts_orange/thin_client` to
     `dev_scripts_{repo_name}/thin_client`
   - In `dev_scripts_{repo_name}/thin_client/setenv.sh` replace
     `DIR_TAG="orange"` with `DIR_TAG="{repo_name}"`
   - In `dev_scripts_order_execution/thin_client/tmux.py` replace
     `dir_prefix = "order_execution"` with `dir_prefix = "{repo_name}"`
7. Copy `.gitignore` from `orange` into the current repo
8. Copy `/test` folder from `orange` into the current repo
   - Rename `test/test_repo_config_orange.py` to
     `test/test_repo_config_{repo_name}.py`
     - Replace `orange` with the {repo_name} inside the file
9. Commit and push the changes
   ```
   # Add files/dirs one-by-one.
   > git add {file_name}
   > git commit -m "add files"
   > git push
   ```

# Confirm that the development set up works

Follow
[the on-boarding](/docs/onboarding/ck.development_setup.how_to_guide.md#begin-working)
doc to confirm.

# File a PR and merge it into `master`

Self-explanatory (hopefully).
