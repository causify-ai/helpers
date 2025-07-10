import logging
import re

import dev_scripts_helpers.llms.llm_prompts as dshlllpr
import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hmarkdown as hmarkdo
import helpers.hprint as hprint


_LOG = logging.getLogger(__name__)


# TODO(gp): Move this to somewhere else, `hdocker_utils.py`?
def _convert_file_names(in_file_name: str, out_file_name: str) -> None:
    """
    Convert the files from inside the container to outside.

    Replace the name of the file inside the container (e.g.,
    `/app/helpers_root/tmp.llm_transform.in.txt`) with the name of the
    file outside the container.
    """
    # TODO(gp): We should use the `convert_caller_to_callee_docker_path`
    txt_out = []
    txt = hio.from_file(out_file_name)
    for line in txt.split("\n"):
        if line.strip() == "":
            continue
        # E.g., the format is like
        # ```
        # /app/helpers_root/r.py:1: Change the shebang line to `#!/usr/bin/env python3` to e
        # ```
        _LOG.debug("before: %s", hprint.to_str("line in_file_name"))
        line = re.sub(r"^.*(:\d+:.*)$", rf"{in_file_name}\1", line)
        _LOG.debug("after: %s", hprint.to_str("line"))
        txt_out.append(line)
    txt_out = "\n".join(txt_out)
    hio.to_file(out_file_name, txt_out)


def run_post_transforms(
    prompt: str,
    compare: bool,
    in_file_name: str,
    tmp_in_file_name: str,
    tmp_out_file_name: str,
) -> str:
    """
    Run post-transforms on the transformed text.

    Note that we need to run this outside the `llm_transform` container to
    avoid to do docker-in-docker in the `llm_transform` container (which
    doesn't support that).

    :param prompt: Prompt used to generate the transformed text
    :param compare: Whether to print the original and transformed text
    :param in_file_name: Original input file name
    :param tmp_in_file_name: Temporary input file name
    :param tmp_out_file_name: Temporary output file name
    :return: Text after applying post-transforms
    """
    post_container_transforms = dshlllpr.get_post_container_transforms(
        prompt
    )
    #
    if dshlllpr.to_run("convert_file_names", post_container_transforms):
        _convert_file_names(in_file_name, tmp_out_file_name)
    #
    out_txt = hio.from_file(tmp_out_file_name)
    if dshlllpr.to_run("prettier_markdown", post_container_transforms):
        # Note that we need to run this outside the `llm_transform`
        # container to avoid to do docker-in-docker in the `llm_transform`
        # container (which doesn't support that).
        out_txt = hmarkdo.prettier_markdown(out_txt)
    #
    if dshlllpr.to_run("format_markdown", post_container_transforms):
        # Same as `prettier_markdown`.
        out_txt = hmarkdo.md_clean_up(out_txt)
        out_txt = hmarkdo.format_markdown(out_txt)
    #
    if dshlllpr.to_run("format_latex", post_container_transforms):
        # Same as `prettier_markdown`.
        out_txt = hmarkdo.md_clean_up(out_txt)
        out_txt = hmarkdo.format_markdown(out_txt)
    #
    if dshlllpr.to_run("format_slide", post_container_transforms):
        # Same as `prettier_markdown`.
        out_txt = hmarkdo.md_clean_up(out_txt)
        out_txt = hmarkdo.format_markdown_slide(out_txt)
    #
    if dshlllpr.to_run("append_to_text", post_container_transforms):
        out_txt_tmp = []
        # Append the original text.
        txt = hio.from_file(tmp_in_file_name)
        out_txt_tmp.append(txt)
        # Append the transformed text.
        out_txt_tmp.append("\n#### Comments ####")
        out_txt_tmp.append(out_txt)
        # Join everything.
        out_txt = "\n".join(out_txt_tmp)
    # Check that all post-transforms were run.
    hdbg.dassert_eq(
        len(post_container_transforms),
        0,
        "Not all post_transforms were run: %s",
        post_container_transforms,
    )
    # Save the original and transformed text on file and a script to compare
    # them.
    txt = hio.from_file(tmp_in_file_name)
    hio.to_file("tmp.llm_original.txt", txt)
    hio.to_file("tmp.llm_transformed.txt", out_txt)
    cmd = "vimdiff tmp.llm_original.txt tmp.llm_transformed.txt"
    hio.create_executable_script("tmp.llm_diff.sh", cmd)
    #
    if compare:
        out_txt_tmp = []
        out_txt_tmp.append("#### Original ####")
        out_txt_tmp.append(hio.from_file(tmp_in_file_name))
        out_txt_tmp.append("#### Transformed ####")
        out_txt_tmp.append(out_txt)
        out_txt = "\n\n".join(out_txt_tmp)
    return out_txt
