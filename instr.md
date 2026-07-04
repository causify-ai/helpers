Create a python script notify.py that

- Find what is the last command executed and in which directory
- Implement in Python ./notify.sh
- makes the window status entries in tmux blink until it's CTRL-C
- has an option to send a notification like
  osascript -e 'display notification \"Claude Code is waiting for your input\" with title \"Claude Code Idle\" sound name \"Glass\"'
- The name of the window in tmux is saved and restored at the end of the script

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is
