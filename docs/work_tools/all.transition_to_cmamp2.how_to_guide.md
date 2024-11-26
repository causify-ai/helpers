# How to switch to cmamp-v2.0

- `cmamp-2.0` brings major changes to our dev and deployment flow

- Changelog
  - Made repos composable by using git subrepos instead of the mono-repo approach
    used until now
    - E.g., `//helpers` is now a subrepo and not a normal dir
    - In this way we can separate multiple applications in different composable
      repos
  - Improved Docker flow where repos and dirs can run in different containers
  - Improved Docker container building flow
    - Switched to Python 3.12
    - Brought all the packages to the newest version, including pandas, numpy, etc.
  - Improved thin client flow and tmux flow
    - It has been almost completely re-written in Python from Bash
  - Improved documentation

- (The whole thing is so fancy, we are writing a paper on our approach).

- Despite the fact that we tested the flows for more than one month across
  different builds (Linux, Mac, GH), there will be certainly be problems for you
  or the build systems, since this is a big change
- You will find more or fewer issues if your flow is different than the official
  one. Be patient, ask for help (kindly), and we will get all your problems
  fixed.

## Patching up an existing client on dev1 or dev2

- You need to patch up your Git client or start from scratch
  ```bash
  > cd /data/saggese/src/cmamp1

  > git checkout master
  # ... It's going to pull a lot of stuff ...

  # Our old friendly dirs are empty.
  > ls helpers/ config/
  ls: config/: No such file or directory
  ls: helpers/: No such file or directory

  # And there is a new friend, but it's still empty.
  > ls helpers_root/

  > git submodule init
  Submodule 'helpers_root' (git@github.com:causify-ai/helpers.git) registered for path 'helpers_root'

  > git submodule update
  Cloning into '/data/saggese/src/cmamp1/helpers_root'...
  Warning: Permanently added 'github.com' (ED25519) to the list of known hosts.
  Submodule path 'helpers_root': checked out '4534c7c3e0157aebc72d7fdc61a297e69cd23cc8'

  # Now `helpers_root` is populated
  > ls helpers_root/
  LICENSE             __init__.py         config_root         dev_scripts_helpers docs                invoke.yaml         pytest.ini          tasks.py
  README.md           changelog.txt       conftest.py         devops              helpers             mypy.ini            repo_config.py
  ```

## Clone Git client from scratch

- If patching up your Git client doesn't work you can take a more destructive
  road and create a new repo

- Push all your local branches remotely, since the Git clients might have issues
- I suggest to rename your Git client to `.old`, e.g., 
  ```
  > mv /data/saggese/cmamp1 /data/saggese/cmamp1.old
  ```

- Then clone the Git from scratch
  ```
  > git clone --recursive ...
  ```

## Fix all env vars

- Your old bash and tmux sessions need to be patched up and then restarted

- To patch up the env vars you can run in every bash:
  ```
  > cd /.../cmamp1
  > ./dev_scripts_cmamp/thin_client/setenv.sh
  ```

- If you are using `tmux` (and you should) you need to restart the dev env
  completely

## Restart tmux system

- E.g., for a client `/data/saggese/src/cmamp1`

- Create a new centralized script to control the different copies of the repos
  ```
  > /data/saggese/src/cmamp1/dev_scripts_cmamp/thin_client/tmux.py --create_global_link
  ##> /data/saggese/src/cmamp1/dev_scripts_cmamp/thin_client/tmux.py
  16:07:44 - INFO  hdbg.py init_logger:1010                               Saving log to file '{'/data/saggese/src/cmamp1/helpers_root/dev_scripts_helpers/thin_client/thin_client_utils.py.log'}'
  16:07:44 - INFO  hdbg.py init_logger:1015                               > cmd='/data/saggese/src/cmamp1/dev_scripts_cmamp/thin_client/tmux.py --create_global_link'
  16:07:44 - INFO  thin_client_utils.py create_tmux_session:199           Creating the global link
  ################################################################################
  ln -sf /data/saggese/src/cmamp1/dev_scripts_cmamp/thin_client/tmux.py ~/go_cmamp.py
  ################################################################################
  16:07:44 - INFO  thin_client_utils.py create_tmux_session:203           Link created: exiting
  ```

- Start a new session for the client 1 of `cmamp`
  ```
  > /data/saggese/src/cmamp1/dev_scripts_cmamp/thin_client/tmux.py --index1
  ```

## Check that the new Docker container works

- Pull the new container

  ```bash
  > i docker_pull
  # This should pull a new image from the repo and should take a bit of time
  ```

- Test the new container
  ```
  > i docker_bash
  16:14:49 - INFO  hdbg.py init_logger:1015                               > cmd='/data/saggese/src/venv/client_venv.helpers/bin/invoke docker_bash'
  ## docker_bash:
  16:14:49 - INFO  lib_tasks_docker.py docker_pull:246                    Pulling the latest version of Docker
  ## docker_pull:
  ## docker_login:
  ## _docker_login_ecr:
  16:14:49 - INFO  lib_tasks_docker.py _docker_login_ecr:350              Logging in to the target registry
    ... WARNING! Using --password via the CLI is insecure. Use --password-stdin.
    ... Login Succeeded
  16:14:53 - INFO  lib_tasks_docker.py _docker_pull:233                   image='623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev'
  docker pull 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev
  dev: Pulling from cmamp
  Digest: sha256:68a1c9dfe5ec8a22f2e86ed13642422c5ca7abd886deb40637314805aa35af9c
  Status: Image is up to date for 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev
  623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev

  What's Next?
    View a summary of image vulnerabilities and recommendations → docker scout quickview 623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev
  IMAGE=623860924167.dkr.ecr.eu-north-1.amazonaws.com/cmamp:dev \
          docker compose \
          --file /data/saggese/src/cmamp1/devops/compose/docker-compose.yml \
          --env-file devops/env/default.env \
          run \
          --rm \
          --name saggese.cmamp.app.cmamp1.20241110_111449 \
          --user $(id -u):$(id -g) \
          app \
          bash
  WARN[0000] The "AM_FORCE_TEST_FAIL" variable is not set. Defaulting to a blank string.
  WARN[0000] The "CK_AWS_ACCESS_KEY_ID" variable is not set. Defaulting to a blank string.
  WARN[0000] The "CK_AWS_DEFAULT_REGION" variable is not set. Defaulting to a blank string.
  WARN[0000] The "CK_AWS_SECRET_ACCESS_KEY" variable is not set. Defaulting to a blank string.
  WARN[0000] The "CK_TELEGRAM_TOKEN" variable is not set. Defaulting to a blank string.
  WARN[0000] /data/saggese/src/cmamp1/devops/compose/docker-compose.yml: `version` is obsolete
  WARN[0000] Found orphan containers ([compose-im_postgres3923-1 compose-im_postgres5173-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
  IS_SUPER_REPO=1
  ##> devops/docker_run/entrypoint.sh
  UID=501
  GID=20
  GIT_ROOT_DIR=/app
  > source /app/helpers_root/dev_scripts_helpers/thin_client/thin_client_utils.sh ...
  AM_CONTAINER_VERSION='2.0.0'
  IS_SUPER_REPO=1
  ##> devops/docker_run/docker_setenv.sh
  GIT_ROOT_DIR=/app
  > source /app/helpers_root/dev_scripts_helpers/thin_client/thin_client_utils.sh ...
  # Activate environment ...
  # Activate environment ... done
  # Set PATH
  PATH=.:./dataflow:./reconciliation:./oms:./ck_web_apps:./dataflow_amp:./devops:./core:./test:./.pytest_cache:./optimizer:./papers:./market_data:./research_amp:./ck.infra:./docker_common:./ck.marketing:./docs:./ck.alembic:./helpers_root:./dev_scripts:./dev_scripts_cmamp:./.github:./im_v2:./sorrentum_sandbox:./im:./mkdocs:./.git:./pnl_web_app:./ck_marketing:./defi:./data_schema:./.idea:/app:/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  # Set PYTHONPATH
  PYTHONPATH=/app:
  # Configure env
  git --version: git version 2.43.0
  /app
  PATH=.:./dataflow:./reconciliation:./oms:./ck_web_apps:./dataflow_amp:./devops:./core:./test:./.pytest_cache:./optimizer:./papers:./market_data:./research_amp:./ck.infra:./docker_common:./ck.marketing:./docs:./ck.alembic:./helpers_root:./dev_scripts:./dev_scripts_cmamp:./.github:./im_v2:./sorrentum_sandbox:./im:./mkdocs:./.git:./pnl_web_app:./ck_marketing:./defi:./data_schema:./.idea:/app:/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  PYTHONPATH=/app/helpers_root:/app:
  entrypoint.sh: 'bash'
  ```
- Note that starting a container should be much faster than what it used to

- Run `pytest`
  ```bash
  docker> pytest
  ```
