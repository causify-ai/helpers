"""
Import as:

import helpers.hunit_test_purification as huntepur
"""

import datetime
import logging
import os
import re
from typing import List, Tuple

import helpers.hgit as hgit
import helpers.hintrospection as hintros
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Mute this module unless we want to debug it.
_LOG.setLevel(logging.INFO)


# #############################################################################
# Purification functions
# #############################################################################


def purify_txt_from_client(txt: str) -> str:
    """
    Apply all purification steps to the input text.

    :param txt: input text to purify
    :return: purified text
    """
    # The order of substitutions is important. We want to start from the "most
    # specific" (e.g., `amp/helpers/test/...`) to the "least specific" (e.g.,
    # `amp`).
    txt = purify_directory_paths(txt)
    txt = purify_from_environment(txt)
    # Correct order: -> `app` -> `amp` ->
    # Start with `app.amp.helpers_root.helpers...`
    # After purifying app references -> `amp.helpers_root.helpers...`
    # After purifying amp references -> `helpers_root.helpers...`
    #
    # Incorrect order: -> `amp` -> `app` ->
    # Start with `amp.helpers_root.helpers...`
    # After purifying `amp` references -> `app.amp.helpers_root.helpers...`
    # After purifying `app` references -> `amp.helpers_root.helpers...`
    #
    txt = purify_app_references(txt)
    txt = purify_amp_references(txt)
    txt = purify_from_env_vars(txt)
    txt = purify_object_representation(txt)
    txt = purify_today_date(txt)
    txt = purify_white_spaces(txt)
    txt = purify_parquet_file_names(txt)
    txt = purify_helpers(txt)
    txt = purify_docker_cmd(txt)
    txt = purify_docker_image_name(txt)
    txt = purify_apple_container_output(txt)
    return txt


def purify_directory_paths(txt: str) -> str:
    """
    Replace known directory paths with standardized placeholders.

    Apply replacements in this order:
    1. Replace Git root paths with `$GIT_ROOT`.
    2. Replace `CSFY_HOST_GIT_ROOT_PATH` with `$CSFY_HOST_GIT_ROOT_PATH`.
    3. Replace current working directory with `$PWD`.

    :param txt: input text that needs to be purified
    :return: purified text
    """
    _LOG.debug("Before: txt='\n%s'", txt)
    # Collect all paths to replace with their priorities.
    replacements = []
    # 1. Git root paths.
    # Remove references to Git modules starting from the innermost one.
    for super_module in [False, True]:
        # Replace the git root path with `$GIT_ROOT`.
        git_root = hgit.get_client_root(super_module=super_module)
        if git_root and git_root != "/":
            replacements.append((git_root, "$GIT_ROOT"))
            _LOG.debug("Added git root '%s' for replacement", git_root)
        else:
            # Skip git root path if it is `/`.
            pass
    # 2. CSFY_HOST_GIT_ROOT_PATH environment variable.
    # Replace the CSFY_HOST_GIT_ROOT_PATH with `$CSFY_HOST_GIT_ROOT_PATH`.
    csfy_git_root = os.environ.get("CSFY_HOST_GIT_ROOT_PATH")
    if csfy_git_root:
        replacements.append((csfy_git_root, "$CSFY_HOST_GIT_ROOT_PATH"))
        _LOG.debug(
            "Added CSFY_HOST_GIT_ROOT_PATH '%s' for replacement",
            csfy_git_root,
        )
    # 3. Current working directory.
    # Replace the path of current working directory with `$PWD`.
    pwd = os.getcwd()
    if pwd and pwd != "/":
        replacements.append((pwd, "$PWD"))
        _LOG.debug("Added PWD '%s' for replacement", pwd)
    # Apply replacements in order of priority.
    for path, replacement in replacements:
        # Use word boundaries to avoid replacing path fragments.
        # E.g., To avoid replacing `app` in `application.py`.
        pattern = rf"(?<![\w/]){re.escape(path)}(?![\w])"
        txt = re.sub(pattern, replacement, txt)
        _LOG.debug("Replaced '%s' with '%s'", path, replacement)
    _LOG.debug("After purifying directory paths: txt='\n%s'", txt)
    return txt


def purify_from_environment(txt: str) -> str:
    """
    Replace environment-specific values with placeholders.

    Perform these transformations:
    1. Replace directory paths with standardized placeholders.
    2. Replace the current user name with $USER_NAME.
    3. Handle special cases like usernames in paths and commands.

    :param txt: input text that needs to be purified
    :return: purified text
    """
    # Replace current username with `$USER_NAME`.
    user_name = hsystem.get_user_name()
    # Set a regex pattern that finds a user name surrounded by dot, dash or space.
    # E.g., `IMAGE=$CSFY_ECR_BASE_PATH/amp_test:local-$USER_NAME-1.0.0`,
    # `--name $USER_NAME.amp_test.app.app`, `run --rm -l user=$USER_NAME`.
    regex = rf"([\s\n\-\.\=]|^)+{user_name}+([.\s/-]|$)"
    # Use `\1` and `\2` to preserve specific characters around `$USER_NAME`.
    target = r"\1$USER_NAME\2"
    txt = re.sub(regex, target, txt)
    _LOG.debug("After %s: txt='\n%s'", hintros.get_function_name(), txt)
    return txt


def _apply_regex_replacements(
    txt: str, regex_patterns: List[Tuple[str, str]]
) -> str:
    """
    Apply a series of regex replacements to text.

    :param txt: input text to process
    :param regex_patterns: list of (pattern, replacement) tuples to
        apply in order
    :return: text with all regex replacements applied
    """
    # Apply regex replacements in order.
    txt_out = txt
    for regex_pattern, replacement in regex_patterns:
        txt_out = re.sub(regex_pattern, replacement, txt_out)
        _LOG.debug(
            "Applying %s -> %s: before=%s, after=%s",
            regex_pattern,
            replacement,
            txt,
            txt_out,
        )
    return txt_out


def purify_amp_references(txt: str) -> str:
    """
    Remove references to amp from text by applying a series of regex
    substitutions.

    Handle these patterns:
    1. Replace path references
       - E.g., "amp/helpers/test/..." -> "helpers/test/..."
    2. Replace class references
       - E.g., "<amp.helpers.test.TestClass>" -> "<helpers.test.TestClass>"
    3. Replace comment references
       - E.g., "# Test created for amp.helpers.test" -> "# Test created for helpers.test"
    4. Replace module references
       - E.g., "amp.helpers.test.TestClass" -> "helpers.test.TestClass"

    :param txt: input text containing amp references
    :return: text with amp references removed
    """
    amp_patterns = [
        # Remove 'amp/' prefix from quoted paths.
        (r"'amp/", "'"),
        # Remove 'amp/' prefix from path segments.
        (r"(?m)(^\s*|\s+)amp/", r"\1"),
        # Replace '/amp/' with '/' and '/amp:' with ':' in paths.
        (r"(?m)/amp/", "/"),
        (r"(?m)/amp:", ":"),
        # Remove 'amp.' prefix from class representations and tracebacks.
        (r"<amp\.", "<"),
        (r"class 'amp\.", "class '"),
        # Replace 'amp.helpers' with 'helpers' in package references.
        (r"\bamp\.helpers\b", "helpers"),
        # Replace 'amp.app.helpers_root' with 'helpers'.
        (r"\bamp\.app\.helpers_root\b", "helpers"),
        # Remove amp references from test creation comments.
        (r"# Test created for amp\.([\w\.]+)", r"# Test created for \1"),
        # Remove leading './' from relative paths.
        (r"(?m)^\./", ""),
    ]
    txt = _apply_regex_replacements(txt, amp_patterns)
    _LOG.debug("After %s: txt=\n%s", hintros.get_function_name(), txt)
    return txt


def purify_app_references(txt: str) -> str:
    """
    Remove references to `/app` from text by applying a series of regex
    substitutions.

    :param txt: input text containing app references
    :return: text with app references removed
    """
    app_patterns = [
        # Replace the `/app` Docker mount point (the container's mirror of
        # the Git root, e.g. `--workdir /app`) with `$GIT_ROOT`.
        (r"(?<![\w/])/app(?=/)", "$GIT_ROOT"),
        (r"(?<![\w/])/app(?=\s|$)", "$GIT_ROOT"),
        # Remove trailing '/app/' references.
        (r"(?<![\w/])/app/(?=\s|$)", ""),
        # Remove 'app/' prefix from path segments.
        (r"(?m)(^\s*'?)app/", r"\1"),
        # Replace '/app/' with '/' and '/app:' with ':' in paths.
        (r"(?m)/app/", "/"),
        (r"(?m)/app:", ":"),
        # Remove 'app.' prefix from class representations and tracebacks.
        (r"<app\.", "<"),
        (r"class 'app\.", "class '"),
        # Replace 'app.helpers' with 'helpers' in package references.
        (r"\bapp\.helpers\b", "helpers"),
        # Remove app references from test creation comments.
        (r"# Test created for app\.([\w\.]+)", r"# Test created for \1"),
        # Update legacy module path forms to use amp.helpers.
        (r"app\.amp\.helpers_root\.helpers", "amp.helpers"),
        (r"app\.amp\.helpers", "amp.helpers"),
        #
        (r"/helpers_root", ""),
        # Remove leading './' from relative paths.
        (r"(?m)^\./", ""),
    ]
    txt = _apply_regex_replacements(txt, app_patterns)
    _LOG.debug("After %s: txt=\n%s", hintros.get_function_name(), txt)
    return txt


def purify_from_env_vars(txt: str) -> str:
    """
    Replace environment variable values with their variable names.

    :param txt: input text containing environment variable values
    :return: text with environment variable values replaced
    """
    for env_var in [
        "CSFY_AWS_S3_BUCKET",
        "CSFY_ECR_BASE_PATH",
    ]:
        if env_var in os.environ:
            val = os.environ[env_var]
            if val == "":
                _LOG.debug("Env var '%s' is empty", env_var)
            else:
                txt = txt.replace(val, f"${env_var}")
    _LOG.debug("After %s: txt='\n%s'", hintros.get_function_name(), txt)
    return txt


def purify_object_representation(txt: str) -> str:
    """
    Remove references like `at 0x7f43493442e0`.

    :param txt: input text containing object representations
    :return: text with object representations standardized
    """
    object_patterns = [
        (r"at 0x[0-9A-Fa-f]+", "at 0x"),
        (r" id='\d+'>", " id='xxx'>"),
        (r"port=\d+", "port=xxx"),
        (r"host=\S+ ", "host=xxx "),
        (
            r"wall_clock_time=Timestamp\('.*?',",
            r"wall_clock_time=Timestamp('xxx',",
        ),
    ]
    txt = _apply_regex_replacements(txt, object_patterns)
    _LOG.debug("After %s: txt='\n%s'", hintros.get_function_name(), txt)
    return txt


def purify_today_date(txt: str) -> str:
    """
    Remove today's date like `20220810`.

    :param txt: input text containing dates
    :return: text with dates standardized
    """
    today_date = datetime.date.today()
    today_date_as_str = today_date.strftime("%Y%m%d")
    # Replace predict.3.compress_tails.df_out.20220627_094500.YYYYMMDD_171106.csv.gz.
    txt = re.sub(
        today_date_as_str + r"_\d{6}",
        "YYYYMMDD_HHMMSS",
        txt,
        flags=re.MULTILINE,
    )
    txt = re.sub(today_date_as_str, "YYYYMMDD", txt, flags=re.MULTILINE)
    return txt


def purify_white_spaces(txt: str) -> str:
    """
    Remove trailing white spaces.

    :param txt: input text with whitespace
    :return: text with standardized whitespace
    """
    txt_new = []
    for line in txt.split("\n"):
        line = line.rstrip()
        txt_new.append(line)
    txt = "\n".join(txt_new)
    return txt


def purify_line_number(txt: str) -> str:
    """
    Replace line number with `$LINE_NUMBER`.

    :param txt: input text containing line numbers
    :return: text with line numbers standardized
    """
    txt = re.sub(r"\.py::\d+", ".py::$LINE_NUMBER", txt, flags=re.MULTILINE)
    return txt


def purify_parquet_file_names(txt: str) -> str:
    """
    Replace UUIDs file names to `data.parquet` in the golden outcomes.

    :param txt: input text containing parquet file names
    :return: text with standardized parquet file names
    """
    pattern = r"""
        [0-9a-f]{32}-[0-9].*    # GUID pattern.
        (?=\.parquet)           # positive lookahead assertion that matches a
                                # position followed by ".parquet" without
                                # consuming it.
    """
    # TODO(Vlad): Need to change the replacement to `$FILE_NAME` as in the
    # `purify_from_environment()` function. For now, some tests are expecting
    # `data.parquet` files.
    replacement = "data"
    # flags=re.VERBOSE allows us to use whitespace and comments in the pattern.
    txt = re.sub(pattern, replacement, txt, flags=re.VERBOSE)
    return txt


def purify_helpers(txt: str) -> str:
    """
    Replace the path `helpers_root.helpers` with `helpers`.

    :param txt: input text containing helper references
    :return: text with standardized helper references
    """
    txt = re.sub(
        r"helpers_root\.helpers\.", "helpers.", txt, flags=re.MULTILINE
    )
    txt = re.sub(
        r"helpers_root/helpers/", "helpers/", txt, flags=re.MULTILINE
    )
    txt = re.sub(
        r"helpers_root\.config_root", "config_root", txt, flags=re.MULTILINE
    )
    txt = re.sub(
        r"helpers_root/config_root/", "config_root/", txt, flags=re.MULTILINE
    )
    txt = re.sub(
        r"helpers_root/dev_scripts_helpers/",
        "dev_scripts_helpers/",
        txt,
        flags=re.MULTILINE,
    )
    return txt


def purify_docker_image_name(txt: str) -> str:
    """
    Remove temporary docker image name.

    :param txt: input text containing docker image names
    :return: text with standardized docker image names
    """
    # Purify command like:
    # > docker run --rm ...  tmp.latex.edb567be ..
    # > ... tmp.latex.aarch64.2f590c86.2f590c86
    # > container run --rm ... tmp.latex.arm64.417056b0 ..
    # > $DOCKER_EXECUTABLE run --rm ... tmp.latex.arm64.417056b0 ..
    # Note: `docker`/`container` may have already been normalized to
    # `$DOCKER_EXECUTABLE` by `purify_docker_cmd()`, which runs before
    # this function, so both forms need to be recognized.
    # E.g., `tmp.pandoc_texlive.aarch64.9a4bae9a` becomes
    # `tmp.pandoc_texlive.$ARCH.$CONTAINER_ID`.
    # Handle the double-hash pattern first (e.g.,
    # `tmp.latex.aarch64.2f590c86.2f590c86`), since it is a special case
    # of the single-hash pattern below: matching it first prevents the
    # single-hash regex from only collapsing the trailing hash and
    # leaving the leading one behind.
    pattern = r"""
        ^                            # Start of line
        (                            # Start capture group 1
            .*(?:docker|container|   # Any text containing "docker" or
            \$DOCKER_EXECUTABLE).*   # "container" (the Apple engine CLI)
                                     # or the normalized placeholder
            \s+                      # One or more whitespace
            tmp\.\S+\.\S+\.          # tmp.something.something.
        )                            # End capture group 1
        [a-z0-9]{8}                  # 8 character hex hash
        \.                           # Literal dot
        [a-z0-9]{8}                  # Another 8 character hex hash
        (                            # Start capture group 2
            \s+                      # One or more whitespace
            .*                       # Rest of the line
        )                            # End capture group 2
        $                            # End of line
    """
    txt = re.sub(
        pattern,
        r"\1$CONTAINER_ID\2",
        txt,
        flags=re.MULTILINE | re.VERBOSE,
    )
    pattern = r"""
        ^                            # Start of line
        (                            # Start capture group 1
            .*(?:docker|container|   # Any text containing "docker" or
            \$DOCKER_EXECUTABLE).*   # "container" (the Apple engine CLI)
                                     # or the normalized placeholder
            \s+                      # One or more whitespace
            tmp\.\S+\.               # tmp.something.
        )                            # End capture group 1
        [a-z0-9]{8}                  # 8 character hex hash
        (                            # Start capture group 2
            \s+                      # One or more whitespace
            .*                       # Rest of the line
        )                            # End capture group 2
        $                            # End of line
    """
    txt = re.sub(
        pattern,
        r"\1$CONTAINER_ID\2",
        txt,
        flags=re.MULTILINE | re.VERBOSE,
    )
    # Normalize the CPU architecture tag (e.g., `aarch64` on Linux vs.
    # `arm64` on macOS) that precedes the container ID placeholder, so
    # golden files are stable across machines with different
    # architecture-naming conventions.
    txt = re.sub(
        r"\.(?:aarch64|arm64|x86_64|amd64)\.\$CONTAINER_ID",
        ".$ARCH.$CONTAINER_ID",
        txt,
    )
    return txt


def purify_docker_cmd(txt: str) -> str:
    """
    Normalize a Docker/Apple `container` run command for golden
    comparisons.

    This handles two sources of environment-dependent variance in
    commands built by `hdocker.get_docker_base_cmd()`:
    - The executable is `docker` on Linux/CI and `container` on macOS
      (Apple engine), e.g. `docker run --rm ...` vs
      `container run --rm ...`.
    - The `-e VAR` flags list the env vars currently set in the host
      environment (`AM_*`, `CK_*`, `CSFY_*`, `*_API_KEY`), which differs
      across machines and can also be wrapped across multiple lines.

    E.g.,
    ```
    docker run --rm --user $(id -u):$(id -g) -e CSFY_AWS_PROFILE -e CSFY_ECR_BASE_PATH --workdir ...
    ```
    and
    ```
    container run --rm --user $(id -u):$(id -g)
    -e AM_GDRIVE_PATH
    -e CSFY_HOST_NAME --workdir ...
    ```
    both become
    ```
    $DOCKER_EXECUTABLE run --rm --user $(id -u):$(id -g) -e ... --workdir ...
    ```

    :param txt: input text containing Docker/container run commands
    :return: text with the run command normalized
    """
    # Normalize the executable name.
    pattern = r"""
        \b(?:docker|container)\b     # "docker" (Linux/CI) or "container"
                                     # (Apple engine CLI on macOS)
        (?=                          # Lookahead: only if followed by
            \s+run\s+--rm\s+--user\s+       # the `run --rm --user`
            \$\(id\s+-u\):\$\(id\s+-g\)     # invocation with the
                                            # `$(id -u):$(id -g)` flag
        )
    """
    txt = re.sub(
        pattern,
        "$DOCKER_EXECUTABLE",
        txt,
        flags=re.MULTILINE | re.VERBOSE,
    )
    # Collapse the `-e VAR` flags (which may be wrapped across multiple
    # lines) into a single placeholder.
    pattern = r"""
        (                            # Start capture group 1
            \$DOCKER_EXECUTABLE      # Already-normalized executable
            \s+run\s+--rm\s+--user\s+       # `run --rm --user`
            \$\(id\s+-u\):\$\(id\s+-g\)     # `$(id -u):$(id -g)` flag
        )                            # End capture group 1
        (?:                          # Start non-capture group
            \s+-e\s+\S+              # First `-e VAR` flag
            (?:\s+-e\s+\S+)*         # Additional `-e VAR` flags
        )                            # End non-capture group
    """
    txt = re.sub(
        pattern,
        r"\1 -e ...",
        txt,
        flags=re.MULTILINE | re.VERBOSE,
    )
    return txt


def purify_apple_container_output(txt: str) -> str:
    """
    Remove Apple container startup progress lines from output.

    These lines are printed by the Apple container runtime during boot.
    Examples:
    - [0/6] [0s]
    - [1/6] Fetching image [0s]
    - [2/6] Unpacking image [0s]
    - [6/6] Starting container [0s]

    :param txt: input text containing container output
    :return: text with container startup lines removed
    """
    # Match lines starting with a `[step/total]` progress marker, e.g.
    # `[0/6]` or `[1/6] Fetching image [0s]`. This avoids matching unrelated
    # bracketed content, e.g. `['helpers/test/test_file.py']`.
    progress_line_pattern = re.compile(r"^\[\d+/\d+\]")
    lines = txt.split("\n")
    filtered_lines = [
        line for line in lines if not progress_line_pattern.match(line)
    ]
    return "\n".join(filtered_lines)


# #############################################################################


def purify_file_names(file_names: List[str]) -> List[str]:
    """
    Express file names in terms of the root of git repo, removing reference
    to `amp`.
    """
    git_root = hgit.get_client_root(super_module=True)
    file_names = [os.path.relpath(f, git_root) for f in file_names]
    # Apply amp reference purification to file paths.
    file_names = list(map(purify_amp_references, file_names))
    return file_names


def purify_text(txt: str) -> str:
    """
    Purify text by removing environment-specific information and standardizing
    output for test comparisons.
    """
    return purify_txt_from_client(txt)
