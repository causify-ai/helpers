DEBIAN_FRONTEND=noninteractive


print_vars() {
  echo "AM_CONTAINER_VERSION=$AM_CONTAINER_VERSION"
  echo "APP_DIR=$APP_DIR"
  echo "CLEAN_UP_INSTALLATION=$CLEAN_UP_INSTALLATION"
  echo "ENV_NAME=$ENV_NAME"
  echo "HOME=$HOME"
  echo "INSTALL_DIND=$INSTALL_DIND"
  echo "POETRY_MODE=$POETRY_MODE"
}


report_disk_usage() {
  du -h --max-depth=1 / --exclude=/proc | sort -hr
  # Print dirs with size larger than 1MB.
  DIRS="/usr /var"
  du -h --max-depth=1 $DIRS 2>/dev/null | \
    awk '$1 ~ /[0-9\.]+M/ || $1 ~ /[0-9\.]+G/ || $1 ~ /[0-9\.]+T/' | \
    sort -hr
}