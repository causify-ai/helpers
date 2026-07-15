# Centralized Orchestration, Regional Execution

Canonical full version of the Near-Exchange Compute paper.

## Files

- `paper.tex` - canonical full version for arXiv / technical-report.
- `Orchestrating_Near_Exchange_Compute.pdf` - the canonical PDF.
- `references.bib` - bibliography used by the full version.
- `submission_metadata.md` - arXiv / technical-report upload metadata.

## Build

```bash
make clean
make
```

_The Makefile runs `pdflatex`, `bibtex`, and the final LaTeX passes, then checks for unresolved references/citations in the rendered PDF._

## Notes

The canonical full version is for arXiv. No IEEE cut as for now. A magazine cut may be created later if intended.

This directory is self-contained for local builds. Run `make all` from this directory to rebuild PDFs and run the unresolved-reference checks. The compatibility-named PDF is regenerated from the canonical `paper.pdf` during the build.
