import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hsystem as hsystem

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
        f"pandoc --read=markdown --write=latex -o {out_file_name}"
        f" {in_file_name}"
    )
    hsystem.system(cmd)
    # Read tmp file.
    res = hio.from_file(out_file_name)
    return res
