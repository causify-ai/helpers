# syntax = docker/dockerfile:experimental

FROM ubuntu:24.04 AS builder
#FROM ubuntu:20.04 AS builder

# Interface for the build arguments.
# NOTE: The values are encoded as the strings "True" and "False".
# TODO(gp): AM_CONTAINER_VERSION -> CK_CONTAINER_VERSION
ARG AM_CONTAINER_VERSION
ARG CLEAN_UP_INSTALLATION
ARG INSTALL_DIND
ARG POETRY_MODE
# `BUILD_TOOL` selects the Python dependency installer used inside the
# container venv: `poetry` (default, historical flow) or `uv` (new flow,
# faster). See `install_python_packages.sh` for the implementation.
ARG BUILD_TOOL=poetry
# `PINNED_PYTHON_VERSION` is the single source of truth from
# `repo_config.yaml#python_info.python_version`. It is checked against
# the interpreter shipped by the base image inside
# `install_os_packages.sh`; the build fails fast on drift.
ARG PINNED_PYTHON_VERSION="3.12"

# Name of the virtual environment to create.
ENV APP_DIR=/app
ENV ENV_NAME="venv"
ENV HOME=/home

# Where to copy the installation files.
ENV INSTALL_DIR=/install
WORKDIR $INSTALL_DIR

COPY devops/docker_build/utils.sh .
RUN /bin/bash -c "source utils.sh; print_vars"

# - Update OS and Install OS packages.
# Forward the pinned Python version so `install_os_packages.sh` can assert
# that the base image ships the expected interpreter.
COPY devops/docker_build/install_os_packages.sh devops/docker_build/update_os.sh ./
COPY devops/docker_build/os_packages/ ./os_packages/
RUN /bin/bash -c "export PINNED_PYTHON_VERSION='${PINNED_PYTHON_VERSION}' && ./update_os.sh && ./install_os_packages.sh"

# - Install Python packages.
# Copy the minimum amount of files needed to call `install_python_packages.sh`
# so we can cache it effectively. `BUILD_TOOL` selects the installer
# (`poetry` or `uv`); see the script for the two flows.
COPY devops/docker_build/poetry.lock poetry.lock.in
COPY devops/docker_build/poetry.toml \
     devops/docker_build/pyproject.toml \
     devops/docker_build/install_python_packages.sh ./
RUN /bin/bash -c "export BUILD_TOOL='${BUILD_TOOL}' && ./install_python_packages.sh"

# - Install Docker-in-docker.
COPY devops/docker_build/install_dind.sh .
RUN /bin/bash -c 'if [[ $INSTALL_DIND == "True" ]]; then ./install_dind.sh; fi;'

# - Create users and set permissions.
COPY devops/docker_build/create_users.sh .
RUN /bin/bash -c "./create_users.sh"
COPY devops/docker_build/etc_sudoers /etc/sudoers

# When building for the `arm64` architecture, root permissions are not
# propagated to the files in the container. This is a workaround to fix the
# behavior.
RUN chown root:root /etc/sudoers

# - Mount external filesystems.
# RUN mkdir -p /s3/alphamatic-data
# RUN mkdir -p /fsx/research

# - Create the bashrc file.
COPY devops/docker_run/bashrc $HOME/.bashrc

ENV AM_CONTAINER_VERSION=$AM_CONTAINER_VERSION
RUN echo "AM_CONTAINER_VERSION=$AM_CONTAINER_VERSION"

# TODO(gp): Is this needed?
WORKDIR $APP_DIR

ENTRYPOINT ["devops/docker_run/entrypoint.sh"]
