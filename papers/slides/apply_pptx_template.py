#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "python-pptx",
#   "pyyaml",
# ]
# ///

"""
Apply PowerPoint template styling to an input presentation.

This script takes an input PowerPoint file and applies the design theme and
master slides from a template file by manipulating the underlying XML structure.

Example usage:
    # Apply template to a presentation.
    > apply_pptx_template.py --input presentation.pptx --template template.pptx --output output.pptx

Import as:

import apply_pptx_template as apppxte
"""

import argparse
import logging
import os
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

# #############################################################################


def _register_xml_namespaces() -> dict:
    """
    Register common PowerPoint XML namespaces.

    :return: dictionary of namespace prefixes to URIs
    """
    namespaces = {
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
    return namespaces


def _copy_directory_contents(src_dir: Path, dst_dir: Path) -> None:
    """
    Copy all files from source directory to destination directory.

    :param src_dir: source directory path
    :param dst_dir: destination directory path
    """
    if src_dir.exists():
        _LOG.debug("Copying directory: %s to %s", src_dir, dst_dir)
        dst_dir.mkdir(parents=True, exist_ok=True)
        for item in src_dir.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(src_dir)
                target_path = dst_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)


def _update_presentation_xml(
    input_dir: Path, template_dir: Path, namespaces: dict
) -> None:
    """
    Update presentation.xml to reference template's masters and layouts.

    :param input_dir: extracted input presentation directory
    :param template_dir: extracted template presentation directory
    :param namespaces: XML namespace dictionary
    """
    _LOG.debug("Updating presentation.xml references")
    input_pres_xml = input_dir / "ppt" / "presentation.xml"
    template_pres_xml = template_dir / "ppt" / "presentation.xml"
    hdbg.dassert_file_exists(str(input_pres_xml))
    hdbg.dassert_file_exists(str(template_pres_xml))
    # Parse both presentation files.
    input_tree = ET.parse(input_pres_xml)
    input_root = input_tree.getroot()
    template_tree = ET.parse(template_pres_xml)
    template_root = template_tree.getroot()
    # Find sldMasterIdLst in both files.
    input_master_list = input_root.find(".//p:sldMasterIdLst", namespaces)
    template_master_list = template_root.find(".//p:sldMasterIdLst", namespaces)
    if input_master_list is not None and template_master_list is not None:
        # Remove existing master list and replace with template's.
        input_root.remove(input_master_list)
        # Find position after sldSz element to insert master list.
        sld_sz = input_root.find(".//p:sldSz", namespaces)
        if sld_sz is not None:
            idx = list(input_root).index(sld_sz) + 1
            input_root.insert(idx, template_master_list)
        else:
            input_root.append(template_master_list)
    # Write back the modified presentation.xml.
    input_tree.write(input_pres_xml, encoding="UTF-8", xml_declaration=True)


def _copy_background_to_slides(
    input_dir: Path, template_dir: Path, namespaces: dict
) -> None:
    """
    Copy background element from template slide to all input slides.

    :param input_dir: extracted input presentation directory
    :param template_dir: extracted template presentation directory
    :param namespaces: XML namespace dictionary
    """
    _LOG.info("Copying background to slides")
    # Read template slide to get background element.
    template_slide = template_dir / "ppt" / "slides" / "slide1.xml"
    if not template_slide.exists():
        _LOG.debug("No template slide found, skipping background copy")
        return
    template_tree = ET.parse(template_slide)
    template_root = template_tree.getroot()
    # Find the background element in template.
    bg_element = None
    for cSld in template_root.findall(".//p:cSld", namespaces):
        for bg in cSld.findall("p:bg", namespaces):
            bg_element = bg
            break
    if bg_element is None:
        _LOG.debug("No background element found in template slide")
        return
    # Copy template media files to input.
    template_media_dir = template_dir / "ppt" / "media"
    input_media_dir = input_dir / "ppt" / "media"
    if template_media_dir.exists():
        _LOG.debug("Copying media files from template")
        _copy_directory_contents(template_media_dir, input_media_dir)
    # Process all slides in input presentation.
    slides_dir = input_dir / "ppt" / "slides"
    slide_files = sorted(slides_dir.glob("slide*.xml"))
    _LOG.debug("Processing %d slides", len(slide_files))
    for slide_file in slide_files:
        _LOG.debug("Adding background to %s", slide_file.name)
        # Parse slide.
        tree = ET.parse(slide_file)
        root = tree.getroot()
        # Find cSld element.
        cSld = root.find(".//p:cSld", namespaces)
        if cSld is None:
            _LOG.debug("No cSld found in %s, skipping", slide_file.name)
            continue
        # Check if background already exists.
        existing_bg = cSld.find("p:bg", namespaces)
        if existing_bg is not None:
            _LOG.debug(
                "Background already exists in %s, removing", slide_file.name
            )
            cSld.remove(existing_bg)
        # Insert background as first child of cSld.
        cSld.insert(0, bg_element)
        # Write back.
        tree.write(slide_file, encoding="UTF-8", xml_declaration=True)
        # Add image relationship if not exists.
        rels_file = slides_dir / "_rels" / f"{slide_file.stem}.xml.rels"
        if rels_file.exists():
            rels_tree = ET.parse(rels_file)
            rels_root = rels_tree.getroot()
            # Check if rId99 exists.
            has_image_rel = False
            for rel in rels_root.findall("Relationship"):
                if rel.get("Id") == "rId99":
                    has_image_rel = True
                    break
            if not has_image_rel:
                # Add image relationship.
                _LOG.debug("Adding image relationship to %s", rels_file.name)
                ET.SubElement(
                    rels_root,
                    "Relationship",
                    {
                        "Id": "rId99",
                        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                        "Target": "../media/image1.png",
                    },
                )
                rels_tree.write(
                    rels_file, encoding="UTF-8", xml_declaration=True
                )


def _merge_presentation_rels(
    input_rels: Path, template_rels: Path, namespaces: dict
) -> None:
    """
    Merge presentation relationships from template into input.

    This preserves slide relationships from input while adding master/layout
    relationships from template.

    :param input_rels: input presentation relationships file path
    :param template_rels: template presentation relationships file path
    :param namespaces: XML namespace dictionary
    """
    if not template_rels.exists():
        return
    hdbg.dassert_file_exists(str(input_rels))
    _LOG.debug("Merging presentation relationships")
    # Parse both rels files.
    input_tree = ET.parse(input_rels)
    input_root = input_tree.getroot()
    template_tree = ET.parse(template_rels)
    template_root = template_tree.getroot()
    # Get existing relationship IDs in input.
    input_rel_ids = set()
    for rel in input_root.findall("Relationship"):
        input_rel_ids.add(rel.get("Id"))
    # Get all slide master and theme relationships from template.
    for rel in template_root.findall("Relationship"):
        rel_type = rel.get("Type", "")
        rel_id = rel.get("Id")
        # Only copy master, layout, and theme relationships.
        if "slideMaster" in rel_type or "theme" in rel_type:
            # Remove existing relationship with same ID if exists.
            for existing_rel in input_root.findall("Relationship"):
                if existing_rel.get("Id") == rel_id:
                    input_root.remove(existing_rel)
            # Add the template relationship.
            input_root.append(rel)
    # Write back the merged relationships.
    input_tree.write(input_rels, encoding="UTF-8", xml_declaration=True)


def _apply_template_xml(
    input_path: str, template_path: str, output_path: str
) -> None:
    """
    Apply template by manipulating PowerPoint XML structure.

    :param input_path: path to input PowerPoint file
    :param template_path: path to template PowerPoint file
    :param output_path: path to save the styled output
    """
    _LOG.info("Loading input presentation from: %s", input_path)
    hdbg.dassert_file_exists(input_path)
    _LOG.info("Loading template from: %s", template_path)
    hdbg.dassert_file_exists(template_path)
    # Register XML namespaces.
    namespaces = _register_xml_namespaces()
    # Create temporary directories for extraction.
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        template_dir = temp_path / "template"
        input_dir.mkdir(parents=True)
        template_dir.mkdir(parents=True)
        # Extract both presentations.
        _LOG.info("Extracting presentations")
        with zipfile.ZipFile(input_path, "r") as zip_ref:
            zip_ref.extractall(input_dir)
        with zipfile.ZipFile(template_path, "r") as zip_ref:
            zip_ref.extractall(template_dir)
        # Copy theme files from template to input.
        _LOG.info("Copying theme files from template")
        template_theme_dir = template_dir / "ppt" / "theme"
        input_theme_dir = input_dir / "ppt" / "theme"
        if input_theme_dir.exists():
            shutil.rmtree(input_theme_dir)
        _copy_directory_contents(template_theme_dir, input_theme_dir)
        # Copy slide master files from template to input.
        _LOG.info("Copying slide master files from template")
        template_masters_dir = template_dir / "ppt" / "slideMasters"
        input_masters_dir = input_dir / "ppt" / "slideMasters"
        if input_masters_dir.exists():
            shutil.rmtree(input_masters_dir)
        _copy_directory_contents(template_masters_dir, input_masters_dir)
        # Copy slide layout files from template to input.
        _LOG.info("Copying slide layout files from template")
        template_layouts_dir = template_dir / "ppt" / "slideLayouts"
        input_layouts_dir = input_dir / "ppt" / "slideLayouts"
        if input_layouts_dir.exists():
            shutil.rmtree(input_layouts_dir)
        _copy_directory_contents(template_layouts_dir, input_layouts_dir)
        # Copy background from template to all slides.
        _copy_background_to_slides(input_dir, template_dir, namespaces)
        # Update presentation.xml to reference new masters.
        _update_presentation_xml(input_dir, template_dir, namespaces)
        # Merge presentation.xml.rels from template.
        _LOG.info("Merging presentation relationships")
        template_pres_rels = (
            template_dir / "ppt" / "_rels" / "presentation.xml.rels"
        )
        input_pres_rels = input_dir / "ppt" / "_rels" / "presentation.xml.rels"
        _merge_presentation_rels(input_pres_rels, template_pres_rels, namespaces)
        # Ensure output directory exists.
        output_dir = os.path.dirname(output_path)
        if output_dir:
            hio.create_dir(output_dir, incremental=True)
        # Repack as PPTX.
        _LOG.info("Creating output presentation: %s", output_path)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(input_dir)
                    zipf.write(file_path, arcname)
    _LOG.info("Template applied successfully")


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        action="store",
        required=True,
        help="Input PowerPoint file path",
    )
    parser.add_argument(
        "--template",
        action="store",
        required=True,
        help="Template PowerPoint file path",
    )
    parser.add_argument(
        "--output",
        action="store",
        required=True,
        help="Output PowerPoint file path",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _apply_template_xml(
        input_path=args.input,
        template_path=args.template,
        output_path=args.output,
    )


if __name__ == "__main__":
    _main(_parse())
