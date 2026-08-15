# Disk Space Analysis: <MACHINE_OR_PATH> (read-only, nothing deleted)

## Summary
- Volume: `<VOLUME>`: total `<SIZE>`, free `<FREE>` (`<PERCENT>` full)
- Status: <e.g. "critical: under 5% free" / "healthy">

## Top Space Consumers
| Location | Size | Reclaimable | Notes |
|---|---|---|---|
| `<PATH>` | `<SIZE>` | `<SIZE>` or `-` | <one-line reason> |

## Reclaimable Breakdown

### <Engine Or Category Name, e.g. "Docker Desktop">
- On-disk size: `<SIZE>`
- Reclaimable: `<SIZE>`
- Command (not run): `<COMMAND>`
- Notes: <what makes this reclaimable, e.g. "0 containers reference any of
  the N images">

<Repeat one `###` subsection per engine/category found>

## Needs Manual Review
- `<PATH>` (`<SIZE>`): <why it might still be needed; can't auto-recommend>

## Recommendation (Ranked By Impact, Then Risk)
1. `<COMMAND>` → frees `<SIZE>`, risk: <low/medium/high>, reason: <why safe>
2. `<COMMAND>` → frees `<SIZE>`, risk: <low/medium/high>, reason: <why safe>

## Verification
- Nothing was deleted or modified; this is analysis only
- Total reclaimable identified: `<SIZE>` (`<PERCENT>` of the current
  free-space deficit)
