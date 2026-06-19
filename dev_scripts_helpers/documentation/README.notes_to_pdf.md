# Overview

- `notes_to_pdf.py` is a comprehensive document conversion orchestrator that
  transforms markdown/text files into multiple output formats (PDF, HTML,
  presentation slides) using Pandoc/LaTeX/Typst toolchains
- Manages a complete multi-stage pipeline including
  - Preprocessing
  - Image rendering
  - Format conversion
  - Post-processing
- Uses optional Docker containerization for tool isolation
- Converts research notes, lecture materials, and educational content into
  professional-grade documents and presentations
- Users can selectively enable/disable pipeline stages for iterative development
  and debugging

# Architecture (C4 Model)

## C1 (Context)

- This section describes how the system fits in the world

<!--  rendered_images:begin -->
<!--  ```mermaid -->
<!--  graph TB -->
<!--      User["User / CLI"] -->
<!--      InputFile["Input File<br/>(markdown/txt)"] -->
<!--      Pandoc["Pandoc<br/>(conversion engine)"] -->
<!--      LaTeX["LaTeX / pdflatex<br/>(PDF rendering)"] -->
<!--      Typst["Typst<br/>(slide rendering)"] -->
<!--      Docker["Docker<br/>(optional isolation)"] -->
<!--      OutputPDF["PDF Output"] -->
<!--      OutputHTML["HTML Output"] -->
<!--      OutputSlides["Slides Output"] -->
<!--      GoogleDrive["Google Drive<br/>(archive)"] -->
<!--       -->
<!--      User -->|"provides input file"| InputFile -->
<!--      InputFile -->|"notes_to_pdf.py"| Pandoc -->
<!--      Pandoc -->|"for PDF"| LaTeX -->
<!--      Pandoc -->|"for slides-typst"| Typst -->
<!--      LaTeX -->|"via Docker"| Docker -->
<!--      Typst -->|"via Docker"| Docker -->
<!--      LaTeX -->|"generates"| OutputPDF -->
<!--      Pandoc -->|"generates"| OutputHTML -->
<!--      Pandoc -->|"generates"| OutputSlides -->
<!--      OutputPDF -->|"optional copy"| GoogleDrive -->
<!--      OutputHTML -->|"optional copy"| GoogleDrive -->
<!--      OutputSlides -->|"optional copy"| GoogleDrive -->
<!--  ``` -->
<!--  rendered_images:end -->
<!--  render_images:begin -->
![](README.notes_to_pdf.md.figs/README.notes_to_pdf.1.png)
<!--  render_images:end -->

- `notes_to_pdf.py` acts as a central orchestrator, coordinating multiple
  external tools (Pandoc, LaTeX, Typst, Ghostscript) and optional Docker
  containers for tool execution

- Users interact with the CLI, providing input files and output specifications,
  and the module manages the complete workflow including preprocessing,
  rendering, conversion, and post-processing

## C2 (Container)

- This section describes the high-level technical blocks

// TODO(ai_gp): This is too detailed split in different diagrams
<!--  rendered_images:begin -->
<!--  ```mermaid -->
<!--  graph TB -->
<!--      subgraph CLI["CLI Interface"] -->
<!--          Parse["_parse()"] -->
<!--          Main["_main()"] -->
<!--      end -->
<!--       -->
<!--      subgraph Pipeline["Pipeline Orchestration"] -->
<!--          RunAll["_run_all()"] -->
<!--          MarkAction["_mark_action()"] -->
<!--          Cleanup["_cleanup_before()/<br/>_cleanup_after()"] -->
<!--      end -->
<!--       -->
<!--      subgraph Processing["Processing Stages"] -->
<!--          Preprocess["_preprocess_notes()"] -->
<!--          RenderImg["_render_images()"] -->
<!--      end -->
<!--       -->
<!--      subgraph Conversion["Format Converters"] -->
<!--          ToPDF["_run_pandoc_to_pdf()"] -->
<!--          ToHTML["_run_pandoc_to_html()"] -->
<!--          ToSlides["_run_pandoc_to_slides()"] -->
<!--          ToTypstSlides["_run_pandoc_to_typst_slides()"] -->
<!--      end -->
<!--       -->
<!--      subgraph PostProc["Post-Processing"] -->
<!--          Compress["_compress_pdf()"] -->
<!--          CopyOut["_copy_to_output()"] -->
<!--          CopyGDrive["_copy_to_gdrive()"] -->
<!--      end -->
<!--       -->
<!--      subgraph SystemOps["System Operations"] -->
<!--          System["_system()"] -->
<!--          SystemStr["_system_to_string()"] -->
<!--          Log["_log_system()"] -->
<!--          Report["_report_phase()"] -->
<!--          Script["_append_script()"] -->
<!--      end -->
<!--       -->
<!--      Parse -->|"parsed args"| Main -->
<!--      Main -->|"execute pipeline"| RunAll -->
<!--      RunAll -->|"orchestrate actions"| MarkAction -->
<!--      RunAll -->|"cleanup state"| Cleanup -->
<!--      RunAll -->|"execute stages"| Preprocess -->
<!--      RunAll -->|"execute stages"| RenderImg -->
<!--      RunAll -->|"convert format"| ToPDF -->
<!--      RunAll -->|"convert format"| ToHTML -->
<!--      RunAll -->|"convert format"| ToSlides -->
<!--      RunAll -->|"convert format"| ToTypstSlides -->
<!--      RunAll -->|"post-process"| Compress -->
<!--      RunAll -->|"post-process"| CopyOut -->
<!--      RunAll -->|"post-process"| CopyGDrive -->
<!--      ToPDF -->|"system calls"| System -->
<!--      ToHTML -->|"system calls"| SystemStr -->
<!--      Preprocess -->|"logging"| Report -->
<!--      All -->|"script tracking"| Script -->
<!--  ``` -->
<!--  rendered_images:end -->
<!--  render_images:begin -->
![](README.notes_to_pdf.md.figs/README.notes_to_pdf.2.png)
<!--  render_images:end -->

- **Responsibilities:**
  - _CLI Interface_: Argument parsing and main entry point
  - _Pipeline Orchestration_: Manages action selection, sequencing, and phase
    reporting
  - _Processing Stages_: External preprocessing and image rendering via
    subprocess calls
  - _Format Converters_: Format-specific Pandoc command builders and execution
    logic for PDF, HTML, and two slide engines
  - _Post-Processing_: Output finalization, compression, copying, and archival
  - _System Operations_: Wrapper functions for command execution, logging, and
    optional script generation

## C3 (Component)

- Shows the components inside a container

// TODO(ai_gp): Use a different plot style instead of sequenceDiagram
<!--  rendered_images:begin -->
<!--  ```mermaid -->
<!--  sequenceDiagram -->
<!--      participant User -->
<!--      participant CLI as _parse/_main -->
<!--      participant Orchestrator as _run_all -->
<!--      participant Actions as _mark_action -->
<!--      participant Process as _preprocess_notes -->
<!--      participant Images as _render_images -->
<!--      participant Convert as Format Converters -->
<!--      participant PostProc as Post-Processing -->
<!--       -->
<!--      User->>CLI: invoke with args -->
<!--      CLI->>Orchestrator: execute _run_all(args) -->
<!--       -->
<!--      Orchestrator->>Actions: mark 'cleanup_before' -->
<!--      Actions-->>Orchestrator: enabled? -->
<!--      Orchestrator->>Orchestrator: _cleanup_before(prefix) -->
<!--       -->
<!--      Orchestrator->>Orchestrator: filter content (if requested) -->
<!--       -->
<!--      Orchestrator->>Actions: mark 'preprocess_notes' -->
<!--      Actions-->>Orchestrator: enabled? -->
<!--      Orchestrator->>Process: _preprocess_notes() -->
<!--      Process-->>Orchestrator: processed file -->
<!--       -->
<!--      Orchestrator->>Actions: mark 'render_images' -->
<!--      Actions-->>Orchestrator: enabled? -->
<!--      Orchestrator->>Images: _render_images() -->
<!--      Images-->>Orchestrator: rendered file -->
<!--       -->
<!--      Orchestrator->>Actions: mark 'run_pandoc' -->
<!--      Actions-->>Orchestrator: enabled? -->
<!--       -->
<!--      alt type == 'pdf' -->
<!--          Orchestrator->>Convert: _run_pandoc_to_pdf() -->
<!--      else type == 'html' -->
<!--          Orchestrator->>Convert: _run_pandoc_to_html() -->
<!--      else type == 'slides' -->
<!--          Orchestrator->>Convert: _run_pandoc_to_slides() or _run_pandoc_to_typst_slides() -->
<!--      end -->
<!--      Convert-->>Orchestrator: output file -->
<!--       -->
<!--      Orchestrator->>PostProc: _compress_pdf() (if enabled) -->
<!--      PostProc-->>Orchestrator: compressed file -->
<!--       -->
<!--      Orchestrator->>PostProc: _copy_to_output() -->
<!--      PostProc-->>Orchestrator: final output path -->
<!--       -->
<!--      Orchestrator->>PostProc: _copy_to_gdrive() (if enabled) -->
<!--       -->
<!--      Orchestrator->>Orchestrator: _cleanup_after (if enabled) -->
<!--       -->
<!--      Orchestrator-->>User: success -->
<!--  ``` -->
<!--  rendered_images:end -->
<!--  render_images:begin -->
![](README.notes_to_pdf.md.figs/README.notes_to_pdf.3.png)
<!--  render_images:end -->

- **Key Component Interactions:**
  1. _Action Selection_: `_mark_action()` returns whether an action should
     execute, managing state across the pipeline
  2. _File Threading_: Each processing stage receives an input file path and
     returns an output path for the next stage
  3. _System Command Wrapping_: All external tools invoked through `_system()`
     and `_system_to_string()` for consistent logging
  4. _Script Logging_: Commands optionally appended to a bash script via global
     `_SCRIPT` list

## C4 (Code)

- This section shows how components are implemented

- **Primary Call Flow:**
  ```
  _main() 
    - _run_all(args)
      - _cleanup_before()
      - _preprocess_notes()
        - _render_images()
      - [_run_pandoc_to_pdf() | _run_pandoc_to_html() | _run_pandoc_to_slides() | _run_pandoc_to_typst_slides()]
      - _compress_pdf() [optional]
      - _copy_to_output()
        - _copy_to_gdrive() [optional]
      - _cleanup_after() [optional]
  ```

- **Function List**

// TODO(ai_gp): Remove signature column

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_run_all(args)` | `_run_all(args: argparse.Namespace) -> None` | Main orchestrator; manages entire pipeline execution and action sequencing |
| `_preprocess_notes()` | `_preprocess_notes(file_name: str, prefix: str, type_: str, toc_type: str) -> str` | Calls external preprocessor script; returns processed file path |
| `_render_images()` | `_render_images(file_name: str, prefix: str) -> str` | Renders inline diagram/image specs; filters commented code; returns file path |
| `_run_pandoc_to_pdf()` | `_run_pandoc_to_pdf(curr_path: str, file_name: str, prefix: str, toc_type: str, no_run_latex_again: bool, use_host_tools: bool, dockerized_force_rebuild: bool, dockerized_use_sudo: bool, *, tex_only: bool = False) -> str` | Converts markdown → LaTeX → PDF via Pandoc and pdflatex (2 passes); returns PDF path |
| `_run_pandoc_to_html()` | `_run_pandoc_to_html(file_in: str, prefix: str, toc_type: str) -> str` | Converts markdown to HTML via Pandoc; returns HTML path |
| `_run_pandoc_to_slides()` | `_run_pandoc_to_slides(file_name: str, toc_type: str, use_host_tools: bool, dockerized_force_rebuild: bool, dockerized_use_sudo: bool, *, debug: bool = False, tex_only: bool = False) -> str` | Converts markdown to Beamer PDF slides; returns PDF path or .tex if `tex_only=True` |
| `_run_pandoc_to_typst_slides()` | `_run_pandoc_to_typst_slides(curr_path: str, file_name: str, use_host_tools: bool, dockerized_force_rebuild: bool, dockerized_use_sudo: bool, *, typst_only: bool = False) -> str` | Converts markdown → Typst/Touying → PDF slides; returns PDF path or .typ if `typst_only=True` |
| `_compress_pdf()` | `_compress_pdf(file_name: str) -> str` | Compresses PDF via ghostscript; in-place modification; returns file path |
| `_copy_to_output()` | `_copy_to_output(file_in: str, output: str) -> str` | Copies processed file to output location; returns output path |
| `_copy_to_gdrive()` | `_copy_to_gdrive(file_name: str, ext: str, input_: str, gdrive_dir: str) -> None` | Copies output to Google Drive archive directory |
| `_cleanup_before()` | `_cleanup_before(prefix: str) -> None` | Removes intermediate files matching prefix pattern and cache files |
| `_cleanup_after()` | `_cleanup_after(prefix: str) -> None` | Removes intermediate files matching prefix pattern |
| `_system()` | `_system(cmd: str, *, log_level: int = logging.DEBUG, **kwargs: Any) -> int` | Executes shell command; logs output; optionally appends to script; returns exit code |
| `_system_to_string()` | `_system_to_string(cmd: str, *, log_level: int = logging.DEBUG, **kwargs: Any) -> Tuple[int, str]` | Executes shell command; captures stdout; returns (exit_code, output) |

- **Notable Code Patterns:**

  1. _Global Script Accumulation_: The `_SCRIPT` global list accumulates all
     executed commands if `--script` flag is used, enabling script generation for
     reproducibility.

  2. _File Path Staging_: Each processing function takes input file path and
     returns output path, creating a pipeline of transformations:
     ```
     - original.txt 
     - tmp.preprocess_notes.txt
     - tmp.render_image2.txt
     - tmp.tex (or .html, .pdf)
     - output.pdf (final)
     ```

  3. _Docker Containerization_: Functions like `_run_pandoc_to_pdf()` check
     `use_host_tools` flag and conditionally wrap commands via
     `dshdlipa.run_dockerized_pandoc()` and `dshdlila.run_dockerized_latex()`.

  4. _Two-Pass LaTeX Compilation_: PDF generation runs `pdflatex` twice by
     default (controlled by `no_run_latex_again` flag) to resolve
     cross-references.

  5. _Multiple Slide Engines_: `--slides_engine` flag switches between Beamer
     (LaTeX-based) and Typst/Touying engines, with engine-specific command
     building and compilation logic.

  6. _Common Pandoc Options_: Shared options stored in `_COMMON_PANDOC_OPTS` list
     (margins, highlighting, numbering) to ensure consistency across PDF and HTML
     converters.

- **External Dependencies**

| Module | Purpose |
|--------|---------|
| `helpers.hdbg` | Assertions and debugging (dassert_*, init_logger) |
| `helpers.hio` | File I/O (from_file, to_file, create_dir) |
| `helpers.hgit` | Git operations (find_file to locate helper scripts) |
| `helpers.hmarkdown` | Markdown processing (filter_by_header, filter_by_slides, process_single_line_comment) |
| `helpers.hopen` | File opening utilities (open_file) |
| `helpers.hdocker` | Docker CLI integration (add_dockerized_script_arg) |
| `helpers.hparser` | Argument parsing utilities (add_verbosity_arg) |
| `helpers.hselect_action` | Action state management (mark_action, select_actions, actions_to_string) |
| `helpers.hprint` | Colored output and formatting (color_highlight, frame, func_signature_to_str) |
| `helpers.hsystem` | System command execution (system, system_to_string) |
| `dev_scripts_helpers.dockerize.lib_latex` | LaTeX Docker wrapper (run_dockerized_latex) |
| `dev_scripts_helpers.dockerize.lib_pandoc` | Pandoc Docker wrapper (run_dockerized_pandoc) |
| `dev_scripts_helpers.dockerize.lib_typst` | Typst Docker wrapper (run_dockerized_typst) |
| External CLI tools | `pandoc`, `pdflatex`, `typst`, `/opt/homebrew/bin/gs` (ghostscript) |

# Critique and Improvements

## Strengths

- **Modular Pipeline Design**: Action-based architecture allows users to
  selectively enable/disable stages for iterative development and debugging
  without re-running expensive operations.
- **Dual-Engine Slide Support**: Supports both Beamer (LaTeX-based) and
  Typst/Touying engines (single Typst pass vs two LaTeX passes).
- **Optional Containerization**: Docker support with `use_host_tools` flag
  enables tool isolation while remaining optional for faster development on local
  machines.
- **Script Logging**: Optional `--script` flag generates reproducible bash script
  from executed commands for debugging and documentation.
- **Comprehensive Filtering**: Supports filtering by header, line range, slide
  range, and slide name before processing, enabling partial document generation
  for testing.
- **Rich CLI Interface**: Well-structured argparse with action flags, docker
  options, and format-specific parameters (e.g., `toc_type`, `slides_engine`).

## Weaknesses & Assumptions

1. **Hardcoded Ghostscript Path**: `/opt/homebrew/bin/gs` is hardcoded
   for macOS homebrew. This fails on Linux or different macOS installations.
   - **Fact**: Line 604 has hardcoded path
   - **Impact**: `_compress_pdf()` will crash if ghostscript is not at this exact location

2. **Global Mutable State**: `_SCRIPT = None` used as global
   accumulator. This is fragile if the module is imported or called multiple
   times in the same process.
   - **Assumption**: Assumed single execution per process

3. **Silent LaTeX Failures on Comment Processing**:
   `_render_images()` silently removes commented lines from `render_images.py`
   output but doesn't validate that images were actually rendered. If image
   rendering fails, the pipeline continues with incomplete content.
   - **Fact**: No validation of image existence after `_render_images()`

4. **No Retry Logic for External Tools**: If `pdflatex` fails intermittently
   (e.g., due to temporary Docker issues), there's no retry mechanism. Users must
   manually re-run the entire pipeline.

5. **File Path Assumptions**: Code assumes `os.path.basename()` and simple
   `.replace('.tex', '.pdf')` work correctly. Edge case: files with multiple dots
   in names (e.g., `file.v1.2.txt`) may fail.
   - **Assumption**: Filenames follow simple naming convention

6. **Hardcoded Google Drive Directory**: Default path
   `/Users/saggese/GoogleDrive/pdf_notes` is user-specific and won't work on
   other systems.
