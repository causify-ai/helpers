prompt = """
You are an expert Python coder, which is very detail oriented.

Report if in the following Python code the parameters of any function declaration are in
the proper order, where
- input parameters come first
- input-output parameters (i.e., parameters that input and modified) are second
- output parameters come last but before optional parameters

Do not explain why, just print the line number of where a problem is found and
what the problem is
"""

r"""
def _extract_headers_from_markdown(
    in_file_name: str, out_file_name: str, mode: str, max_level: int, 
) -> None:
    input_content = hparser.read_file(in_file_name)
    input_content = "\n".join(input_content)
    # We don't want to sanity check since we want to show the headers, even
    # if malformed.
    sanity_check = False
    header_list = hmarkdo.extract_headers_from_markdown(
        input_content, max_level=max_level, sanity_check=sanity_check
    )
    if mode == "cfile":
        output_content = hmarkdo.header_list_to_vim_cfile(
            in_file_name, header_list
        )
    else:
        output_content = hmarkdo.header_list_to_markdown(header_list, mode)
    hparser.write_file(output_content, out_file_name)
    #
    hmarkdo.check_header_list(header_list)
"""

# #############################################################################

prompt = """
You are an expert Python coder, which is very detail oriented.

Make sure that variables are declared in the same order as the parameters of
the function they are passed to.

Do not explain why, just print the line number of where a problem is found and
what the problem is
"""

"""
content = hprint.dedent(content)
input_file = self.get_scratch_space() + "/input.md"
output_file = self.get_scratch_space() + "/output.md"
hio.to_file(input_file, content)
mode = "headers"
max_level = "3"
# Call tested function.
dshdehfma._extract_headers_from_markdown(input_file, mode, max_level, output_file)"
""""

# #############################################################################

prompt = """
You are an expert Python coder, which is very detail oriented.

Make sure that parameters with a default value in a functionm declaration come
after the * to indicate that the name is mandatory.

Do not explain why, just print the line number of where a problem is found and
what the problem is
"""

"""
def diff_files(
    file_name1: str,
    file_name2: str,
    tag: Optional[str] = None,
    abort_on_exit: bool = True,
    dst_dir: str = ".",
    error_msg: str = "",
) -> None:"
"""