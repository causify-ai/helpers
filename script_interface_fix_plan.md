# Plan: Fix `dev_scripts_helpers/` Script Interfaces (GH #1342)
Audited ~230 `*.py` files under `dev_scripts_helpers/` against
`script_interface.md`. ~230 real CLI entry points found once libraries,
`__init__.py`, and non-`argparse` scripts are excluded; **~115 of those
deviate** from the documented conventions in some way. This file lists every
finding, grouped by the convention violated (so fixes can be batched by helper
function), then flags actual bugs, then proposes scope/phasing

## 0. Actual Bugs Found (not Just Convention Drift: Fix Regardless of Scope)
| File                                                               | Bug                                                                                                                                                                                 |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dev_scripts_helpers/generate_videos/convert_pdf_to_flip_video.py` | `_parse()` returns a `Namespace` (calls `.parse_args()` itself); `_main(parser)` then calls `parser.parse_args()` on that `Namespace` → `AttributeError` crash on every invocation. |
| `dev_scripts_helpers/documentation/publish_notes.py`               | `--dst_dir` is declared `action="store_true"` with a path-string default → the flag can never actually be set to a custom directory from the CLI.                                   |
| `dev_scripts_helpers/system_tools/email_notify.py`                 | Entry guard is `if __name__ == "main":` (missing underscores) → the script body never runs when executed directly.                                                                  |
| `dev_scripts_helpers/aws/am_aws.py`                                | `_parse()` itself calls `_main(parser)` at the end, and `if __name__ == "__main__": _parse()`: control flow is inverted from the documented skeleton.                              |

## 1. Findings by Convention Violated

### 1.1 Input/Output (`helpers.hselect_input_output.add_input_output_args()`)
Hand-rolled `-i/--input`/`-o/--output` (or `--in_file`/`--out_file`,
`--input_file`, etc.) instead of the canonical helper:

- `dev_scripts_helpers/ai/extract_cc_log.py`
- `dev_scripts_helpers/coding_tools/build_call_graph.py`, `print_pickle.py`,
  `reorder_python_code.py`, `split_in_files.py`, `toml_merge.py`
- `dev_scripts_helpers/dockerize/dockerized_graphviz.py`, `dockerized_latex.py`,
  `dockerized_mermaid.py`, `dockerized_pandoc.py`,
  `dockerized_svg_with_inkscape.py`, `dockerized_svg_with_rsvg_convert.py`,
  `dockerized_tikz_to_bitmap.py`
- `dev_scripts_helpers/documentation/check_links.py`, `clean_markdown.py`,
  `notes_to_pdf.py`, `transform_pandoc_ast_to_typst.py`,
  `dockerized_svg_with_inkscape.py`, `dockerized_svg_with_rsvg_convert.py`,
  `open_md.py`, `run_latex.py`, `standardize_book_filename.py`,
  `replace_latex.py`, `convert_epub_to_md.py`
- `dev_scripts_helpers/generate_videos_veo3/generate_videos.py`
- `dev_scripts_helpers/git/github/dockerized_sync_gh_issue_labels.py`,
  `sync_gh_issue_labels.py`, `dockerized_sync_gh_repo_settings.py`,
  `to_github.py`
- `dev_scripts_helpers/google/to_gsheet.py`
- `dev_scripts_helpers/llms/dockerized_llm_review.py`
- `dev_scripts_helpers/notebooks/extract_notebook_images.py`,
  `dockerized_extract_notebook_images.py`
- `dev_scripts_helpers/testing/pytest_failed.py`

Fix: replace with
`hseinout.add_input_output_args(parser, in_required=..., out_required=...)`, use
`args.input`/`args.output`

### 1.2 Destination Directory (`helpers.hselect_input_output.add_dst_dir_arg()`)
Hand-rolled `--dst_dir`/`--out_dir`/`--output_dir`/`--target_dir`, usually
missing the paired `--overwrite` or using a differently-named/broken equivalent
(`--override`, `--from_scratch`, `--delete_dst_dir`, `--no_backup`):

- `dev_scripts_helpers/coding_tools/build_call_graph.py`, `split_in_files.py`
- `dev_scripts_helpers/documentation/convert_docx_to_md.py`,
  `convert_pdf_to_md.py`, `extract_chapters_from_text.py`, `generate_images.py`,
  `render_images.py`, `publish_notes.py` (also a bug, see §0)
- `dev_scripts_helpers/generate_videos_veo3/generate_images.py`
- `dev_scripts_helpers/google/create_google_drive_map.py`, `gdrive_backup.py`,
  `gws_download_doc.py` (`--to_dir`)
- `dev_scripts_helpers/llms/llm_compare.py`
- `dev_scripts_helpers/notebooks/publish_notebook.py` (`--target_dir`)
- `dev_scripts_helpers/system_tools/create_links.py`, `save_screenshot.py`,
  `zip_files.py`

Fix: replace with
`hseinout.add_dst_dir_arg(parser, dst_dir_required=..., dst_dir_default=...)`,
use `args.dst_dir`/`args.overwrite`

### 1.3 File Selection (`helpers.hselect_input_output.add_file_selection_args()`)
Hand-rolled file-selection surfaces (`--files`, `--current_git_files`,
`--modified_files_in_branch`, `--only_files`, dir-walk flags, etc.) that
duplicate `-i/--input`, `--files`, `--from_file`, `--modified`, `--branch`,
`--last_commit`, `--all_files`:

- `dev_scripts_helpers/documentation/count_words.py`
- `dev_scripts_helpers/git/gd_notebook.py`
- `dev_scripts_helpers/llms/dockerized_llm_review.py` (alt. fix vs 1.1)
- `dev_scripts_helpers/notebooks/add_toc_to_notebook.py`
- `dev_scripts_helpers/old/linter/linter.py` (legacy)
- `dev_scripts_helpers/system_tools/replace_text.py`

### 1.4 Multi-file Selection (`helpers.hselect_input_output.add_multi_file_args()`)
- `dev_scripts_helpers/coding_tools/copy_across_clients.py`, `toml_merge.py`
- `dev_scripts_helpers/documentation/concatenate_pdfs.py`
- `dev_scripts_helpers/generate_videos/convert_png_to_movie.py`

### 1.5 File Type Filtering (`helpers.hselect_input_output.add_file_type_filter_args()`)
- `dev_scripts_helpers/old/linter/linter.py` (legacy:
  `--skip_py`/`--only_py`/etc.)
- `dev_scripts_helpers/system_tools/replace_text.py` (`--ext`)

### 1.6 Boolean On/off (`helpers.hparser.add_bool_arg()`)
One-sided `--no_foo`/`--foo` flags, or hand-rolled `dest=`/`store_false` pairs:

- `dev_scripts_helpers/coding_tools/last_cmd.py` (also nullifies
  `--no_report_command_line`, see §1.9)
- `dev_scripts_helpers/documentation/lint_text.py` (x2:
  `use_dockerized_prettier`, `use_dockerized_markdown_toc`)
- `dev_scripts_helpers/git/git_create_issue_and_branch.py`,
  `git_hooks/gitleaks.py`
- `dev_scripts_helpers/llms/compute_llm_query_cost.py` (x3)
- `dev_scripts_helpers/old/create_conda/install/create_conda.py` (legacy, x5,
  has its own `# TODO(gp)` admitting this)
- `dev_scripts_helpers/system_tools/capture_browser_screenshot.py` (x2),
  `capture_iterm_command.py`

### 1.7 Action Selection (`helpers.hselect_action.add_action_arg()`)
Independent boolean "mode" flags or a bare single-`choices` `--action` standing
in for the composable action registry:

- `dev_scripts_helpers/coding_tools/process_prof.py`
- `dev_scripts_helpers/git/git_submodules.py`
- `dev_scripts_helpers/git/git_hooks/install_hooks.py`
- `dev_scripts_helpers/google/gdrive_backup.py` (name collision, incompatible
  semantics)
- `dev_scripts_helpers/old/linter/pre_pr_checklist.py` (legacy)
- `dev_scripts_helpers/system_tools/create_links.py`, `replace_text.py` (name
  collision)

### 1.8 Parallel Processing (`helpers.hjoblib.add_parallel_processing_arg()`)
Hand-rolled `--dry_run`/`--no_incremental` (or `--preview` in place of
`--dry_run`):

- `dev_scripts_helpers/documentation/publish_notes.py`
- `dev_scripts_helpers/download/download_academic_paper_to_md.py`,
  `download_hn_article_to_md.py`, `download_html_to_md.py`,
  `download_link_articles.py`, `download_to_md.py`
- `dev_scripts_helpers/generate_videos/generate_synthesia_videos.py`
- `dev_scripts_helpers/github/dockerized_sync_gh_issue_labels.py`,
  `sync_gh_issue_labels.py`, `dockerized_sync_gh_repo_settings.py`,
  `set_secrets_and_variables.py`, `sync_gh_projects.py`,
  `gh_migration/bulk_transfer_issues.py`
- `dev_scripts_helpers/system_tools/replace_text.py` (`--preview` →
  `--dry_run`), `zip_files.py`, `thin_client/create_all_helpers_links.py` (name
  collision only)

### 1.9 Verbosity / Logger Init (`helpers.hparser.add_verbosity_arg()` + `hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)`)
Missing verbosity arg, missing/malformed `init_logger` call:

- `dev_scripts_helpers/ai/control_cc_commit.py` (no verbosity arg at all)
- `dev_scripts_helpers/coding_tools/find_unused_golden_files.py`, `grsync.py`
  (missing `use_exec_path=True`)
- `dev_scripts_helpers/coding_tools/last_cmd.py` (hardcodes
  `report_command_line=False`)
- `dev_scripts_helpers/git/gd_notebook.py` (missing `use_exec_path=True`)
- `dev_scripts_helpers/github/gh_migration/bulk_transfer_issues.py` (no
  verbosity arg, no `init_logger` call at all)
- `dev_scripts_helpers/llms/llm_cli.py` (delegates `init_logger` to a lib call
  instead of owning it: low severity)
- `dev_scripts_helpers/old/linter/linter_master_report.py`, `linter.py` (legacy;
  missing/positional call)
- `dev_scripts_helpers/system_tools/ffind.py` (conditional on `--log`, should be
  unconditional)
- `dev_scripts_helpers/system_tools/replace_text.py` (positional call, missing
  `use_exec_path=True`)

### 1.10 `_parse() -> ArgumentParser` / `_main(parser)` Skeleton
Returns/accepts a `Namespace` instead of the `parser`, parses args twice, or
otherwise deviates from `script_template.py`:

- `dev_scripts_helpers/ai/cc_script.py`, `control_cc_commit.py`
- `dev_scripts_helpers/aws/am_aws.py` (bug, §0)
- `dev_scripts_helpers/coding_tools/grsync.py`
- `dev_scripts_helpers/docker/print_release_message.py`
- `dev_scripts_helpers/generate_videos/convert_pdf_to_flip_video.py` (bug, §0),
  `download_synthesia_video.py`, `get_synthesia_status.py`,
  `stop_synthesia_videos.py`, `extract_png_from_ppt.py`,
  `generate_elevenlabs_voice.py`, `generate_synthesia_videos.py`
- `dev_scripts_helpers/generate_videos_veo3/get_veo3_status.py`
- `dev_scripts_helpers/git/gsp.py` (`_parser()` → `_parse()` rename only)
- `dev_scripts_helpers/git/git_hooks/install_hooks.py`
- `dev_scripts_helpers/github/dockerized_invite_gh_contributors.py`,
  `invite_gh_contributors.py`, `run_local_ci.py`, `sync_gh_projects.py`,
  `gh_migration/bulk_transfer_issues.py`
- `dev_scripts_helpers/infra/old/ssh_tunnels.py`
- `dev_scripts_helpers/notebooks/ipynb_format.py` (vendored, low priority),
  `old/create_conda/install/print_conda_packages.py`,
  `old/linter/linter_master_report.py`, `old/linter/linter.py`,
  `old/create_conda/_setenv_lib.py` (naming only)
- `dev_scripts_helpers/release_sorrentum/filter_repo/lint_history.py` (vendored,
  low priority)
- `dev_scripts_helpers/testing/pytest_multi_build.py` (double `parse_args()`
  call)

### 1.11 Open (`helpers.hdocker.add_open_arg()`)
7 of 8 `dockerized_*` scripts in `dev_scripts_helpers/dockerize/` use a
byte-for-byte duplicate (`dockerized_utils.add_open_arg`/`open_file_on_macos`)
instead of the canonical `helpers.hdocker` versions, despite already importing
`hdocker` for `add_dockerized_script_arg`: `dockerized_graphviz.py`,
`dockerized_latex.py`, `dockerized_mermaid.py`, `dockerized_pandoc.py`,
`dockerized_prettier.py`, `dockerized_svg_with_inkscape.py`,
`dockerized_svg_with_rsvg_convert.py`, `dockerized_tikz_to_bitmap.py`
`dockerized_typst.py` is missing `--open` entirely (inconsistent with its 7
siblings). Also `dev_scripts_helpers/github/to_github.py` hand-rolls `--open`

Fix: switch all 8 to `hdocker.add_open_arg()`/`hdocker.open_file_on_macos()`;
add `--open` to `dockerized_typst.py`; delete the duplicate functions from
`dockerized_utils.py`

### 1.12 Daemon (`helpers.hdaemon.add_daemon_arg()`)
- `dev_scripts_helpers/documentation/notes_to_pdf.py` (hand-rolled, duplicates
  default help text verbatim)
- `dev_scripts_helpers/github/run_local_ci.py` (name collision, incompatible
  semantics: needs rename, not the helper)

### 1.13 LLM Args (`helpers.hllm_cli.add_llm_args()` / `add_llm_prompt_arg()`)
- `dev_scripts_helpers/llms/compute_llm_query_cost.py`

### 1.14 Naming Style (underscore_case, Not Hyphens)
- `dev_scripts_helpers/llms/ai_review.py`, `llm_transform.py`
  (`-s/--skip-post-transforms`)
- `dev_scripts_helpers/github/gh_migration/bulk_transfer_issues.py`,
  `sync_gh_projects.py` (`--dry-run` and others)
- `dev_scripts_helpers/generate_videos_veo3/get_veo3_status.py`
  (`--operation-ids`), `generate_videos/stop_synthesia_videos.py`
  (`--delete-all`), `extract_png_from_ppt.py`
  (`--extract-images`/`--extract-slides`)
- `dev_scripts_helpers/git/git_hooks/gitleaks.py` (`--no-abort-on-error`)

### 1.15 Minor / Cosmetic (missing `-o`/`-i` Short Alias, Etc.)
- `dev_scripts_helpers/git/git_productivity_metrics.py` (`--output`, no `-o`)
- `dev_scripts_helpers/system_tools/capture_website_screenshot_with_playright.py`
  (`--output`, no `-o`)
- `dev_scripts_helpers/documentation/convert_png_dir_to_movie.py`,
  `extract_gdoc_map.py` (`--output_file` vs `-o/--output`)
- `dev_scripts_helpers/documentation/generate_script_catalog.py`
  (`--src_dir`/`--src_file`/`--dst_file` ad hoc naming)

## 2. Explicitly Out of Scope (recommend Excluding)
- **Git hooks** invoked directly by git, not by a human on the CLI: no
  `argparse`, take positional args from git itself:
  `git/git_hooks/commit-msg.py`, `pre-commit.py`. (`gitleaks.py` and
  `install_hooks.py` _do_ have argparse and stay in scope.)
- **Vendored/upstream code**, not ours to restyle: `notebooks/ipynb_format.py`
  (from `github.com/fg1/ipynb_format`),
  `release_sorrentum/filter_repo/lint_history.py` (git-filter-repo example)
- **`dev_scripts_helpers/old/`**: explicitly legacy/deprecated directory
  (`create_conda/`, `linter/`). 4 files flagged there; recommend leaving as-is
  unless the directory is still actively used

## 3. Proposed Phasing for Step 2
Given ~110 in-scope non-conforming scripts, recommend fixing in this order, each
as its own reviewable commit:

1. **Bugs** (§0): 4 files, fix immediately regardless of anything else
2. **`_parse()`/`_main(parser)` skeleton violations** (§1.10): mechanical,
   low-risk, unblocks consistent verbosity/logger handling everywhere else
3. **Verbosity/logger-init fixes** (§1.9): mechanical
4. **Open/dockerized-open dedup** (§1.11): mechanical, deletes duplicate code
5. **Input/Output, Destination-dir, File-selection, Multi-file,
   File-type-filter** (§1.1–1.5): the bulk of the work; each rename needs its
   callers (other scripts, `invoke` tasks, docs, CI configs) updated to match
6. **Boolean on/off, Action selection, Parallel processing, Daemon, LLM args**
   (§1.6–1.8, 1.12–1.13): same caller-update requirement
7. **Naming/cosmetic** (§1.14–1.15): lowest risk, can batch last

For every renamed/replaced flag, Step 2 must also grep for and update: callers
in other scripts, `invoke` tasks (`helpers/lib_tasks_*.py`), and any markdown
docs referencing the old flag name: per the issue's "update the callers, the
documentation."
