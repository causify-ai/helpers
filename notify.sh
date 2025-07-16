#!/bin/bash -e

rc=$?
if [ -n "$TMUX" ]; then
    msg=""
    session_name=$(tmux display-message -p "#{session_name}")
    window_id=$(tmux display-message -p "#{window_id}")
    window_id=""
    window_name=$(tmux display-message -p "#{window_name}")
    msg="$PWD: ${session_name} ${window_id} ${window_name} -> rc=$rc"
else
    msg="$PWD: -> rc=$rc"
fi;
echo $msg

if [[ 0 == 0 ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        cmd='display notification "'$msg'" with title "DONE!" subtitle "Script finished" sound name "blow"'
        echo $cmd
        osascript -e "$cmd"
    fi;

    if [ -n "$TMUX" ]; then
        tmux display-message "$msg"
        if [[ 0 == 1 ]]; then
            for i in {1..5}; do
                tmux display-message "$msg"
                sleep 2
                #tmux set -g status-bg black 
                #sleep 0.2
            done
        fi;
    fi;
fi;
