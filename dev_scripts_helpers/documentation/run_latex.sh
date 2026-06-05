#!/usr/bin/env bash
#
# Dockerized latex
#

# TODO(gp): Convert to Python using hdocker.

set -eux
if [[ -z $1 ]]; then
    echo "Need to specify latex file to compile"
    exit -1
fi;
FILE_NAME=$1

# 1) Build container.
IMAGE=latex
# See devops/docker_build/install_publishing_tools.sh
#DOCKER_FILE=/tmp/tmp.dockerfile
DOCKER_FILE=./tmp.dockerfile
cat >$DOCKER_FILE <<EOF
FROM blang/latex:ubuntu
EOF
docker build -f $DOCKER_FILE -t $IMAGE .

# 2) Create script to run.
EXEC="./tmp.run_latex.sh"
cat >$EXEC <<EOF
#/bin/bash -xe
pdflatex -interaction=nonstopmode -halt-on-error ${FILE_NAME} && \
pdflatex -interaction=nonstopmode -halt-on-error ${FILE_NAME}
EOF
chmod +x $EXEC

# 3) Run inside Docker.
CMD="bash -c '$EXEC'"
WORKDIR="$(realpath .)"
MOUNT="type=bind,source=${WORKDIR},target=${WORKDIR}"
USER="$(id -u $(logname)):$(id -g $(logname))"
#OPTS="--user "${USER}"
OPTS=""
docker run --rm -it $OPTS --workdir "${WORKDIR}" --mount "${MOUNT}" $IMAGE:latest $CMD "$@"

# To debug:
# > docker run --rm -it --user 2908:2908 --workdir /local/home/gsaggese/src/sasm-lime6/amp --mount type=bind,source=/local/home/gsaggese/src/sasm-lime6/amp,target=/local/home/gsaggese/src/sasm-lime6/amp ctags:latest

# 4) Open.
FILE_NAME_PDF=$(echo $FILE_NAME | sed 's/\.tex$/.pdf/')
open -a /Applications/Skim.app ${FILE_NAME_PDF}
