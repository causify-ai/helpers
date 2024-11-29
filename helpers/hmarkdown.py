import logging
import re

import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

def extract_section_from_markdown(content: str, header_name: str) -> str:
    """
    Extract text between the specified header and the next header of the same
    level in a Markdown text.

    :param content: The Markdown content as a string.
    :param header_name: The name of the header to extract the section from.
    :return: The text between the specified header and the next header of the
        same level.
    """
    # Find all headers and their positions.
    # E.g., A list of tuples where each tuple contains a header string
    # and its starting position in the content.
    # headers = [
    #     ("# Header1", 0),
    #     ("## Header2", 15),
    #     ("# Header3", 30)
    # ]
    headers = [(match.group(0), match.start()) for match in
               re.finditer(r'^(#+)\s+(.*)$', content, re.MULTILINE)]
    _LOG.debug("headers=\n%s", headers)
    # Find the specified header and its level.
    for i, (header, position) in enumerate(headers):
        #header_level, header_text = header.split(' ', 1)
        # Count the number of `#` symbols.
        header_level = len(header.split()[0])
        # Extract the header text.
        header_text = header.split(' ', 1)[1]
        _LOG.debug(hprint.to_str("header_level header_text"))
        if header_text.strip() == header_name:
            _LOG.debug("Found header '%s' at position %d", header_name, position)
            # Find the next header of the same level.
            for next_header in headers[i + 1:]:
                next_level, next_text = header.split(' ', 1)
                _LOG.debug(hprint.to_str("next_level next_text"))
                next_level = len(next_level)
                _LOG.debug("Found next header '%s' at position %d",
                    next_text, next_level)
                if next_level > header_level:
                    # Return text between the headers.
                    return content[position:next_header[1]].strip()
            # If no next header of the same level, return until the end of file.
            return content[position:].strip()
    raise ValueError(f"Header '{header_name}' not found")