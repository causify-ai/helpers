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

# Name of the virtual environment to create.
ENV APP_DIR=/app
ENV ENV_NAME="venv"
ENV HOME=/home

# Where to copy the installation files.
ENV INSTALL_DIR=/install
WORKDIR $INSTALL_DIR

COPY devops/docker_build/utils.sh .
RUN /bin/bash -c "source utils.sh; print_vars"

# - Update OS.
COPY devops/docker_build/update_os.sh .
RUN /bin/bash -c "./update_os.sh"

# - Install OS packages.
COPY devops/docker_build/install_os_packages.sh .
RUN /bin/bash -c "./install_os_packages.sh"

# - Install Python packages.
# Copy the minimum amount of files needed to call `install_requirements.sh` so
# we can cache it effectively.
COPY devops/docker_build/poetry.lock poetry.lock.in
COPY devops/docker_build/poetry.toml .
COPY devops/docker_build/pyproject.toml .
COPY devops/docker_build/install_python_packages.sh .
RUN /bin/bash -c "./install_python_packages.sh"

# - Install Jupyter extensions.
#COPY devops/docker_build/install_jupyter_extensions.sh .
#RUN /bin/sh -c "./install_jupyter_extensions.sh"

# - Install Docker-in-docker.
COPY devops/docker_build/install_dind.sh .
RUN /bin/bash -c 'if [[ $INSTALL_DIND == "True" ]]; then ./install_dind.sh; fi;'

## - Install publishing tools.
COPY devops/docker_build/install_publishing_tools.sh .
RUN /bin/bash -c "./install_publishing_tools.sh"

# - Create users and set permissions.
COPY devops/docker_build/create_users.sh .
RUN /bin/bash -c "./create_users.sh"
COPY devops/docker_build/etc_sudoers /etc/sudoers

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
