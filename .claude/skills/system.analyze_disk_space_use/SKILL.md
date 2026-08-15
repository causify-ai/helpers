---
description: Analyze disk usage to find the largest space consumers and reclaim options
model: haiku
---

# Goal
- Find what is consuming the most disk space, identify what is safely reclaimable
  (unused container/VM images, caches, logs) versus what needs manual review, and
  report the findings
- Never delete, move, or modify anything: analysis only

# Workflow

## Step 1: Check Overall Disk Usage
- Run `df -h` to see total/used/available space per volume
- On macOS, the volume that actually holds user data is
  `/System/Volumes/Data`, not `/`: use its `Capacity`/`Avail` columns to
  judge how urgent the situation is

## Step 2: Survey The Home Directory
- List top-level home directory usage, largest first:
  ```bash
  > du -sh ~/* 2>/dev/null | sort -rh
  ```
- Recurse one level at a time into whichever directory dominates (on
  macOS this is typically `~/Library`), always sorting by size, until you
  reach the actual large items instead of just a big parent directory
  name:
  ```bash
  > /usr/bin/du -sh ~/Library/* 2>/dev/null | sort -rh | head -30
  ```
- Track every directory measured along the way: it feeds the top-10 list
  in Step 6

## Step 3: Check Container And VM Engines First
- On a dev machine these are usually the single biggest consumer, because
  they cache every pulled/built image and rarely self-prune
- For every engine that is installed, check its own usage report before
  digging into raw directory sizes:
  - Docker: if `docker` exists, run `docker system df -v` for a
    per-image/per-volume breakdown; images with `CONTAINERS` = 0 are
    unused and reclaimable
  - Apple `container` CLI (native macOS containers): if `container`
    exists, run `container system df`; its data lives under
    `~/Library/Application Support/com.apple.container` and Docker's VM
    disk lives under `~/Library/Containers/com.docker.docker`
  - Other engines present (`podman`, `colima`, `lima`, `nerdctl`): use
    their equivalent `system df` / usage-report command
- A builder container (e.g. Docker's `buildx` state volume, Apple's
  `buildkit` builder container) can be reported as "active" and excluded
  from `RECLAIMABLE` by the tool even when it has grown very large
  - Size it directly with `/usr/bin/du -sh <path>` and report it as a
    manual candidate, along with the reset command that would reclaim it
    (`docker buildx prune --all`, or
    `container builder stop && container builder delete`)

## Step 4: Check Common Cache/Log Locations
- macOS:
  - `~/Library/Caches`
  - `~/Library/Logs`
  - Per-app `Cache` / `Code Cache` folders under
    `~/Library/Application Support/<App>`
  - `~/.Trash`
  - `tmutil listlocalsnapshots /`: flag any entry that is not a normal
    `com.apple.os.update-*` system snapshot
- Linux: use the equivalents instead: `~/.cache`, `/var/cache`,
  `/var/log`, and package-manager caches (`apt`, `dnf`, `pacman`)

## Step 5: Spot-Check Dev Artifacts
- Look for large, likely-stale developer artifacts: `venv`/`.venv`
  directories, `node_modules`, old or duplicate repo clones, and
  suspiciously named directories (`backups`, `ancient_*`, `old_*`)
- Report these as "needs manual review", not as auto-recommended
  deletions: they can hold unique, irreplaceable data

## Step 6: Rank Findings And Write The Report
- For every candidate record: path, size, and whether it is safely
  reclaimable (rebuildable / re-pullable / re-cacheable) or needs manual
  review (may hold unique data)
- Fill in the template
  `.claude/skills/system.analyze_disk_space_use/report.template.md`,
  formatted per `.claude/skills/markdown.rules.md`
- List the top 10 directories measured in Steps 2-3 by size, largest
  first; prefer the most specific directory that explains the bytes over
  a vague ancestor (e.g. list the Docker VM disk itself, not just
  `~/Library`)
- Every reclaim command in the report must come from the tool's own
  output (e.g. `docker system df`), never be guessed, and must be paired
  with the size it frees
- Because the report describes commands, lead with a summary table of
  every command and its estimated savings, then give the full nested
  breakdown per `.claude/skills/markdown.rules.md` "List of Items"
  convention: one bold-labeled bullet per reclaimable item, with the
  command and size nested underneath it
- Rank the breakdown by impact (space freed) first, then by risk

# Constraints
- Only run read-only commands: `df`, `du`, `*system df`, `*ls`,
  `tmutil listlocalsnapshots`, `find` (without `-delete`)
- Never run a destructive command: `docker system prune`,
  `docker image rm`, `container image rm`, `rm -rf`, `container builder
  delete`, etc.: only list them in the report as candidates for the user
  to run themselves
- If a read-only command errors with an unexpected `usage:` message,
  suspect a shell-hook rewrite and retry with the command's full binary
  path (e.g. `/usr/bin/du`)
- Do not enumerate every file: stop recursing into a directory once its
  largest child no longer meaningfully explains the space gap

# Verification
- The report accounts for most of the gap between disk size and free
  space (the sum of reported items roughly explains where the used space
  went)
- Confirm no file was created, deleted, or modified other than the report
  itself
