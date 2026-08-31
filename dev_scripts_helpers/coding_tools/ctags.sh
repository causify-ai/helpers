#!/usr/bin/env bash
# """
# Build and run universal-ctags inside a container to generate a `tags` file
# for the current directory, without requiring ctags to be installed on the
# host.
#
# The container engine is auto-detected: Docker if it is installed and
# running, otherwise Apple's native `container` CLI (macOS only). Force one
# explicitly with `--engine` or `CONTAINER_ENGINE`.
#
# sudo apt install universal-ctags
# rm tags
# ctags --languages=Python --exclude=.git --exclude=.mypy_cache -R .
#
# Skip extra dirs with -e/--exclude (repeatable):
# > ctags.sh --exclude node_modules --exclude build
#
# Force a specific container engine:
# > ctags.sh --engine docker
# > ctags.sh --engine container
# > CONTAINER_ENGINE=container ctags.sh
# """

set -eu

# Dirs always excluded.
EXCLUDE_DIRS=(".git" ".mypy_cache")

# Container engine to use ("docker" or "container"). Empty means auto-detect.
ENGINE="${CONTAINER_ENGINE:-}"

# Parse `-e|--exclude DIR` and `--engine ENGINE` options, forward everything
# else untouched.
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -e|--exclude)
            EXCLUDE_DIRS+=("$2")
            shift 2
            ;;
        --engine)
            ENGINE="$2"
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done
set -- ${ARGS[@]+"${ARGS[@]}"}

EXCLUDE_OPTS=""
for dir in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_OPTS+=" --exclude=${dir}"
done

# #############################################################################
# Pick the container engine.
# #############################################################################

detect_engine() {
    # """
    # Pick a container engine when none was requested explicitly, preferring
    # Docker (widely available) over Apple's `container` CLI (macOS-only).

    # :return: print "docker" or "container" to stdout, or nothing if neither
    #     is usable
    # """
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        echo "docker"
    elif command -v container >/dev/null 2>&1; then
        echo "container"
    fi
}

if [[ -z "$ENGINE" ]]; then
    ENGINE="$(detect_engine)"
fi

if [[ "$ENGINE" != "docker" && "$ENGINE" != "container" ]]; then
    echo "ERROR: no container engine found (need 'docker' or Apple's 'container')" >&2
    echo "Install Docker (https://docker.com) or Apple's container tool" \
        "(https://github.com/apple/container), or pass --engine explicitly." >&2
    exit 1
fi
if ! command -v "$ENGINE" >/dev/null 2>&1; then
    echo "ERROR: engine '${ENGINE}' is not installed" >&2
    exit 1
fi
echo "Using container engine: ${ENGINE}"

if [[ "$ENGINE" == "container" ]]; then
    # Apple's `container` CLI needs its VM-backed service running, both to
    # build and to run images. This is a no-op if it is already running.
    container system start >/dev/null 2>&1 || true
fi

# #############################################################################
# Build the image with universal-ctags built from source.
# #############################################################################

cat >/tmp/tmp.dockerfile <<EOF
FROM ubuntu:20.04

RUN apt-get update && \
    apt-get -y upgrade

# Install package (but it's from 2018).
#RUN apt install -y universal-ctags

# Build from source.
RUN export DEBIAN_FRONTEND=noninteractive; \
    apt-get install -y build-essential && \
    apt-get install -y automake && \
    apt-get install -y pkg-config && \
    apt-get install -y git

RUN export GIT_SSL_NO_VERIFY=1 && \
    git clone http://github.com/universal-ctags/ctags.git

RUN cd ctags && \
    ./autogen.sh && \
    ./configure --prefix=/usr/local && \
    make && \
    make install
RUN ctags --version
EOF

"$ENGINE" build -f /tmp/tmp.dockerfile -t ctags .

# Only allocate tty if one is detected. See - https://stackoverflow.com/questions/911168
#if [[ -t 0 ]]; then IT+=(-i); fi
#if [[ -t 1 ]]; then IT+=(-t); fi

USER="$(id -u $(logname)):$(id -g $(logname))"
WORKDIR="$(realpath .)"
MOUNT="type=bind,source=${WORKDIR},target=${WORKDIR}"

TAGS_FILE="tags"

cat >./run_tags.sh <<EOF
rm $TAGS_FILE
ctags --version || true
ctags --languages=python$EXCLUDE_OPTS -R .
echo "Created tags in '$TAGS_FILE'"
EOF
chmod +x ./run_tags.sh

CMD="bash -c './run_tags.sh'"

# #############################################################################
# Run the container, mounting the current dir to generate `tags` in place.
# #############################################################################

#OPTS="--user "${USER}"
OPTS=""
"$ENGINE" run --rm -it $OPTS --workdir "${WORKDIR}" --mount "${MOUNT}" ctags:latest $CMD "$@"

# To debug:
# > docker run --rm -it --user 2908:2908 --workdir /local/home/gsaggese/src/sasm-lime6/amp --mount type=bind,source=/local/home/gsaggese/src/sasm-lime6/amp,target=/local/home/gsaggese/src/sasm-lime6/amp ctags:latest
