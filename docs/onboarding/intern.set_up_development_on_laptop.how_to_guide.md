<!-- toc -->

- [Set up development environment locally](#set-up-development-environment-locally)
  * [Clone the code](#clone-the-code)
  * [Set up GitHub SSH access and personal access token (PAT)](#set-up-github-ssh-access-and-personal-access-token-pat)
  * [Build and activate the thin environment](#build-and-activate-the-thin-environment)
  * [Install and test Docker](#install-and-test-docker)
    + [Supported OS](#supported-os)
    + [Install Docker](#install-docker)
    + [Checking Docker installation](#checking-docker-installation)
    + [Docker installation troubleshooting](#docker-installation-troubleshooting)
  * [Tmux](#tmux)
  * [Shell support](#shell-support)
  * [Some useful workflows](#some-useful-workflows)
  * [Hack: use a local container if needed](#hack-use-a-local-container-if-needed)

<!-- tocstop -->

# Set up development environment locally

- One only develops locally on their laptop during the intern stage. All
  permanent members of the team should develop on our server. Interns will get
  access to the server once they "graduate" to a permanent position.

## Clone the code

- To clone the repo, use the cloning command described in the official GitHub
  documentation

- Example of the cloning command:

  ```bash
  > git clone --recursive git@github.com:causify-ai/{repo_name}.git ~/src/{repo_name}1
  ```
  - The previous command might not work sometimes, in which case try the
    alternative command using HTTP instead of SSH:

  ```bash
  > git clone --recursive https://github.com/causify-ai/{repo_name}.git ~/src/{repo_name}1
  ```

- All the source code should go under `~/src` (e.g., `/Users/<YOUR_USER>/src` on
  a Mac)
- The path to the local repo folder should look like this
  `~/src/{REPO_NAME}{IDX}` where
  - `REPO_NAME` is a name of the repository
  - IDX is an integer

## Set up GitHub SSH access and personal access token (PAT)

- To generate a new SSH key, follow the official
  [GitHub instructions](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

- Ensure that you save the SSH key with the below name format and at the
  specified location

  File location: `~/.ssh/id_rsa.causify-ai.github`

  Example command to generate SSH key:

  ```bash
  > ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_rsa.causify-ai.github
  ```

- To create a Personal Access Token (classic) with necessary scopes like `repo`,
  `workflow`, etc., go to
  [https://github.com/settings/tokens](https://github.com/settings/tokens) and
  click "Generate new token (classic)".

- After obtaining the token, store it in a file named
  `github_pat.causify-ai.txt` at the specified path

  File location: `~/.ssh/github_pat.causify-ai.txt`

  Example command to save using `vim`:

  ```bash
  > vim ~/.ssh/github_pat.causify-ai.txt
  ```

## Build and activate the thin environment

- NB! This whole section can be skipped if you use [tmux](#tmux)

- Create the "thin environment" which contains the minimum set of dependencies
  needed for running our Dev Docker container

- Build the thin environment; this is done once per client
  - If you are in the `helpers` repo:

    ```bash
    > ./dev_scripts_helpers/thin_client/build.py
    ```
  - Otherwise:

    ```bash
    > cd helpers_root
    > ./dev_scripts_helpers/thin_client/build.py
    ```

- While building the thin environment, the
  [GitHub CLI](https://github.com/cli/cli/) will also be installed system-wide

- Activate the thin environment; make sure it is always activated

  ```bash
  > source dev_scripts_{repo_name}/thin_client/setenv.sh
  ```
  - E.g.,

  ```bash
  > source dev_scripts_tutorials/thin_client/setenv.sh
  ```

- If you see output like below, your environment is successfully built!
  ```bash
  ...
  alias sp='echo '\''source ~/.profile'\''; source ~/.profile'
  alias vi='/usr/bin/vi'
  alias vim='/usr/bin/vi'
  alias vimdiff='/usr/bin/vi -d'
  alias vip='vim -c "source ~/.vimrc_priv"'
  alias w='which'
  ==> SUCCESS <==
  ```
- If you encounter any issues, please post them by creating a new issue on
  GitHub and assign it to @gpsaggese
  - You should report as much information as possible: what was the command,
    what is your platform, output of the command (copy-and-paste, do not use
    screenshots)

## Install and test Docker

### Supported OS

- Our systems support Mac (both x86 and Apple Silicon) and Linux Ubuntu
- We do not support Windows and WSL: we have tried several times to port the
  toolchain to it, but there are always subtle incompatible behaviors that drive
  everyone crazy
  - If you are using Windows, we suggest to use dual boot with Linux or use a
    virtual machine with Linux
  - Install VMWare software
  - Reference video for installing
    [ubuntu](https://www.youtube.com/watch?v=NhlhJFKmzpk&ab_channel=ProgrammingKnowledge)
    on VMWare software
  - Make sure you set up your git and github
  - Install
    [docker](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)
    on your Ubuntu VM

### Install Docker

- Get familiar with Docker if you are not, e.g.,
  https://docs.docker.com/get-started/overview/

- We work in a Docker container that has all the required dependencies installed
  - You can use PyCharm / VSCode on your laptop to edit code, but you want to
    run code inside the dev container since this makes sure everyone is running
    with the same system, and it makes it easy to share code and reproduce
    problems

- Install Docker Desktop on your PC
  - Links:
    - [Mac](https://docs.docker.com/desktop/install/mac-install/)
    - [Linux](https://docs.docker.com/desktop/install/linux-install/)

- Follow
  [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

- For Mac you can also install `docker-cli` without the GUI using

  ```bash
  > brew install docker
  > brew link docker
  > brew install colima
  ```

- After installing, make sure Docker works on your laptop (of course the version
  will be newer)

  ```bash
  > docker version
  Client:
   Cloud integration: v1.0.24
   Version:           20.10.17
   API version:       1.41
   Go version:        go1.17.11
   Git commit:        100c701
   Built:             Mon Jun  6 23:04:45 2022
   OS/Arch:           darwin/amd64
   Context:           default
   Experimental:      true

  Server: Docker Desktop 4.10.1 (82475)
   Engine:
    Version:          20.10.17
    API version:      1.41 (minimum version 1.12)
    Go version:       go1.17.11
    Git commit:       a89b842
    Built:            Mon Jun  6 23:01:23 2022
    OS/Arch:          linux/amd64
    Experimental:     false
   containerd:
    Version:          1.6.6
    GitCommit:        10c12954828e7c7c9b6e0ea9b0c02b01407d3ae1
   runc:
    Version:          1.1.2
    GitCommit:        v1.1.2-0-ga916309
   docker-init:
    Version:          0.19.0
    GitCommit:        de40ad0
  ```

### Checking Docker installation

- Check the installation by running:
  ```bash
  > docker pull hello-world
  Using default tag: latest
  latest: Pulling from library/hello-world
  Digest: sha256:fc6cf906cbfa013e80938cdf0bb199fbdbb86d6e3e013783e5a766f50f5dbce0
  Status: Image is up to date for hello-world:latest
  docker.io/library/hello-world:latest
  ```

### Docker installation troubleshooting

- Common problems with Docker
  - Mac DNS problem, try step 5 from the
    [article](https://medium.com/freethreads/mac-os-docker-error-response-from-daemon-net-http-request-canceled-while-waiting-for-connection-7d1069eb4ca9)
    and repeat the cmd below:
    ```bash
    > docker pull hello-world
    Error response from daemon: net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)
    ```
  - Linux sudo problem, see
    [here](https://stackoverflow.com/questions/48568172/docker-sock-permission-denied)
    for the solution
    ```bash
    > docker pull hello-world
    Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get   http://%2Fvar%2Frun%2Fdocker.sock/v1.40/containers/json: dial unix /var/run/docker.sock: connect: permission denied
    ```

## Tmux

- Using [tmux](https://en.wikipedia.org/wiki/Tmux) is optional but recommended

- The [thin environment](#build-and-activate-the-thin-environment) is activated
  automatically within a tmux session

- Create a soft link. The command below will create a file `~/go_{repo_name}.py`

  ```bash
  > dev_scripts_{repo_name}/thin_client/tmux.py --create_global_link
  ```

- Create a tmux session. Choose `index` based on the dir name, e.g., `--index 1`
  if the dir name is `~/src/tutorials1`.

  ```bash
  > dev_scripts_{repo_name}/thin_client/tmux.py --index 1
  ```

- You need to create the tmux environment once per client and then you can
  re-connect with:

  ```bash
  # Check the available environments.
  > tmux ls
  tutorials1: 4 windows (created Fri Dec  3 18:27:09 2021) (attached)

  # Attach an environment.
  > tmux attach -t tutorials1
  ```

## Shell support

- We only support `bash`, no other shells like `zsh`, etc.
- We recommended that you make `bash` the default shell on your system, to avoid
  possible compatibility issues

## Some useful workflows

- Check the installation by running:

  ```bash
  > docker pull hello-world
  Using default tag: latest
  ```

- Pull the latest image; this is done once

  ```bash
  > i docker_pull
  ```

- Pull the latest `helpers` image containing Linter; this is done once

  ```bash
  > i docker_pull_helpers
  ```

- Get the latest version of `master`

  ```bash
  # To update your feature branch with the latest changes from master, run
  # the cmd below from a feature branch, i.e. not from master.
  > i git_merge_master
  # If you are on `master`, just pull the remote changes.
  > i git_pull
  ```

- Run Linter

  ```bash
  > i lint --files="dir1/file1.py dir2/file2.py"
  ```

- Start a Docker container

  ```bash
  > i docker_bash
  ```

- You can ignore all the warnings that do not prevent you from running the
  tests, e.g.,

  ```bash
  WARNING: The AM_AWS_ACCESS_KEY_ID variable is not set. Defaulting to a blank string.
  WARNING: The AM_AWS_DEFAULT_REGION variable is not set. Defaulting to a blank string.
  WARNING: The AM_AWS_SECRET_ACCESS_KEY variable is not set. Defaulting to a blank string.
  WARNING: The AM_FORCE_TEST_FAIL variable is not set. Defaulting to a blank string.
  WARNING: The CK_AWS_ACCESS_KEY_ID variable is not set. Defaulting to a blank string.
  WARNING: The CK_AWS_DEFAULT_REGION variable is not set. Defaulting to a blank string.
  WARNING: The CK_AWS_SECRET_ACCESS_KEY variable is not set. Defaulting to a blank string.
  WARNING: The CK_TELEGRAM_TOKEN variable is not set. Defaulting to a blank string.
  -----------------------------------------------------------------------------
  This code is not in sync with the container:
  code_version='1.4.1' != container_version='1.4.0'
  -----------------------------------------------------------------------------
  You need to:
  - merge origin/master into your branch with `invoke git_merge_master`
  - pull the latest container with `invoke docker_pull`
  ```

- If you are prompted to enter sudo password, do not enter anything and press
  Ctrl-C to resolve

  ```bash
  WARN  hserver.py _raise_invalid_host:342   Don't recognize host: host_os_name=Linux, am_host_os_name=None
  [sudo] password for ubuntu:
  ```

- Start a Jupyter server

  ```bash
  > i docker_jupyter
  ```

- To open a Jupyter notebook in a local web-browser:
  - In the output from the cmd above find an assigned port, e.g.,
    `[I 14:52:26.824 NotebookApp] http://0044e866de8d:10091/` -> port is `10091`
  - Add the port to the link like so: `http://localhost:10091/` or
    `http://127.0.0.1:10091`
  - Copy-paste the link into a web-browser and update the page

## Hack: use a local container if needed

- If [the commands above](#some-useful-workflows) do not work for you, then, as
  a temporary workaround, you can run the commands in a local Docker container

- Build a local container (the version number is not that important but make
  sure it follows the format of `NUM.NUM.NUM`)

```bash
> i docker_build_local_image --version 1.1.0
```

- Run all the commands with the flags
  `--stage local --version <YOUR_VERSION_NUMBER>`, e.g.:

```bash
# Starting bash in a Docker container.
> i docker_bash --stage local --version 1.1.0
# Starting a Jupyter server.
> i docker_jupyter --stage local --version 1.1.0
# Running Linter.
> i lint --stage local --version 1.1.0 --files="dir1/file1.py dir2/file2.py"
```

- The hack is only there to unblock you and shouldn't be relied on forever. File
  an issue to figure out why the commands don't work for you as-is
