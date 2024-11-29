import logging

import helpers.hprint as hprint
from typing import Optional

_LOG = logging.getLogger(__name__)


def extract_section_from_markdown(content: str, header_name: str) -> str:
    """
    Extract a section of text from a markdown document based on the header name.

    The function identifies a section by locating the specified header and
    captures all lines until encountering another header of the same or
    higher level. Headers are identified by the '#' prefix, and their level
    is determined by the number of '#' characters.

    :param content: The markdown content as a single string.
    :param header_name: The exact header name to extract (excluding '#' symbols).
    :return: The extracted section as a string, including the header line itself
             and all lines until the next header of the same or higher level.
    """
    lines = content.splitlines()
    _LOG.debug(hprint.to_str("lines"))
    extracted_lines = []
    # Level of the current header being processed.
    current_level: Optional[int] = None
    # Flag to indicate if we're inside the desired section.
    inside_section: bool = False
    found = False
    # Process each line in the markdown content.
    for line in lines:
        _LOG.debug(hprint.to_str("line"))
        # Check if the line is a markdown header.
        if line.strip().startswith("#"):
            # Determine the level of the header by counting leading '#'
            # characters.
            header_level = len(line) - len(line.lstrip('#'))
            # Extract the actual header text by stripping '#' and surrounding
            # whitespace.
            header_text = line.strip('#').strip()
            _LOG.debug(hprint.to_str("header_level, header_text"))
            # Handle the end of the desired section when encountering another
            # header.
            if inside_section:
                if header_level <= current_level:
                    break
            # Check if the current line is the desired header.
            if header_text == header_name:
                found = True
                # Set the level of the matched header.
                current_level = header_level
                # Mark that we are now inside the desired section.
                inside_section = True
        # Add the line to the output if inside the desired section.
        if inside_section:
            extracted_lines.append(line)
            _LOG.debug(hprint.to_str("extracted_lines"))
    if not found:
        raise ValueError(f"Header '{header_name}' not found")
    return "\n".join(extracted_lines)
