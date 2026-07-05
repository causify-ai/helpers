# Status (updated 2026-07-05)

## Plan

- Phase 1: add unit tests for 0%-coverage pure-logic files (no external tool
  deps): count_words.py, generate_latex_sty.py, standardize_book_filename.py,
  clean_markdown.py, extract_from_md.py, replace_latex.py,
  extract_gdoc_map.py, extract_toc_from_txt.py
- Phase 2 (not started): mock LLM/API calls for update_md.py, summarize_md.py,
  summarize_chapters.py, check_ai_slop.py
- Phase 3: expand existing partial-coverage test files: open_md.py,
  generate_images.py, piper_markdown_reader.py, render_images.py,
  lib_notes_to_pdf.py, preprocess_notes.py, lint_txt.py, convert_table.py,
  extract_chapters_from_text.py, check_links.py
- Phase 4 (not started): file-conversion wrappers with external tool deps
  (test helpers only): convert_docx_to_md.py, convert_epub_to_md.py,
  convert_pdf_to_md.py, convert_png_dir_to_movie.py, concatenate_pdfs.py,
  transform_notes.py, generate_script_catalog.py, notes_to_pdf.py
- Phase 5 (not started, low ROI): dockerized_svg_with_inkscape.py,
  dockerized_svg_with_rsvg_convert.py, run_pandoc.py, publish_notes.py

## Progress

### Phase 1 — COMPLETE (8/8 files, 0% -> 88-98% each)

All new test files pass, following `.claude/skills/coding.rules.md` and
`.claude/skills/testing.rules.md` conventions (three-section tests,
`assert_equal`, mocked `sys.argv`, `capture_system_calls()` for subprocess
mocking, etc.):

- [x] `test/test_count_words.py` (0% -> 97%)
- [x] `test/test_generate_latex_sty.py` (0% -> 95%)
- [x] `test/test_standardize_book_filename.py` (0% -> 93%)
- [x] `test/test_clean_markdown.py` (0% -> 89%)
- [x] `test/test_extract_from_md.py` (expanded, 0% -> 94% for the in-process
      calls)
- [x] `test/test_replace_latex.py` (0% -> 95%)
- [x] `test/test_extract_gdoc_map.py` (0% -> 94%)
- [x] `test/test_extract_toc_from_txt.py` (expanded, -> 98%)

### Phase 3 — IN PROGRESS (3/10 done)

- [x] `test/test_open_md.py` (expanded, 28% -> 96%, 26 tests passing)
- [x] `test/test_generate_images.py` (27% -> 73%, all 17 tests passing).
      Found and fixed 2 real bugs in `generate_images.py`:
  - `_generate_images()`: `hdbg.dfatal("Unsupported model: %s", model)` used
    printf-style formatting, but `dfatal(message, assertion_type=None)`
    takes the 2nd positional arg as an exception class, not a format arg
    -> `model` string was used as `assertion_type`, raising `TypeError:
    'str' object is not callable`. Fixed to
    `hdbg.dfatal(f"Unsupported model: {model}")`.
  - `_parse()`: `--reference_image` argparse arg had no `default=""`, so
    `args.reference_image` was `None` when omitted; `_generate_images()`
    checks `reference_image != ""` to decide `use_reference`, so `None`
    was treated as "reference provided" and failed
    `hdbg.dassert_path_exists(None)`. Fixed by adding `default=""`.
- [x] `test/test_piper_markdown_reader.py` (13% -> 77%, 44 new tests added
      and passing). Added tests for all pure-logic helpers
      (`_read_markdown_file`, `_split_by_first_level_bullets`,
      `_format_markdown`, `_clean_text`, `_count_words`,
      `_format_reading_time`, `_chunk_text_by_length`,
      `_get_chunk_filename`, `_get_voice_path`,
      `_process_sections_to_chunks`), mocked-subprocess tests
      (`_generate_audio`, `_apply_speed_with_ffmpeg`,
      `_process_chunk_audio` caching logic), mocked-collaborator tests
      (`_handle_final_output`), `_parse()`, and `_main()` in dry-run mode
      (both plain-file and `--select` branches).
  - Left uncovered (low ROI / needs real hardware or interactive input):
    `_play_audio_with_controls` (real `pygame`/`pynput` audio playback)
    and the non-dry-run branch of `_main()` (uses `tqdm` + blocking
    `input()`).
  - **Pre-existing environment issue found (not fixed, out of scope)**:
    `Test__extract_markdown_section::test1,2,4,5,6,7` fail in this sandbox
    because `_extract_markdown_section()` shells out to `lint_txt.py`,
    which tries to build a docker container for `prettier` and the local
    container daemon isn't running (`XPC connection error`). This is a
    local environment limitation, not a code bug; these tests should pass
    in an environment with a working container runtime.
- [ ] `test/test_render_images.py` (64% -> ?) - not started
- [ ] `test/test_check_links.py` (65% -> ?) - not started
- [ ] `test/test_lib_notes_to_pdf.py` (72% -> ?) - not started
- [ ] `test/test_preprocess_notes.py` (77% -> ?) - not started
- [ ] `test/test_lint_txt.py` (80% -> ?) - not started
- [ ] `test/test_convert_table.py` (62% -> ?) - not started
- [ ] `test/test_extract_chapters_from_text.py` (74% -> ?) - not started

### Next steps

1. Proceed through the remaining 7 Phase 3 files in the order above,
   starting with `test/test_render_images.py`.
2. Then tackle Phase 2, Phase 4, Phase 5 (not yet started).

---

# Original coverage report (baseline before this work)

pytest dev_scripts_helpers/documentation --cov=dev_scripts_helpers/documentation

> coverage report
Name                                                                         Stmts   Miss Branch BrPart  Cover
--------------------------------------------------------------------------------------------------------------
dev_scripts_helpers/documentation/__init__.py                                    0      0      0      0   100%
dev_scripts_helpers/documentation/check_ai_slop.py                             151    151     28      0     0%
dev_scripts_helpers/documentation/check_links.py                               146     48     56      9    65%
dev_scripts_helpers/documentation/clean_markdown.py                             25     25      2      0     0%
dev_scripts_helpers/documentation/concatenate_pdfs.py                           68     68     16      0     0%
dev_scripts_helpers/documentation/convert_docx_to_md.py                         72     72     22      0     0%
dev_scripts_helpers/documentation/convert_epub_to_md.py                        114    114     32      0     0%
dev_scripts_helpers/documentation/convert_pandoc_divved_fence.py               136     19     32      4    86%
dev_scripts_helpers/documentation/convert_pdf_to_md.py                         256    256    110      0     0%
dev_scripts_helpers/documentation/convert_png_dir_to_movie.py                   92     92     16      0     0%
dev_scripts_helpers/documentation/convert_table.py                             111     36     30      6    62%
dev_scripts_helpers/documentation/count_words.py                                65     65     12      0     0%
dev_scripts_helpers/documentation/dockerized_svg_with_inkscape.py               25     25      4      0     0%
dev_scripts_helpers/documentation/dockerized_svg_with_rsvg_convert.py           25     25      4      0     0%
dev_scripts_helpers/documentation/documentation_utils.py                       169      5     28      5    95%
dev_scripts_helpers/documentation/extract_chapters_from_text.py                 99     27     34      1    74%
dev_scripts_helpers/documentation/extract_from_md.py                            32     32      2      0     0%
dev_scripts_helpers/documentation/extract_gdoc_map.py                           89     89     22      0     0%
dev_scripts_helpers/documentation/extract_toc_from_txt.py                      137    137     48      0     0%
dev_scripts_helpers/documentation/generate_images.py                           179    129     70      3    27%
dev_scripts_helpers/documentation/generate_latex_sty.py                        102    102     32      0     0%
dev_scripts_helpers/documentation/generate_script_catalog.py                    75     75     24      0     0%
dev_scripts_helpers/documentation/lib_notes_to_pdf.py                          401     97     90     22    72%
dev_scripts_helpers/documentation/lint_txt.py                                  398     71    158     18    80%
dev_scripts_helpers/documentation/notes_to_pdf.py                              182    182     52      0     0%
dev_scripts_helpers/documentation/open_md.py                                   129     92     36      2    28%
dev_scripts_helpers/documentation/piper_markdown_reader.py                     329    275    110      1    13%
dev_scripts_helpers/documentation/preprocess_notes.py                          357     80    144     20    77%
dev_scripts_helpers/documentation/publish_notes.py                              88     88     16      0     0%
dev_scripts_helpers/documentation/render_images.py                             381    137    142     18    64%
dev_scripts_helpers/documentation/replace_latex.py                              58     58     22      0     0%
dev_scripts_helpers/documentation/run_pandoc.py                                 26     26      4      0     0%
dev_scripts_helpers/documentation/standardize_book_filename.py                  38     38      6      0     0%
dev_scripts_helpers/documentation/summarize_chapters.py                         57     36     10      1    36%
dev_scripts_helpers/documentation/summarize_md.py                              225    151     80      4    30%
dev_scripts_helpers/documentation/test/__init__.py                               0      0      0      0   100%
dev_scripts_helpers/documentation/test/test_check_links.py                     179      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_docx_to_md.py               22      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_epub_to_md.py               22      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_pandoc_divved_fence.py     151      0     16      0   100%
dev_scripts_helpers/documentation/test/test_convert_pdf_to_md.py                20      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_table.py                   129      2      0      0    98%
dev_scripts_helpers/documentation/test/test_documentation_utils.py             362      0      0      0   100%
dev_scripts_helpers/documentation/test/test_extract_from_md.py                  55      1      0      0    98%
dev_scripts_helpers/documentation/test/test_extract_toc_from_txt.py             26      0      0      0   100%
dev_scripts_helpers/documentation/test/test_generate_images.py                  42      0      0      0   100%
dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py                409     10     20      1    97%
dev_scripts_helpers/documentation/test/test_lint_txt.py                        602     22     10      1    96%
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py                    530     68     48     15    85%
dev_scripts_helpers/documentation/test/test_open_md.py                          67      0      0      0   100%
dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py            85     17      0      0    80%
dev_scripts_helpers/documentation/test/test_preprocess_notes.py                626      0      6      0   100%
dev_scripts_helpers/documentation/test/test_render_images.py                   416      0      0      0   100%
dev_scripts_helpers/documentation/test/test_split_text_in_chapters.py          172      0      4      0   100%
dev_scripts_helpers/documentation/test/test_summarize_chapters.py               70     35      6      0    46%
dev_scripts_helpers/documentation/test/test_summarize_md.py                    200      0      2      1    99%
dev_scripts_helpers/documentation/test/test_transform_notes.py                  31      0      0      0   100%
dev_scripts_helpers/documentation/transform_notes.py                            76     76     26      0     0%
dev_scripts_helpers/documentation/update_md.py                                 173    173     42      0     0%
--------------------------------------------------------------------------------------------------------------
TOTAL                                                                         9302   3327   1674    132    60%


> coverage report --sort=cover
Name                                                                         Stmts   Miss Branch BrPart  Cover
--------------------------------------------------------------------------------------------------------------
dev_scripts_helpers/documentation/check_ai_slop.py                             151    151     28      0     0%
dev_scripts_helpers/documentation/clean_markdown.py                             25     25      2      0     0%
dev_scripts_helpers/documentation/concatenate_pdfs.py                           68     68     16      0     0%
dev_scripts_helpers/documentation/convert_docx_to_md.py                         72     72     22      0     0%
dev_scripts_helpers/documentation/convert_epub_to_md.py                        114    114     32      0     0%
dev_scripts_helpers/documentation/convert_pdf_to_md.py                         256    256    110      0     0%
dev_scripts_helpers/documentation/convert_png_dir_to_movie.py                   92     92     16      0     0%
dev_scripts_helpers/documentation/count_words.py                                65     65     12      0     0%
dev_scripts_helpers/documentation/dockerized_svg_with_inkscape.py               25     25      4      0     0%
dev_scripts_helpers/documentation/dockerized_svg_with_rsvg_convert.py           25     25      4      0     0%
dev_scripts_helpers/documentation/extract_from_md.py                            32     32      2      0     0%
dev_scripts_helpers/documentation/extract_gdoc_map.py                           89     89     22      0     0%
dev_scripts_helpers/documentation/extract_toc_from_txt.py                      137    137     48      0     0%
dev_scripts_helpers/documentation/generate_latex_sty.py                        102    102     32      0     0%
dev_scripts_helpers/documentation/generate_script_catalog.py                    75     75     24      0     0%
dev_scripts_helpers/documentation/notes_to_pdf.py                              182    182     52      0     0%
dev_scripts_helpers/documentation/publish_notes.py                              88     88     16      0     0%
dev_scripts_helpers/documentation/replace_latex.py                              58     58     22      0     0%
dev_scripts_helpers/documentation/run_pandoc.py                                 26     26      4      0     0%
dev_scripts_helpers/documentation/standardize_book_filename.py                  38     38      6      0     0%
dev_scripts_helpers/documentation/transform_notes.py                            76     76     26      0     0%
dev_scripts_helpers/documentation/update_md.py                                 173    173     42      0     0%
dev_scripts_helpers/documentation/piper_markdown_reader.py                     329    275    110      1    13%
dev_scripts_helpers/documentation/generate_images.py                           179    129     70      3    27%
dev_scripts_helpers/documentation/open_md.py                                   129     92     36      2    28%
dev_scripts_helpers/documentation/summarize_md.py                              225    151     80      4    30%
dev_scripts_helpers/documentation/summarize_chapters.py                         57     36     10      1    36%
dev_scripts_helpers/documentation/test/test_summarize_chapters.py               70     35      6      0    46%
dev_scripts_helpers/documentation/convert_table.py                             111     36     30      6    62%
dev_scripts_helpers/documentation/render_images.py                             381    137    142     18    64%
dev_scripts_helpers/documentation/check_links.py                               146     48     56      9    65%
dev_scripts_helpers/documentation/lib_notes_to_pdf.py                          401     97     90     22    72%
dev_scripts_helpers/documentation/extract_chapters_from_text.py                 99     27     34      1    74%
dev_scripts_helpers/documentation/preprocess_notes.py                          357     80    144     20    77%
dev_scripts_helpers/documentation/test/test_piper_markdown_reader.py            85     17      0      0    80%
dev_scripts_helpers/documentation/lint_txt.py                                  398     71    158     18    80%
dev_scripts_helpers/documentation/test/test_notes_to_pdf.py                    530     68     48     15    85%
dev_scripts_helpers/documentation/convert_pandoc_divved_fence.py               136     19     32      4    86%
dev_scripts_helpers/documentation/documentation_utils.py                       169      5     28      5    95%
dev_scripts_helpers/documentation/test/test_lint_txt.py                        602     22     10      1    96%
dev_scripts_helpers/documentation/test/test_lib_notes_to_pdf.py                409     10     20      1    97%
dev_scripts_helpers/documentation/test/test_extract_from_md.py                  55      1      0      0    98%
dev_scripts_helpers/documentation/test/test_convert_table.py                   129      2      0      0    98%
dev_scripts_helpers/documentation/test/test_summarize_md.py                    200      0      2      1    99%
dev_scripts_helpers/documentation/__init__.py                                    0      0      0      0   100%
dev_scripts_helpers/documentation/test/__init__.py                               0      0      0      0   100%
dev_scripts_helpers/documentation/test/test_check_links.py                     179      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_docx_to_md.py               22      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_epub_to_md.py               22      0      0      0   100%
dev_scripts_helpers/documentation/test/test_convert_pandoc_divved_fence.py     151      0     16      0   100%
dev_scripts_helpers/documentation/test/test_convert_pdf_to_md.py                20      0      0      0   100%
dev_scripts_helpers/documentation/test/test_documentation_utils.py             362      0      0      0   100%
dev_scripts_helpers/documentation/test/test_extract_toc_from_txt.py             26      0      0      0   100%
dev_scripts_helpers/documentation/test/test_generate_images.py                  42      0      0      0   100%
dev_scripts_helpers/documentation/test/test_open_md.py                          67      0      0      0   100%
dev_scripts_helpers/documentation/test/test_preprocess_notes.py                626      0      6      0   100%
dev_scripts_helpers/documentation/test/test_render_images.py                   416      0      0      0   100%
dev_scripts_helpers/documentation/test/test_split_text_in_chapters.py          172      0      4      0   100%
dev_scripts_helpers/documentation/test/test_transform_notes.py                  31      0      0      0   100%
--------------------------------------------------------------------------------------------------------------
TOTAL                                                                         9302   3327   1674    132    60%


> coverage html
Wrote HTML report to htmlcov/index.html

> open htmlcov/index.html

# Plan
Plan — 5 phases, sorted by ROI

Phase 1 — quick wins, pure logic, no external deps (~660 stmts missed, easy)
- count_words.py, generate_latex_sty.py, standardize_book_filename.py, clean_markdown.py, extract_from_md.py, replace_latex.py, extract_gdoc_map.py, extract_toc_from_txt.py
- All pure functions (string/regex/file logic), no network/docker/subprocess. Straightforward unit tests.

Phase 2 — mock LLM/API calls (~467 stmts missed, moderate)
- update_md.py, summarize_md.py, summarize_chapters.py, check_ai_slop.py
- Core logic (TOC parsing, section find/replace, header counting) is pure and testable now; mock hllmcli / requests for the LLM-call branches.

Phase 3 — expand existing partial coverage (edge cases, moderate)
- open_md.py (28%), generate_images.py (27%), piper_markdown_reader.py (13%), render_images.py (64%), lib_notes_to_pdf.py (72%), preprocess_notes.py (77%), lint_txt.py (80%), convert_table.py (62%), extract_chapters_from_text.py (74%), check_links.py (65%)
- Test files already exist for most — need more branch/edge-case tests, not new scaffolding.

Phase 4 — file-conversion wrappers, external tool deps (harder, test helpers only)
- convert_docx_to_md.py, convert_epub_to_md.py, convert_pdf_to_md.py, convert_png_dir_to_movie.py, concatenate_pdfs.py, transform_notes.py, generate_script_catalog.py, notes_to_pdf.py
- Real conversion needs pandoc/fitz/imageio/docker. Test extractable pure helpers (_move_media, _fix_image_paths, _get_frame_files, _extract_images_from_page, etc.) directly; mock hsystem.system/hdocker for orchestration paths.

Phase 5 — thin docker/network wrappers, low ROI
- dockerized_svg_with_inkscape.py, dockerized_svg_with_rsvg_convert.py, run_pandoc.py, publish_notes.py
- Almost entirely _parse() + a docker/tunnel call. Not practically unit-testable beyond arg parsing. Recommend testing _parse() only and accepting the rest, rather than burning effort mocking full docker pipelines.

Note

test_summarize_chapters.py (46%), test_notes_to_pdf.py (85%), test_piper_markdown_reader.py (80%) are themselves under 100% — worth a quick look for dead/skipped test branches before adding new tests on top.

# Important
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`
