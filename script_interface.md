

# File selection options (--files, --from_file, --branch, --modified, etc.).
hseinout.add_file_selection_args(parser)

  -i, --input FILE      Select a single file

  --files FILES
                        Select specific files (space-separated list in a single argument)
  --from_file FROM_FILE
                        Path to file containing one file path per line
  --modified            Select only files modified in the client (staged and unstaged)
  --branch              Select only files modified with respect to the branch point
  --last_commit         Select only files part of the previous commit
  --all                 Select all repo files

  -o, --output FILE
  --output_dir ...
  --output_file

    # File type filtering options (--file_types, --skip_file_types).
    hseinout.add_file_type_filter_args(parser, file_types_default="py,ipynb,md")
  --file_types FILE_TYPES
                        Comma-separated list of file extensions to process (e.g., 'py,ipynb,md,txt') Available: py (Python), ipynb (Jupyter), md (Markdown), txt (Text) Default: 'py,ipynb,md'
  --skip_file_types SKIP_FILE_TYPES
                        Comma-separated list of file extensions to skip (e.g., 'txt') Empty string means skip no extensions

  --dry_run             ...
  -v {TRACE,DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
  --no_report_command_line
                        Disable printing of executed commands
