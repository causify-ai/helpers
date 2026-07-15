# Causify Serverless Control Plane

Canonical full paper and IEEE Cloud Computing cut.

## Files

- `paper.tex` - canonical full arXiv / technical-report version.
- `Causify_Serverless_Control_Plane.pdf` - the canonical PDF.
- `references.bib` - bibliography for the canonical version.
- `submissions/ieee_cloud_computing/` - venue-specific IEEE Cloud Computing cut.
- `submission_metadata.md` - arXiv / technical-report upload metadata.

## Build

```bash
make clean
make
```

_The Makefile builds the full version and the IEEE Cloud Computing cut, then checks for unresolved references/citations in the rendered PDFs._

## Notes

The full version preserves richer implementation depth; DataMap, Horizon/Grid module Lambdas, Optima-style jobs, connector ingestion, scope envelopes, OpenAPI filtering, RDS Proxy/Postgres schema scoping, and production measurements. The IEEE Cloud Computing cut is shorter and venue-shaped.

This directory is self-contained for local builds. Run `make all` from this directory to rebuild PDFs and run the unresolved-reference checks. The compatibility-named PDF is regenerated from the canonical `paper.pdf` during the build.
