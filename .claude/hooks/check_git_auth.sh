#!/usr/bin/env bash
# PreToolUse hook: gate `git commit` / `git push` behind an explicit,
# human-set authorization flag file.
#
# Design goals (see problem.txt):
#   - Claude must not commit/push until the user authorizes it for a session.
#   - The user authorizes/revokes from a NORMAL shell (outside Claude), by
#     touching/removing the flag file below. Claude's own Bash tool calls are
#     still subject to the normal permission system, so a *fresh* attempt by
#     Claude to touch this file is itself a Bash command that needs approval
#     (unless a write-capable command family, e.g. `python *`, is already
#     broadly pre-allowed - check that separately).
#
# This hook only DENIES or ALLOWS; it never grants anything a settings.json
# deny rule would otherwise block (deny rules always win regardless of what
# a hook returns).

set -euo pipefail

# Default flag file lives next to this script's repo (.claude/git_authorized),
# resolved relative to this script so it doesn't depend on $HOME.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_AUTH_FILE="$(cd "$SCRIPT_DIR/.." && pwd)/git_authorized"
AUTH_FILE="${CLAUDE_GIT_AUTH_FILE:-$DEFAULT_AUTH_FILE}"

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
