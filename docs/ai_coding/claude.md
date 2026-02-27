//

# Getting started

## Core concepts

### How CC works

- The agentic loop
  - Gather context
  - Take action
  - Verify results

- It is powered by models (to reason) and tools (to act)
- CC is the harness around Claude (the model)
  - Provide tools
  - Manage context
  - Execution environment

- Multiple models `/model` or `claude --model <name>`

- Tools allow to act
  - E.g., read code, edit files, run commands, search the web
  - Return information feeding back into the loop

- Extensions of the agentic loop
  - Skills
  - MCP (connect to external services)
  - Hooks (automate workflows)
  - Subagents (offload / delegate tasks)

- Work with sessions
  - CC saves your conversation locally
  - Before CC makes changes, it takes a snapshot of files
  - Each session starts with a fresh context window
  - Each CC conversation is a session tied to the current dir

- Context window
  - Stores conversation history, file contents, skills, ...
  - You can use `/context` to see what's using space
  - When context reaches the limit. it's compacted, cleaned up
  - Skills are loaded on demand
  - Subagents are separated from main conversation

- Checkpoints
  - Every file edit is reversible
  - You can press `Esc` twice to rewind to a previous state

- Permission mode
  - `Shift + Tab` to cycle through permission modes
  - Asks before edits
  - Auto-accept edits
  - Plan mode (read-only tools)

- Ask CC for help
  - "How do I set up hooks?" ...
  - `/init` walks through creating a CLAUDE.md
  - `/agents` configures subagents
  - `/doctor`

- If CC is going to wrong path, just type your correction
  - CC will stop and adjust the approach

- CC performs best when it can check its own work
  - E.g., include test cases, paste expected UI, define the output you want

- Explore before implementing
  - Separate research from coding, using plan mode
    ```
    Read ... and understand. Then create a plan for ...
    ```
  - Then let CC implement

- Delegate, don't dictate
  - Think of CC as a capable colleague
  - Give context and direction and trust CC to figure out the details

### Extend CC

- Extensions for agentic loop
  - `CLAUDE.md` to add context for every sessions
  - Skills: on-demand / reusable knowledge and invocable workflows
  - MCP: connects to external services
  - Subagents: run in isolated context, returning summaries
  - Agent teams: coordinate independent sessions with shared tasks and
    peer-to-peer messaging
  - Hooks: run scripts outside the loop
  - Plugins and packages

- Skill
  - Markdown file containing knowledge and workflows
  - You can invoke skills with slash command or CC can load them when relevant
  - You can run skills in current conversation or via subagents

- Skill vs Subagents
  - Skills are reusable content you can load into any context
  - Subagents are isolated workers (e.g., parallel work and specialized workers)

- Skill vs `CLAUDE.md`
  - `CLAUDE.md` is for every session ("always do X" rule)
    - E.g., coding conventions, project structure, "never do X" rules
    - It should be less than 500 lines
  - Skills can be invoked for `/name`
  - Both can include paths with @path imports
    ```
    @path ./rules.md
    @path ./examples.md
    ```

- Subagent vs Agent team
  - Subagents run inside the same session and report back to main context
  - Agent teams are independent CC that communicate with each other
  - Use subagent when need a focused worked
  - Use agent team when agents need to coordinate independently

- MCP vs Skill
  - MCP connects to external services
  - Skills extend what CC knows

- You can nest `CLAUDE.md` files in subdirs

- Skill + MCP: MCP provides the connection, a skill teaches CC how to use it
- Skill + Subagent: A skill can spawn subagents for parallel work
- `CLAUDE.md` + Skills: CLAUDE.md is for always-on rules, skills are for
  on-demand knowledge
- Hook + MCP: a hook triggers external actions (e.g., "send a Slack notification"
  when CC modifies critical files)

- Features consume CC's context
  - Too much can fill context window and add noise

### Common workflows

- Quick codebase overview
  - Navigate to project root
  - "Give me an overview of this codebase"
  - "Explain the main architecture patterns"
  - "What are the key data models?"
  - ...

- Find relevant code
  - "Find the files that handle user authentication"
  - "How do these authentication files work together?"

- Fix bugs efficiently

- Refactor code
  - Do refactoring in small / testable increments

- Use specialized subagents
  - "Use the code-reviewer subagent ..."
  - "Have the debugger subagent investigate ..."

- Use Plan Mode for safe code analysis
  - E.g., `claude --permission-mode plan`

- Work with tests

- Create pull requests
  - Create a PR
  - E.g., `/commit-push-pr` skill

- Handle documentation

- Work with images
  - Drag-and-drop image into CC window
  - Copy-paste image with `CTRL+v` (not `CMD+v`)

- Reference files and directories
  - E.g., "What's the structure of @src/...?"

- Reference MCP resources
  - E.g., "Show me the data from @github:repos/owner/`

- Use extended thinking
  - The reasoning is visible in verbose mode, toggled with `CTRL+O`
  - Phrases like "think", "think hard", "ultrathink"

- Extended thinking controls how much internal reasoning CC perform before
  responding

- Resume conversations
  - `/rename` and `/resume`

- Git worktrees
  - When running on multiple tasks at once, you need to have different copies of
    the codebase
  - E.g., work on a feature in one worktree and fix a bug in another, without
    sessions interfering
  ```
  > git worktree add ../.. -b feature-XYZ
  > git worktree add ../.. bugfix-XYZ
  > cd ../.. && claude
  > git worktree list
  > git worktree remove ../...
  ```

- Subagents can use worktree to work in parallel
  - E.g., use `isolation: worktree` to the agent front matter

- Get notified when CC needs your attention
  - Use hooks in `.claude/settings.local.json`
  - Hooks communicate through stdin, stdout, stderr and exit codes

- Use Claude as a unix-style utility
  ```
  > claude -p "..." --output-format ...
  ```

### Best practices

- CC's context window fills up fast and then performance degrades (e.g.,
  forgetting earlier instructions)
  - Context window holds your entire conversation, every message, every file,
    every command output

- CC performs much better when it can verify its work
  - It needs a clear success criteria

- Explore first, then plan, then code
  - Enter plan mode to read files and answers questions without making changes
    - This is important when you are uncertain about the approach
    - If the task is simple (fix a typo, rename a variable) skip planning
  - Ask to create a detailed implementation plan (press `CTRL+G` in your text
    editor to edit directly)
  - Implement switch to normal mode and let CC code and verify against its plan
  - Commit

- Provide specific context to avoid corrections
  - Scope the task (e.g., specific file, testing preferences)
  - Point to sources
  - Reference existing patterns in your code base
  - Describe the symptom and what "fixed" looks like

- `CLAUDE.md`
  - Treat it like code: review it, prune it, test changes to see whether CC's
    behavior shifts
  - Use `@path/...` to import additional files

- CLI tools are the most context-efficient way to interact with external services
  - E.g., `gh`

# Build with CC

## Create custom subagents

## Run agent teams

## Create plugins

## Prebuilt plugins

## Extend CC with skills

## Output styles

## Automate with hooks

## Programmatic usage

## Model Context Protocol MCP)

## Troubleshooting

# Deployment

# Administration

# Configuration

# Reference

# Resources
