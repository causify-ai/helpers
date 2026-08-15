# Disk Space Analysis: <MACHINE_OR_PATH> (read-only, nothing deleted)

## Summary
- Volume: `<VOLUME>`: total `<SIZE>`, free `<FREE>` (`<PERCENT>` full)
- Status: <e.g. "critical: under 5% free" / "healthy">

## Commands To Reclaim Space
| Command | Frees | Risk |
|:------|:------|:------|
| `<COMMAND>` | `<SIZE>` | <low/medium/high> |
| `<COMMAND>` | `<SIZE>` | <low/medium/high> |

- Total if every command above is run: `<SIZE>`

## Top 10 Directories By Size
| Rank | Directory | Size |
|:----|:------|:----|
| 1 | `<PATH>` | `<SIZE>` |
| 2 | `<PATH>` | `<SIZE>` |
| 3 | `<PATH>` | `<SIZE>` |
| 4 | `<PATH>` | `<SIZE>` |
| 5 | `<PATH>` | `<SIZE>` |
| 6 | `<PATH>` | `<SIZE>` |
| 7 | `<PATH>` | `<SIZE>` |
| 8 | `<PATH>` | `<SIZE>` |
| 9 | `<PATH>` | `<SIZE>` |
| 10 | `<PATH>` | `<SIZE>` |

## Reclaimable Breakdown
- **<Engine or category name>** (`<PATH>`, `<SIZE>` on disk):
  - Reclaimable: `<SIZE>`
  - Command:
    ```bash
    > <command>
    ```
  - Notes: <what makes this reclaimable, e.g. "0 containers reference any
    of the N images">
- <Repeat one bullet per engine/category found, ordered by size freed,
  largest first>

## Needs Manual Review
- `<PATH>` (`<SIZE>`): <why it might still be needed; can't auto-recommend>

## Verification
- Nothing was deleted or modified; this is analysis only
- Total reclaimable identified: `<SIZE>` (`<PERCENT>` of the current
  free-space deficit)
