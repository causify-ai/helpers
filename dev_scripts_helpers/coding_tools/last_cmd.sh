# Wrapper for `last_cmd.py` that
# - flushes the current shell's history to disk
# - dumps the last few commands to a tmp file for `last_cmd.py` to read
# - calls last_cmd.py
#
# A Python (or any child) process can't call the shell's `history` builtin
# itself: it runs in its own process and can't reach into the parent shell's
# memory, so it would only ever see its own empty history, never the
# interactive shell's.
#
# This script must be *sourced*, not executed, so that `history -a` / `history
# 10` run in the actual interactive shell instead of in a throwaway subshell.
#
# > source last_cmd.sh
# > . last_cmd.sh -n 3

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: last_cmd.sh must be sourced, e.g., 'source last_cmd.sh', not executed directly"
    return 1 2>/dev/null || exit 1
fi

history -a
history 10 > /tmp/tmp.history.txt

last_cmd.py "$@"
