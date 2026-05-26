In all the calls to get_files_to_process use parameters in order and not
by name for the mandatory ones

def get_files_to_process(
    files: str,
    from_file: str,
    modified: bool,
    branch: bool,
    last_commit: bool,
    all_: bool,
    *,
    # TODO(gp): Can mutually_exclusive
    mutually_exclusive: bool = True,
    remove_dirs: bool = False,
    dir_name: str = ".",
) -> List[str]:

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications

- Depending on the type of file to modify follow the rules described in
	`@.claude/rules.md`
