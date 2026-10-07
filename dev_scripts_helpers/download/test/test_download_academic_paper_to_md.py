#!/usr/bin/env python

import logging
import os
import pprint
from typing import Any, Dict, List, Tuple
from unittest import mock

import pytest

pytest.importorskip("feedparser")
pytest.importorskip("fitz")
pytest.importorskip("requests")

import fitz

import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest
import helpers.hunit_test_utils as hunteuti
import dev_scripts_helpers.download.download_academic_paper_to_md as dsdapt

_LOG = logging.getLogger(__name__)


def _create_pdf(file_path: str, *, title: str = "", author: str = "") -> None:
    """
    Create a one-page PDF with the given metadata.

    The creation date is always 2025, so that the year of the paper is
    known.

    :param file_path: path of the PDF to create
    :param title: title stored in the PDF metadata
    :param author: author(s) stored in the PDF metadata
    """
    doc = fitz.open()
    doc.new_page()  # type: ignore
    doc.set_metadata(  # type: ignore
        {
            "title": title,
            "author": author,
            "creationDate": "D:20250601000000Z",
        }
    )
    doc.save(file_path)
    doc.close()


# #############################################################################
# Test__is_local_file
# #############################################################################


class Test__is_local_file(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._is_local_file()`.
    """

    def helper(self, input_arg: str, expected: bool) -> None:
        """
        Test helper for `_is_local_file()`.

        :param input_arg: URL, DOI, or path to classify
        :param expected: expected result
        """
        # Run test.
        actual = dsdapt._is_local_file(input_arg)
        # Check outputs.
        self.assertEqual(actual, expected)

    def test1(self) -> None:
        """
        Test an existing file is a local file.
        """
        # Prepare inputs.
        input_arg = os.path.join(self.get_scratch_space(), "paper.pdf")
        _create_pdf(input_arg)
        # Prepare outputs.
        expected = True
        # Run test.
        self.helper(input_arg, expected)

    def test2(self) -> None:
        """
        Test a path to a missing file is not a local file.
        """
        # Prepare inputs.
        input_arg = os.path.join(self.get_scratch_space(), "missing.pdf")
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(input_arg, expected)

    def test3(self) -> None:
        """
        Test a URL is not a local file.
        """
        # Prepare inputs.
        input_arg = "https://arxiv.org/abs/1706.03762"
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(input_arg, expected)

    def test4(self) -> None:
        """
        Test a bare DOI is not a local file.
        """
        # Prepare inputs.
        input_arg = "10.2139/ssrn.5277078"
        # Prepare outputs.
        expected = False
        # Run test.
        self.helper(input_arg, expected)


# #############################################################################
# Test__extract_pdf_metadata_pymupdf
# #############################################################################


class Test__extract_pdf_metadata_pymupdf(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._extract_pdf_metadata_pymupdf()`.
    """

    def helper(self, title: str, author: str, expected: str) -> None:
        """
        Test helper for `_extract_pdf_metadata_pymupdf()`.

        :param title: title stored in the PDF metadata
        :param author: author(s) stored in the PDF metadata
        :param expected: expected metadata, as a string
        """
        # Prepare inputs.
        pdf_path = os.path.join(self.get_scratch_space(), "paper.pdf")
        _create_pdf(pdf_path, title=title, author=author)
        # Run test.
        actual = dsdapt._extract_pdf_metadata_pymupdf(pdf_path)
        # Check outputs.
        self.assert_equal(pprint.pformat(actual), expected, dedent=True)

    def test1(self) -> None:
        """
        Test authors separated by the word "and" are not split on its letters.
        """
        # Prepare inputs.
        title = "A Protocol for Causal Factor Investing"
        author = "Marcos Lopez de Prado and Vincent Zoonekynd"
        # Prepare outputs.
        expected = """
        {'authors': ['Marcos Lopez de Prado', 'Vincent Zoonekynd'],
         'title': 'A Protocol for Causal Factor Investing',
         'year': '2025'}
        """
        # Run test.
        self.helper(title, author, expected)

    def test2(self) -> None:
        """
        Test authors separated by commas and semicolons.
        """
        # Prepare inputs.
        title = "Some Title"
        author = "Ann Lee, Bob Dana; Carl Nand"
        # Prepare outputs.
        expected = """
        {'authors': ['Ann Lee', 'Bob Dana', 'Carl Nand'],
         'title': 'Some Title',
         'year': '2025'}
        """
        # Run test.
        self.helper(title, author, expected)

    def test3(self) -> None:
        """
        Test a PDF without title and authors.
        """
        # Prepare inputs.
        title = ""
        author = ""
        # Prepare outputs.
        expected = """
        {'authors': [], 'title': None, 'year': '2025'}
        """
        # Run test.
        self.helper(title, author, expected)


# #############################################################################
# Test__resolve_doi_metadata
# #############################################################################


class Test__resolve_doi_metadata(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._resolve_doi_metadata()`.
    """

    def helper(
        self, email: str, unpaywall_resp: Dict[str, Any], expected: str
    ) -> None:
        """
        Test helper for `_resolve_doi_metadata()`.

        The CrossRef and Unpaywall APIs are mocked, so no network is used.

        :param email: contact email passed to Unpaywall
        :param unpaywall_resp: response returned by the mocked Unpaywall API
        :param expected: expected metadata and API calls, as a string
        """
        # Prepare inputs.
        doi = "10.2139/ssrn.5277078"
        crossref_resp = {
            "message": {
                "title": ["A Protocol for Causal Factor Investing"],
                "author": [{"given": "Marcos", "family": "Prado"}],
                "issued": {"date-parts": [[2025]]},
            }
        }

        def _get(url: str, **_: Any) -> mock.Mock:
            resp = mock.Mock()
            if "crossref" in url:
                resp.json.return_value = crossref_resp
            else:
                resp.json.return_value = unpaywall_resp
            return resp

        # Run test.
        with mock.patch.object(dsdapt.requests, "get", side_effect=_get) as get:
            metadata = dsdapt._resolve_doi_metadata(doi, email=email)
        # Check outputs.
        calls: List[Dict[str, Any]] = [
            {"url": call.args[0], "params": call.kwargs.get("params")}
            for call in get.call_args_list
        ]
        actual = pprint.pformat({"metadata": metadata, "calls": calls})
        self.assert_equal(actual, expected, dedent=True)

    def test1(self) -> None:
        """
        Test that Unpaywall is queried with the passed email.
        """
        # Prepare inputs.
        email = "me@example.org"
        unpaywall_resp = {
            "is_oa": True,
            "best_oa_location": {
                "url": "https://example.org/abstract",
                "url_for_pdf": "https://example.org/paper.pdf",
            },
        }
        # Prepare outputs.
        expected = """
        {'calls': [{'params': None,
                    'url': 'https://api.crossref.org/works/10.2139/ssrn.5277078'},
                   {'params': {'email': 'me@example.org'},
                    'url': 'https://api.unpaywall.org/v2/10.2139/ssrn.5277078'}],
         'metadata': {'authors': ['Marcos Prado'],
                      'pdf_url': 'https://example.org/paper.pdf',
                      'title': 'A Protocol for Causal Factor Investing',
                      'year': '2025'}}
        """
        # Run test.
        self.helper(email, unpaywall_resp, expected)

    def test2(self) -> None:
        """
        Test that Unpaywall is not queried when there is no email.
        """
        # Prepare inputs.
        email = ""
        unpaywall_resp: Dict[str, Any] = {}
        # Prepare outputs.
        expected = """
        {'calls': [{'params': None,
                    'url': 'https://api.crossref.org/works/10.2139/ssrn.5277078'}],
         'metadata': {'authors': ['Marcos Prado'],
                      'pdf_url': None,
                      'title': 'A Protocol for Causal Factor Investing',
                      'year': '2025'}}
        """
        # Run test.
        self.helper(email, unpaywall_resp, expected)

    def test3(self) -> None:
        """
        Test that a landing page without a direct PDF link is not used as PDF.

        This is the SSRN case: Unpaywall lists the abstract page as the open
        access location, and downloading it fails with a `403`.
        """
        # Prepare inputs.
        email = "me@example.org"
        unpaywall_resp = {
            "is_oa": True,
            "best_oa_location": {
                "url": "https://www.ssrn.com/abstract=5277078",
                "url_for_pdf": None,
            },
            "oa_locations": [
                {
                    "url": "https://www.ssrn.com/abstract=5277078",
                    "url_for_pdf": None,
                }
            ],
        }
        # Prepare outputs.
        expected = """
        {'calls': [{'params': None,
                    'url': 'https://api.crossref.org/works/10.2139/ssrn.5277078'},
                   {'params': {'email': 'me@example.org'},
                    'url': 'https://api.unpaywall.org/v2/10.2139/ssrn.5277078'}],
         'metadata': {'authors': ['Marcos Prado'],
                      'pdf_url': None,
                      'title': 'A Protocol for Causal Factor Investing',
                      'year': '2025'}}
        """
        # Run test.
        self.helper(email, unpaywall_resp, expected)

    def test4(self) -> None:
        """
        Test that a direct PDF link in another location is used.
        """
        # Prepare inputs.
        email = "me@example.org"
        unpaywall_resp = {
            "is_oa": True,
            "best_oa_location": {
                "url": "https://example.org/abstract",
                "url_for_pdf": None,
            },
            "oa_locations": [
                {"url": "https://example.org/abstract", "url_for_pdf": None},
                {
                    "url": "https://repo.example.org/1",
                    "url_for_pdf": "https://repo.example.org/1.pdf",
                },
            ],
        }
        # Prepare outputs.
        expected = """
        {'calls': [{'params': None,
                    'url': 'https://api.crossref.org/works/10.2139/ssrn.5277078'},
                   {'params': {'email': 'me@example.org'},
                    'url': 'https://api.unpaywall.org/v2/10.2139/ssrn.5277078'}],
         'metadata': {'authors': ['Marcos Prado'],
                      'pdf_url': 'https://repo.example.org/1.pdf',
                      'title': 'A Protocol for Causal Factor Investing',
                      'year': '2025'}}
        """
        # Run test.
        self.helper(email, unpaywall_resp, expected)


# #############################################################################
# Test__resolve_metadata_and_content
# #############################################################################


class Test__resolve_metadata_and_content(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._resolve_metadata_and_content()` for
    an SSRN paper.
    """

    def test1(self) -> None:
        """
        Test an SSRN URL is named from CrossRef, with no PDF URL to download.

        The CrossRef API is mocked, so no network is used.
        """
        # Prepare inputs.
        url = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        crossref_resp = {
            "message": {
                "title": ["A Protocol for Causal Factor Investing"],
                "author": [{"given": "Marcos", "family": "Prado"}],
                "issued": {"date-parts": [[2025]]},
            }
        }
        response = mock.Mock()
        response.json.return_value = crossref_resp
        # Prepare outputs.
        expected = """
        {'calls': ['https://api.crossref.org/works/10.2139/ssrn.5277078'],
         'metadata': {'authors': ['Marcos Prado'],
                      'title': 'A Protocol for Causal Factor Investing',
                      'year': '2025'},
         'pdf_content': None,
         'pdf_url': None}
        """
        # Run test.
        with mock.patch.object(
            dsdapt.requests, "get", return_value=response
        ) as get:
            metadata, pdf_content, pdf_url = (
                dsdapt._resolve_metadata_and_content(url)
            )
        # Check outputs.
        actual = {
            "calls": [call.args[0] for call in get.call_args_list],
            "pdf_content": pdf_content,
            "pdf_url": pdf_url,
            "metadata": metadata,
        }
        actual = pprint.pformat(actual)
        self.assert_equal(actual, expected, dedent=True)


# #############################################################################
# Test__get_output_base_path
# #############################################################################


class Test__get_output_base_path(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._get_output_base_path()` for a local
    PDF.
    """

    def helper(self, title: str, author: str, expected_name: str) -> None:
        """
        Test helper for `_get_output_base_path()`.

        :param title: title stored in the PDF metadata
        :param author: author(s) stored in the PDF metadata
        :param expected_name: expected base name, without the output dir
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        pdf_path = os.path.join(scratch_dir, "ssrn_5277078.pdf")
        _create_pdf(pdf_path, title=title, author=author)
        output_dir = os.path.join(scratch_dir, "papers")
        # Prepare outputs.
        expected = os.path.join(output_dir, expected_name)
        # Run test.
        actual = dsdapt._get_output_base_path(pdf_path, output_dir)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test1(self) -> None:
        """
        Test the standardized name is derived from the PDF metadata.
        """
        # Prepare inputs.
        title = "A Protocol for Causal Factor Investing"
        author = "Marcos Lopez de Prado and Vincent Zoonekynd"
        # Prepare outputs.
        expected_name = "2025.Prado_et_al.A_Protocol_for_Causal_Factor_Investing"
        # Run test.
        self.helper(title, author, expected_name)

    def test2(self) -> None:
        """
        Test the name of the file is kept when the PDF has no title.
        """
        # Prepare inputs.
        title = ""
        author = ""
        # Prepare outputs.
        expected_name = "ssrn_5277078"
        # Run test.
        self.helper(title, author, expected_name)


# #############################################################################
# Test__download
# #############################################################################


class Test__download(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._download()` for a local PDF.
    """

    def helper(
        self,
        pdf_path: str,
        *,
        no_incremental: bool = False,
        dry_run: bool = False,
    ) -> str:
        """
        Test helper for `_download()`: create a local PDF and "download" it.

        :param pdf_path: path to save the PDF to
        :param no_incremental: if True, overwrite existing files
        :param dry_run: if True, do not execute the actions
        :return: path of the input PDF
        """
        # Prepare inputs.
        input_path = os.path.join(self.get_scratch_space(), "input.pdf")
        _create_pdf(input_path, title="Some Title")
        # Run test.
        dsdapt._download(
            input_path,
            pdf_path,
            no_incremental=no_incremental,
            dry_run=dry_run,
        )
        return input_path

    def read_bytes(self, file_path: str) -> bytes:
        """
        Read the content of a binary file.

        :param file_path: path of the file to read
        :return: content of the file
        """
        with open(file_path, "rb") as f:
            content = f.read()
        return content

    def test1(self) -> None:
        """
        Test a local PDF is copied to the output path, creating directories.
        """
        # Prepare inputs.
        pdf_path = os.path.join(self.get_scratch_space(), "papers", "out.pdf")
        # Run test.
        input_path = self.helper(pdf_path)
        # Check outputs.
        self.assertEqual(
            self.read_bytes(pdf_path), self.read_bytes(input_path)
        )

    def test2(self) -> None:
        """
        Test nothing is copied with `dry_run`.
        """
        # Prepare inputs.
        pdf_path = os.path.join(self.get_scratch_space(), "papers", "out.pdf")
        # Run test.
        self.helper(pdf_path, dry_run=True)
        # Check outputs.
        self.assertFalse(os.path.exists(pdf_path))

    def test3(self) -> None:
        """
        Test an existing output PDF is not overwritten by default.
        """
        # Prepare inputs.
        pdf_path = os.path.join(self.get_scratch_space(), "out.pdf")
        hio.to_file(pdf_path, "old content")
        # Run test.
        self.helper(pdf_path)
        # Check outputs.
        self.assert_equal(hio.from_file(pdf_path), "old content")

    def test4(self) -> None:
        """
        Test an existing output PDF is overwritten with `no_incremental`.
        """
        # Prepare inputs.
        pdf_path = os.path.join(self.get_scratch_space(), "out.pdf")
        hio.to_file(pdf_path, "old content")
        # Run test.
        input_path = self.helper(pdf_path, no_incremental=True)
        # Check outputs.
        self.assertEqual(
            self.read_bytes(pdf_path), self.read_bytes(input_path)
        )

    def test5(self) -> None:
        """
        Test a PDF already at the output path is left untouched.
        """
        # Prepare inputs.
        input_path = os.path.join(self.get_scratch_space(), "input.pdf")
        _create_pdf(input_path, title="Some Title")
        expected = self.read_bytes(input_path)
        # Run test: copying a file onto itself must not fail.
        dsdapt._download(input_path, input_path, no_incremental=True)
        # Check outputs.
        self.assertEqual(self.read_bytes(input_path), expected)


# #############################################################################
# Test__save_to_papers_dir
# #############################################################################


class Test__save_to_papers_dir(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._save_to_papers_dir()`.
    """

    def helper(
        self,
        *,
        with_summary: bool = True,
        existing_pdf: bool = False,
        no_incremental: bool = False,
        dry_run: bool = False,
    ) -> Tuple[str, str]:
        """
        Test helper for `_save_to_papers_dir()`.

        :param with_summary: if True, create the summary file
        :param existing_pdf: if True, create an old PDF in the papers dir
        :param no_incremental: if True, overwrite existing files
        :param dry_run: if True, do not execute the actions
        :return: sorted list of the files in the papers dir, as a string,
            and the content of the PDF in the papers dir (empty if
            missing)
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        base_path = os.path.join(scratch_dir, "papers", "2017.Vaswani.Paper")
        hio.create_dir(os.path.dirname(base_path), incremental=True)
        hio.to_file(f"{base_path}.pdf", "new pdf")
        if with_summary:
            hio.to_file(f"{base_path}.summary.md", "summary")
        papers_dir = os.path.join(scratch_dir, "saved_papers")
        dst_pdf_path = os.path.join(papers_dir, "2017.Vaswani.Paper.pdf")
        if existing_pdf:
            hio.create_dir(papers_dir, incremental=True)
            hio.to_file(dst_pdf_path, "old pdf")
        # Run test.
        dsdapt._save_to_papers_dir(
            base_path,
            papers_dir,
            no_incremental=no_incremental,
            dry_run=dry_run,
        )
        # Check outputs.
        files = []
        if os.path.exists(papers_dir):
            files = sorted(os.listdir(papers_dir))
        pdf_content = ""
        if os.path.exists(dst_pdf_path):
            pdf_content = hio.from_file(dst_pdf_path)
        return str(files), pdf_content

    def test1(self) -> None:
        """
        Test the PDF and the summary are copied, creating the dir.
        """
        # Run test.
        actual_files, actual_pdf = self.helper()
        # Check outputs.
        expected_files = (
            "['2017.Vaswani.Paper.pdf', '2017.Vaswani.Paper.summary.md']"
        )
        self.assert_equal(actual_files, expected_files)
        self.assert_equal(actual_pdf, "new pdf")

    def test2(self) -> None:
        """
        Test only the PDF is copied when the summary is missing.
        """
        # Run test.
        actual_files, _ = self.helper(with_summary=False)
        # Check outputs.
        self.assert_equal(actual_files, "['2017.Vaswani.Paper.pdf']")

    def test3(self) -> None:
        """
        Test nothing is copied with `dry_run`.
        """
        # Run test.
        actual_files, _ = self.helper(dry_run=True)
        # Check outputs.
        self.assert_equal(actual_files, "[]")

    def test4(self) -> None:
        """
        Test an existing PDF in the papers dir is not overwritten by
        default.
        """
        # Run test.
        _, actual_pdf = self.helper(existing_pdf=True)
        # Check outputs.
        self.assert_equal(actual_pdf, "old pdf")

    def test5(self) -> None:
        """
        Test an existing PDF in the papers dir is overwritten with
        `no_incremental`.
        """
        # Run test.
        _, actual_pdf = self.helper(existing_pdf=True, no_incremental=True)
        # Check outputs.
        self.assert_equal(actual_pdf, "new pdf")


# #############################################################################
# Test__download_ssrn
# #############################################################################


class Test__download_ssrn(hunitest.TestCase):
    """
    Test `download_academic_paper_to_md._download()` for an SSRN paper.
    """

    def test1(self) -> None:
        """
        Test an SSRN DOI is downloaded by running `download_with_chrome.py`.
        """
        # Prepare inputs.
        # Resolve the script path (the result is cached) before capturing the
        # system calls, since `find_file_in_git_tree()` runs `find` through
        # `hsystem`, which would be mocked out.
        script_path = hgit.find_file_in_git_tree("download_with_chrome.py")
        url = "10.2139/ssrn.5277078"
        pdf_path = os.path.join(self.get_scratch_space(), "papers", "out.pdf")
        # The Chrome script is mocked out: this is the PDF it would produce.
        hio.create_dir(os.path.dirname(pdf_path), incremental=True)
        hio.to_file(pdf_path, "pdf content")
        # Prepare outputs.
        expected_cmd = (
            f"{script_path} --launch_chrome --mode file "
            f'--input "{url}" --output "{pdf_path}" --no_incremental -v INFO'
        )
        expected_str = hprint.dedent(
            f"""
            [
                {{
                'function': hsystem.system,
                'args': ('{expected_cmd}',),
                'kwargs': {{'print_command': True}},
                }},
            ]
            """
        )
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dsdapt._download(url, pdf_path, no_incremental=True)
        # Check outputs.
        hunteuti.assert_sys_calls(self, sys_calls, expected_str)

    def test2(self) -> None:
        """
        Test nothing is run with `dry_run`.
        """
        # Prepare inputs.
        url = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5277078"
        pdf_path = os.path.join(self.get_scratch_space(), "papers", "out.pdf")
        # Run test.
        with hunteuti.capture_sys_calls() as sys_calls:
            dsdapt._download(url, pdf_path, dry_run=True)
        # Check outputs.
        self.assertEqual(len(sys_calls), 0)
        self.assertFalse(os.path.exists(pdf_path))


# #############################################################################
# Test_download_academic_paper_to_md_py
# #############################################################################


class Test_download_academic_paper_to_md_py(hunitest.TestCase):
    """
    Test the `download_academic_paper_to_md.py` executable with a local PDF.
    """

    def run_main(self, argv: List[str]) -> None:
        """
        Run `_main()` with a mocked `sys.argv`.

        :param argv: command-line arguments, starting with the script name
        """
        parser = dsdapt._parse()
        with mock.patch("sys.argv", argv):
            dsdapt._main(parser)

    def helper(self, extra_argv: List[str], use_papers_dir: bool) -> str:
        """
        Run the `download` action on a local PDF and list the output dir.

        :param extra_argv: command-line arguments added after `--input`
        :param use_papers_dir: if True, save under `$PAPERS_DIR`
        :return: sorted list of the files in the output dir, as a string
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_path = os.path.join(scratch_dir, "in", "ssrn_5277078.pdf")
        hio.create_dir(os.path.dirname(input_path), incremental=True)
        _create_pdf(
            input_path,
            title="A Protocol for Causal Factor Investing",
            author="Marcos Lopez de Prado and Vincent Zoonekynd",
        )
        output_dir = os.path.join(scratch_dir, "out")
        argv = [
            "download_academic_paper_to_md.py",
            "--input",
            input_path,
            "--clear_actions",
            "--action",
            "download",
        ]
        argv += extra_argv
        env = {"PAPERS_DIR": output_dir} if use_papers_dir else {}
        # Run test.
        with mock.patch.dict(os.environ, env):
            self.run_main(argv)
        # Check outputs.
        actual = str(sorted(os.listdir(output_dir)))
        return actual

    def test1(self) -> None:
        """
        Test the PDF is saved under `$PAPERS_DIR` with the standardized name.
        """
        # Prepare outputs.
        expected = hprint.dedent(
            """
            ['2025.Prado_et_al.A_Protocol_for_Causal_Factor_Investing.pdf']
            """
        )
        # Run test.
        actual = self.helper([], True)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test2(self) -> None:
        """
        Test the PDF is saved with the base name passed with `--output`.
        """
        # Prepare inputs.
        output_base = os.path.join(self.get_scratch_space(), "out", "mypaper")
        extra_argv = ["--output", output_base]
        # Prepare outputs.
        expected = "['mypaper.pdf']"
        # Run test.
        actual = self.helper(extra_argv, False)
        # Check outputs.
        self.assert_equal(actual, expected)

    def test3(self) -> None:
        """
        Test `--action save_to_papers_dir` copies the PDF to `--papers_dir`.
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        input_path = os.path.join(scratch_dir, "in", "ssrn_5277078.pdf")
        hio.create_dir(os.path.dirname(input_path), incremental=True)
        _create_pdf(input_path, title="A Protocol for Causal Factor Investing")
        output_base = os.path.join(scratch_dir, "out", "mypaper")
        papers_dir = os.path.join(scratch_dir, "saved_papers")
        argv = [
            "download_academic_paper_to_md.py",
            "--input",
            input_path,
            "--output",
            output_base,
            "--clear_actions",
            "--action",
            "download",
            "--action",
            "save_to_papers_dir",
            "--papers_dir",
            papers_dir,
        ]
        # Run test.
        self.run_main(argv)
        # Check outputs.
        actual = str(sorted(os.listdir(papers_dir)))
        self.assert_equal(actual, "['mypaper.pdf']")
