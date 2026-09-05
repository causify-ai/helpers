Why does this happen when I run linters2/lint.py

1) src/umd_classes1/helpers_root/dev_scripts_helpers/documentation/test/test_md_to_speech.py

def _get_tmux_windows() -> List[Tuple[int, str]]:
    """
    Get index and pane working directory of each window in the tmux session.

    :return: list of (window_index, pane_current_path), ordered by
        window index
        ```
        [(0, "/Users/saggese/src/umd_classes1/helpers_root"),
         (1, "/Users/saggese/src/umd_classes1")]
        ```
    """
    hdbg.dassert_in("TMUX", os.environ, "Script must run inside a tmux session")



def _get_tmux_windows() -> List[Tuple[int, str]]:
    """
    Get index and pane working directory of each window in the tmux session.

    :return: list of (window_index, pane_current_path), ordered by window index
        ``` [(0, "/Users/saggese/src/umd_classes1/helpers_root"), (1,
        "/Users/saggese/src/umd_classes1")] ```
    """
    hdbg.dassert_in("TMUX", os.environ, "Script must run inside a tmux session")


2) src/umd_classes1/helpers_root/dev_scripts_helpers/documentation/test/test_compress_pdf.py

    def test2(self) -> None:
        """
        Test compressing a PDF in place through the CLI with the
        `ghostscript_dockerized` backend.
        """


    def test2(self) -> None:
        """Test compressing a PDF in place through the CLI with the
        `ghostscript_dockerized` backend.
        """

