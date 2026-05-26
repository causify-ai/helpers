Factor out in helpers/hparser.py the logic to add the command line arguments like

  :param file_types: a comma-separated list of extensions to check, e.g.,
      'csv,py'. An empty string means keep all the extensions
  :param skip_file_types: a comma-separated list of extensions to skip, e.g.,
      'txt'. An empty string means do not skip any extension

and the logic to parse it

- Update the unit tests

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- Depending on the type of file to modify follow the rules described in
	`@.claude/rules.md`
