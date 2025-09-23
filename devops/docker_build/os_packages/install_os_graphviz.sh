#!/usr/bin/env bash
#
# Install graphviz.
#
apt-get install $APT_GET_OPTS python3-dev build-essential pkg-config
if [[ 1 == 1 ]]; then
  # This is needed to install pygraphviz.
  # See https://github.com/alphamatic/amp/issues/1311.
  # It needs tzdata so it needs to go after installing tzdata.
  apt-get install $APT_GET_OPTS libgraphviz-dev
  # This is needed to install dot.
  apt-get install $APT_GET_OPTS graphviz
fi;
