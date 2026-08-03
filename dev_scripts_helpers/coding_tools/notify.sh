# Wrapper for `notify.py` that:
# - Flushes the current shell's history to disk
# - Dumps the last few commands to a tmp file for `notify.py` to read
# - Calls notify.py
#
# A Python (or any child) process can't call the shell's `history` builtin
# itself: it runs in its own process and can't reach into the parent shell's
# memory, so it would only ever see its own empty history, never the
# interactive shell's.
#
# This script must be *sourced*, not executed, so that `history -a` / `history
# 10` run in the actual interactive shell instead of in a throwaway subshell.
#
# > source notify2.sh

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: notify2.sh must be sourced, e.g., 'source notify2.sh', not executed directly"
    return 1 2>/dev/null || exit 1
fi

history -a
history 10 > /tmp/tmp.history.txt

notify.py "$@"
