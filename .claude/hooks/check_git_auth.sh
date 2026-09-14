#!/usr/bin/env bash
# PreToolUse hook: gate `git commit` / `git push` behind an explicit,
# human-set authorization flag file.
#
# Design goals
#   - Claude must not commit/push until the user authorizes it for a session.
#   - The user authorizes/revokes from a NORMAL shell (outside Claude), by
#     touching/removing the flag file below
#   - Claude's own Bash tool calls are still subject to the normal permission
#     system, so a *fresh* attempt by Claude to touch this file is itself a
#     Bash command that needs approval
#
# This hook only DENIES or ALLOWS; it never grants anything a settings.json
# deny rule would otherwise block (deny rules always win regardless of what
# a hook returns).

set -euo pipefail

# This hook is wired up ONCE, globally, in `~/.claude/settings.json`, so its
# `command` path (and therefore this script's own location) is fixed no
# matter which project a session is rooted in. If the flag file were resolved
# relative to *this script*, every project on the machine would share the
# same flag file (whichever repo this script happens to live in), and
# authorizing one project's session would silently authorize every other
# project's session too. Resolve per-project instead, using the
# `CLAUDE_PROJECT_DIR` env var Claude Code sets for every hook invocation
# (project, user, and local settings scopes alike):
#   1. `CLAUDE_GIT_AUTH_FILE` - explicit override, highest priority.
#   2. `$CLAUDE_PROJECT_DIR/.claude/git_authorized` - the current project's
#      own flag file.
#   3. A path next to this script - fallback for the rare case this hook is
#      invoked without `CLAUDE_PROJECT_DIR` set (e.g. manual testing).
# Do NOT "fix" this by pointing the hook's `command` at
# `$CLAUDE_PROJECT_DIR/.claude/hooks/check_git_auth.sh` instead: PreToolUse
# hooks fail OPEN when the command can't be found (non-blocking error, tool
# call proceeds), so any project missing that script would lose the gate
# entirely. Keeping `command` at one fixed, always-reachable path and doing
# the per-project resolution inside the script avoids that trap.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_AUTH_FILE="$(cd "$SCRIPT_DIR/.." && pwd)/git_authorized"
if [[ -n "${CLAUDE_GIT_AUTH_FILE:-}" ]]; then
    AUTH_FILE="$CLAUDE_GIT_AUTH_FILE"
elif [[ -n "${CLAUDE_PROJECT_DIR:-}" ]]; then
    AUTH_FILE="$CLAUDE_PROJECT_DIR/.claude/git_authorized"
else
    AUTH_FILE="$DEFAULT_AUTH_FILE"
fi

# Read the hook input JSON (only used to make the denial message concrete).
input_json="$(cat)"
command_text="$(printf '%s' "$input_json" | jq -r '.tool_input.command // "unknown command"' 2>/dev/null || echo "unknown command")"

emit() {
    local decision="$1"
    local reason="$2"
    jq -n \
        --arg decision "$decision" \
        --arg reason "$reason" \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: $decision, permissionDecisionReason: $reason}}'
}

if [[ ! -e "$AUTH_FILE" ]]; then
    emit "deny" "git commit/push not authorized this session. Run 'touch $AUTH_FILE' in a normal terminal (not through Claude) to allow, then 'rm $AUTH_FILE' to revoke. Blocked command: $command_text"
    exit 0
fi

emit "allow" "git commit/push authorized (flag file present: $AUTH_FILE)."
