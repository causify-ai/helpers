#!/bin/bash
# """
# Capture a command from history and copy to clipboard. Can be sourced or
# executed directly.
# """

capture_command() {
  # """
  # Capture the N-th previous command from history and copy to clipboard.
  #
  # :param -n N: Index of command to capture from history (default: 1)
  # :return: None (copies command to clipboard)
  # """
  local n=1

  # Parse command-line options.
  while getopts "n:" opt; do
    case $opt in
      n) n="$OPTARG" ;;
      *) echo "Usage: capture_last_cmd.sh [-n N]"; return 1 ;;
    esac
  done

  # Get history and filter out script invocations.
  local all_cmds
  all_cmds=$(history 20)

  # Display most recent 5 commands for reference.
  echo "Most recent 5 commands:"
  echo "$all_cmds" | tail -5

  echo

  # Extract and process the specified command by index (counting from most recent).
  prev_cmd=$(echo "$all_cmds" | grep -v "capture_last_cmd.sh" | grep -v "last_cmd" | tail -n "$n" | head -1 | sed -E 's/^[ ]*[0-9]+[ ]*//')

  echo "Capturing command $n to clipboard"
  echo $prev_cmd
  echo "$prev_cmd" | pbcopy
}

capture_command "$@"
