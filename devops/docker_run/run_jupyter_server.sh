#!/usr/bin/env bash

set -e

FILE_NAME="devops/docker_run/run_jupyter_server.sh"
echo "##> $FILE_NAME"

# Use the old notebook interface.
#jupyter_cmd="jupyter notebook"
# Use Jupyter lab.
jupyter_cmd="jupyter lab"

# Would you like to get notified about official Jupyter news?
# --ServerApp.disable_check_for_updates=True \

#sudo /bin/bash -c "(source /venv/bin/activate; pip install jupytext)"

jupyter labextension list
jupyter labextension enable jupytext

cmd="$jupyter_cmd --ip=* --port=${PORT} \
    --allow-root \
    --NotebookApp.token=''"
echo "> cmd=$cmd"
eval $cmd
