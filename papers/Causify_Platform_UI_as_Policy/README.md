# Causify Platform UI-as-Policy

Canonical full paper and IEEE Software cut.

## Files

- `paper.tex` - canonical full arXiv / technical-report version.
- `Causify_Platform_UI_as_Policy.pdf` - the canonical PDF.
- `references.bib` - bibliography for the canonical version.
- `submissions/ieee_software/` - venue-specific IEEE Software cut.
- `submission_metadata.md` - arXiv / technical-report upload metadata.

## Build

```bash
make clean
make
```

_The Makefile builds the full version and the IEEE Software cut, then checks for unresolved references/citations in the rendered PDFs._

## Notes

This directory is self-contained for local builds. Run `make all` from this directory to rebuild PDFs and run the unresolved-reference checks. The compatibility-named PDF is regenerated from the canonical `paper.pdf` during the build.
