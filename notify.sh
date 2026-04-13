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

# Play a sound.
(for i in {1..2}; do afplay -v 1.00 /System/Library/Sounds/Ping.aiff; done) &

if [[ 0 == 0 ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        # brew install terminal-notifier
        # cmd='Display notification "'$msg'" with title "DONE!" subtitle "Script finished" sound name "blow"'
        # echo $cmd
        # osascript -e "$cmd"
        terminal-notifier -title "DONE" -message "Script finished" -sound "Blow"
    fi;

    if [ -n "$TMUX" ]; then
        tmux display-message "$msg"
        if [[ 0 == 1 ]]; then
            for i in {1..5}; do
                tmux display-message "$msg"
            done
        fi;
    fi;
fi;
