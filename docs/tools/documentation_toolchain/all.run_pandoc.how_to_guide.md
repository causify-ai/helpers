<!-- toc -->

- [run_pandoc.py – How‑to Guide](#run_pandocpy-%E2%80%93-how%E2%80%91to-guide)
  * [What the script does](#what-the-script-does)
  * [Quick‑use commands](#quick%E2%80%91use-commands)
  * [Flags](#flags)

<!-- tocstop -->

# run_pandoc.py – How‑to Guide

A **minimal wrapper** around Pandoc that lets you transform files between types.

---

## What the script does

```text
stdin / file  ──►  run_pandoc.py  ──►  stdout / file
                 │
                 └─► helpers.hlatex.convert_pandoc_md_to_latex()
```

* Reads **Markdown** from _stdin_ or `--input` file.
* Dispatches to a named **action** (currently only `convert_md_to_latex`).
* Pushes the Pandoc output to _stdout_ or the `--output` file.

---

## Quick‑use commands

| Goal                                  | Command                                      |
| ------------------------------------- | -------------------------------------------- |
| Convert a Markdown file to LaTeX      | `run_pandoc.py -i note.md -o note.tex`       |
| Same, but stream from STDIN to STDOUT | `cat note.md \| run_pandoc.py -i - -o -`     |
| Inside **Vim** (visual range)         | `:'<,'>!run_pandoc.py -i - -o - -v CRITICAL` |

> **Tip :** pass `-v CRITICAL` to silence helper logging when piping into
> editors.

---

## Flags

| Flag               | Default               | Meaning                                                   |
| ------------------ | --------------------- | --------------------------------------------------------- |
| `-i / --input`     | `-`                   | Source file or `-` for STDIN.                             |
| `-o / --output`    | `-`                   | Destination file or `-` for STDOUT.                       |
| `--action`         | `convert_md_to_latex` | Transformation to apply. Future‑proofed for more actions. |
| `-v / --log_level` | `INFO`                | Standard helper‑library verbosity.                        |

---