#!/bin/bash -e

# Rename tmux pane to CC if inside tmux, and restore on exit.
if [ -n "$TMUX" ]; then
    OLD_PANE_TITLE=$(tmux display-message -p '#W')
    echo "OLD_PANE_TITLE="$OLD_PANE_TITLE
    tmux rename-window "*GH_WATCH*"
fi

watch -c -n 60 i gh_workflow_list

if [ -n "$TMUX" ]; then
    tmux rename-window $OLD_PANE_TITLE
fi
