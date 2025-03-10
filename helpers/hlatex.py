import re

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hio as hio
import helpers.hprint as hprint

# TODO(gp): Consider using `pypandoc` instead of calling `pandoc` directly.
# https://boisgera.github.io/pandoc


# TODO(gp): Add a switch to keep the tmp files or delete them.
def convert_pandoc_md_to_latex(txt: str) -> str:
    """
    Run pandoc to convert a markdown file to a latex file.
    """
    hdbg.dassert_isinstance(txt, str)
    # Save to tmp file.
    in_file_name = "./tmp.run_pandoc_in.md"
    hio.to_file(in_file_name, txt)
    # Run Pandoc.
    out_file_name = "./tmp.run_pandoc_out.tex"
    cmd = (
        f"pandoc {in_file_name}"
        f" -o {out_file_name}"
        " --read=markdown --write=latex"
    )
    container_type = "pandoc_only"
    hdocker.run_dockerized_pandoc(cmd, container_type)
    # Read tmp file.
    res = hio.from_file(out_file_name)
    return res


def markdown_list_to_latex(markdown: str) -> str:
    """
    Convert a Markdown list to LaTeX format.

    :param markdown: The Markdown text to convert
    :return: The converted LaTeX text
    """
    hdbg.dassert_isinstance(markdown, str)
    markdown = hprint.dedent(markdown)
    # Remove the first line if it's a title.
    markdown = markdown.split("\n")
    m = re.match(r"^(\*+ )(.*)", markdown[0])
    if m:
        title = m.group(2)
        markdown = markdown[1:]
    else:
        title = ""
    markdown = "\n".join(markdown)
    # Convert.
    txt = convert_pandoc_md_to_latex(markdown)
    # Remove `\tightlist` and empty lines.
    lines = txt.splitlines()
    lines = [line for line in lines if "\\tightlist" not in line]
    lines = [line for line in lines if line.strip() != ""]
    txt = "\n".join(lines)
    # Add the title frame.
    if title:
        txt = "\\begin{frame}{%s}" % title + "\n" + txt + "\n" + "\\end{frame}"
    return txt


def remove_latex_formatting(latex_string: str) -> str:
    r"""
    Remove LaTeX formatting such as \textcolor{color}{content} and retains only
    the content.
    """
    cleaned_string = re.sub(
        r"\\textcolor\{[^}]*\}\{([^}]*)\}", r"\1", latex_string
    )
    return cleaned_string
