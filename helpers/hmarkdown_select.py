r"""
Utilities for selecting header ranges in markdown files.

Provides functions to find and validate markdown headers by full format or
partial title match, and to determine section boundaries for text extraction.

Import as:

import helpers.hmarkdown_select as hmarsel
"""

from typing import List, Optional, Tuple

import helpers.hdbg as hdbg
import helpers.hmarkdown_headers as hmarhead
import helpers.hmarkdown_slides as hmarslides


def parse_header_string(header_str: str) -> Tuple[int, str]:
	"""
	Parse a header string and extract level and title.

	:param header_str: header string like "## Section Title"
	:return: tuple of (level, title)
	"""
	hdbg.dassert_isinstance(header_str, str, "header_str must be a string")
	hdbg.dassert_ne(header_str, "", "Header string cannot be empty")
	is_header_, level, title = hmarhead.is_header(header_str)
	hdbg.dassert(
		is_header_,
		"Invalid header format '%s'; expected format like '# Title' or '## Subtitle'",
		header_str,
	)
	return level, title


def find_header_by_title(
	header_list: hmarhead.HeaderList, target_title: str
) -> Optional[hmarhead.HeaderInfo]:
	"""
	Find a header in the list matching the target title.

	:param header_list: list of HeaderInfo objects
	:param target_title: title to match (exact match required)
	:return: HeaderInfo if found, None otherwise
	"""
	for header_info in header_list:
		if header_info.description == target_title:
			return header_info
	return None


def find_header_by_partial_title(
	header_list: hmarhead.HeaderList, partial_title: str
) -> Optional[hmarhead.HeaderInfo]:
	"""
	Find a header by partial title match.

	The partial_title matches if any header's title starts with it (case-sensitive).
	Raises an error if multiple headers match.

	:param header_list: list of HeaderInfo objects
	:param partial_title: partial title to match (must be unique)
	:return: HeaderInfo if found, None otherwise
	"""
	matches = []
	for header_info in header_list:
		if header_info.description.startswith(partial_title):
			matches.append(header_info)
	if len(matches) == 0:
		return None
	hdbg.dassert_eq(
		len(matches),
		1,
		"Partial title '%s' matches multiple headers: %s. Please provide a more specific match.",
		partial_title,
		[h.description for h in matches],
	)
	return matches[0]


def find_header_from_input(
	header_list: hmarhead.HeaderList,
	header_input: str,
) -> Tuple[hmarhead.HeaderInfo, int]:
	"""
	Find a header from user input that can be either a full header string or partial title.

	:param header_list: list of HeaderInfo objects
	:param header_input: either "## Title" (full header) or "Title" (partial match)
	:return: tuple of (HeaderInfo, level) where level is from the input if it was a full header
	:raises: ValueError if input is ambiguous or header not found
	"""
	if header_input.lstrip().startswith("#"):
		# Full header format like "## Title"
		level, title = parse_header_string(header_input)
		header_info = find_header_by_title(header_list, title)
		hdbg.dassert_is_not(
			header_info, None, "Header not found: '%s'", header_input
		)
		hdbg.dassert_eq(
			header_info.level,
			level,
			"Header level mismatch for '%s': expected level %s, got %s",
			title,
			level,
			header_info.level,
		)
		return header_info, level
	else:
		# Partial title match
		header_info = find_header_by_partial_title(header_list, header_input)
		hdbg.dassert_is_not(
			header_info, None, "No header matches: '%s'", header_input
		)
		return header_info, header_info.level


def find_end_line(
	header_list: hmarhead.HeaderList,
	start_header_info: hmarhead.HeaderInfo,
	end_header_input: Optional[str],
) -> Optional[int]:
	"""
	Find the line number where the text extraction should end.

	If end_header_input is provided, find that header. Otherwise, find the
	next header at the same or higher level (fewer or equal # symbols).

	:param header_list: list of HeaderInfo objects
	:param start_header_info: the start header
	:param end_header_input: header input (full format or partial match) or None to auto-detect
	:return: line number where extraction ends (exclusive)
	"""
	hdbg.dassert_isinstance(header_list, list, "header_list must be a list")
	hdbg.dassert_isinstance(
		start_header_info,
		hmarhead.HeaderInfo,
		"start_header_info must be a HeaderInfo object",
	)
	# Find the index of the start header in the list for iterating from that point.
	start_idx = None
	for i, header_info in enumerate(header_list):
		if header_info.line_number == start_header_info.line_number:
			start_idx = i
			break
	hdbg.dassert_is_not(start_idx, None, "Start header not found in header list")
	# If an explicit end header is provided, use it directly.
	if end_header_input is not None:
		end_header_info, _ = find_header_from_input(
			header_list, end_header_input
		)
		return end_header_info.line_number - 1
	# Search for the next header at the same or higher level (fewer # symbols).
	for i in range(start_idx + 1, len(header_list)):
		candidate_header = header_list[i]
		if candidate_header.level <= start_header_info.level:
			return candidate_header.line_number - 1
	return None


def extract_text_from_markdown_lines(
	lines: List[str],
	start_header_str: str,
	end_header_str: Optional[str],
	is_slide_format: bool = False,
) -> List[str]:
	"""
	Extract text from markdown lines between two headers.

	For .txt slide files, headers can be specified as:
	- Slides: "* Slide Title" (shorthand for `##### Slide Title`)
	- Full header format: "##### Section 1" (includes the # symbols)
	- Partial match: "Section 1" (just the title, matches if unique)

	For .md files, headers can be specified as:
	- Full format: "## Section 1" (includes the # symbols)
	- Partial match: "Section 1" (just the title, matches if unique)

	:param lines: list of lines in the input file
	:param start_header_str: starting header (e.g., "## Section 1" or "Section 1")
	:param end_header_str: ending header (optional, same formats accepted)
	:param is_slide_format: whether the input is in slide format (*.txt)
	:return: extracted lines with trailing blank lines removed
	"""
	hdbg.dassert_isinstance(lines, list, "lines must be a list of strings")
	# Convert slide notation ('* Title') to header notation if needed.
	start_header_str_converted = start_header_str
	end_header_str_converted = end_header_str
	lines_converted = lines
	if is_slide_format:
		start_header_str_converted = hmarslides.convert_slide_to_markdown(
			[start_header_str]
		)[0]
		if end_header_str is not None:
			end_header_str_converted = hmarslides.convert_slide_to_markdown(
				[end_header_str]
			)[0]
		lines_converted = hmarslides.convert_slide_to_markdown(lines)
	sanity_check = False
	header_list = hmarhead.extract_headers_from_markdown(
		lines_converted, max_level=10, sanity_check=sanity_check
	)
	start_header_info, _ = find_header_from_input(
		header_list, start_header_str_converted
	)
	end_line = find_end_line(header_list, start_header_info, end_header_str_converted)
	start_idx = start_header_info.line_number - 1
	if end_line is None:
		end_idx = len(lines_converted)
	else:
		end_idx = end_line
	extracted_lines = lines_converted[start_idx:end_idx]
	while extracted_lines and extracted_lines[-1].strip() == "":
		extracted_lines.pop()
	return extracted_lines
