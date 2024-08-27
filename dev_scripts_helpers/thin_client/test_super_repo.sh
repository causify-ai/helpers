#!/bin/bash -xe

DIR_PREFIX="sports_analytics"

# dev_scripts_{DIR_PREFIX}/thin_client/build.py

# Test helpers setenv.
(cd helpers_root; source dev_scripts_helpers/thin_client/setenv.sh)

# Test super-repo setenv.
source dev_scripts_${DIR_PREFIX}/thin_client/setenv.sh

# Test tmux.
dev_scripts_${DIR_PREFIX}/thin_client/tmux.py --create_global_link
dev_scripts_${DIR_PREFIX}/thin_client/tmux.py --index 1

# Test building image.
i docker_build_local_image --version 1.0.0 && i docker_tag_local_image_as_dev --version 1.0.0

# Test running image.
i docker_bash --skip-pull
i docker_jupyter

# helpers_root/dev_scripts_helpers/thin_client/sync_repo_thin_client.sh
