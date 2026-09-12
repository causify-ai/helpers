#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "pandas",
#   "tqdm",
# ]
# ///

"""
Compress PNG/JPG figures in a directory that are larger than a target size.

Every file above `--target_kb` is re-encoded as JPEG via `magick`, decreasing
the JPEG quality until the output is at or below the target size (or
`--min_quality` is reached). Files already at or below the target are copied
through unchanged. `--input_dir` and `--output_dir` can be the same directory
only if `--force` is passed, since compressing in place is destructive: a PNG
input is renamed to `.jpg` in the process (removing the original `.png`), and
a JPG input is overwritten. When `--output_dir` differs from `--input_dir`,
`--input_dir` is left untouched and the (possibly compressed) figures are
written under `--output_dir` instead. At the end a report is printed with,
for each file, the format change (if any) and the size before/after
compression.

Requires the `magick` (ImageMagick) CLI, e.g. `brew install imagemagick` on
macOS.

# Usage Example

- Compress all figures larger than 500 KB into a separate dir:
> compress_figures.py --input_dir msml610/lectures_source/figures --output_dir msml610/lectures_source/figures_compressed --target_kb 500

- Compress figures in place (overwrites `--input_dir`):
> compress_figures.py --input_dir msml610/lectures_source/figures --output_dir msml610/lectures_source/figures --target_kb 500 --force

- Preview what would be compressed without touching any file:
> compress_figures.py --input_dir msml610/lectures_source/figures --output_dir /tmp/figures_out --target_kb 500 --dry_run

- Compress recursively, trying harder (lower quality floor):
> compress_figures.py --input_dir data605/lectures_source --output_dir data605/lectures_source_compressed --target_kb 300 --recursive --min_quality 5
"""

import argparse
import logging
import os
import shutil
from typing import Dict, List

import pandas as pd
import tqdm

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# #############################################################################
# Constants
# #############################################################################


# Extensions eligible for compression (lowercase, without the leading dot).
_IMAGE_EXTENSIONS = ("png", "jpg", "jpeg")
# Format all compressed output is converted to.
_TARGET_FORMAT = "jpg"


# #############################################################################
# Low-level helpers
# #############################################################################


def _dassert_magick_installed() -> None:
    """
    Check that the `magick` (ImageMagick) CLI is available on `PATH`.
    """
    magick_path = shutil.which("magick")
    if magick_path is None:
        raise RuntimeError(
            "`magick` (ImageMagick) is not installed. Install it, e.g., "
            "`brew install imagemagick` on macOS or "
            "`sudo apt install imagemagick` on Linux"
        )
    _LOG.debug("Using magick binary: '%s'", magick_path)


def _dassert_dirs_same_requires_force(
    input_dir: str, output_dir: str, *, force: bool
) -> None:
    """
    Raise if `input_dir` and `output_dir` are the same directory, unless
    `force` is set (explicit opt-in to compress figures in place).

    :param input_dir: source directory
    :param output_dir: destination directory
    :param force: if True, allow `input_dir` and `output_dir` to coincide
    """
    same_dir = os.path.realpath(input_dir) == os.path.realpath(output_dir)
    if same_dir and not force:
        raise RuntimeError(
            "--input_dir and --output_dir are the same directory "
            f"('{input_dir}'): pass --force to compress figures in place"
        )


def _copy_unchanged(
    input_file: str, unchanged_file: str, *, in_place: bool, dry_run: bool
) -> None:
    """
    Copy `input_file` to `unchanged_file` under a separate `--output_dir`.

    A no-op when compressing in place, since `input_file` is already at
    `unchanged_file`.

    :param input_file: source file
    :param unchanged_file: destination path under `--output_dir`
    :param in_place: if True, `input_dir` and `output_dir` are the same
    :param dry_run: if True, report the copy without performing it
    """
    if in_place:
        return
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would copy '%s' -> '%s'", input_file, unchanged_file
        )
        return
    hio.create_dir(os.path.dirname(unchanged_file) or ".", incremental=True)
    shutil.copy2(input_file, unchanged_file)


def _find_image_files(input_dir: str, *, recursive: bool) -> List[str]:
    """
    Find all PNG/JPG files under `input_dir`.

    :param input_dir: directory to search
    :param recursive: if True, search subdirectories too
    :return: sorted list of absolute file paths
    """
    hdbg.dassert_dir_exists(input_dir)
    maxdepth = None if recursive else 1
    all_paths = hio.listdir(
        input_dir,
        "*",
        only_files=True,
        use_relative_paths=False,
        maxdepth=maxdepth,
    )
    image_paths = [
        path
        for path in all_paths
        if os.path.splitext(path)[1].lstrip(".").lower() in _IMAGE_EXTENSIONS
    ]
    image_paths = sorted(image_paths)
    _LOG.debug("Found %d image file(s) in '%s'", len(image_paths), input_dir)
    return image_paths


def _compress_image_to_target(
    input_file: str,
    output_file: str,
    target_bytes: int,
    *,
    quality_step: int = 5,
    min_quality: int = 10,
) -> int:
    """
    Re-encode `input_file` as JPEG into `output_file`, lowering quality until
    the output size is at or below `target_bytes`.

    :param input_file: path to the source PNG/JPG image
    :param output_file: path where the compressed JPEG is written
    :param target_bytes: target maximum output size, in bytes
    :param quality_step: amount to decrease JPEG quality by at each attempt
    :param min_quality: lowest JPEG quality to try before giving up
    :return: final output file size, in bytes
    """
    quality = 95
    output_size = 0
    while True:
        # Flatten transparency onto white (JPEG has no alpha channel) and
        # re-encode at `quality`. Force the `jpg:` coder explicitly instead of
        # relying on `output_file`'s extension, since the caller writes to a
        # `.tmp` file that `magick` would otherwise fail to recognize as JPEG.
        cmd = (
            f"magick {input_file} "
            "-background white -alpha remove -alpha off "
            f"-quality {quality} jpg:{output_file}"
        )
        hsystem.system(cmd, suppress_output="ON_DEBUG_LEVEL")
        output_size = os.path.getsize(output_file)
        if output_size <= target_bytes or quality <= min_quality:
            break
        quality -= quality_step
    _LOG.debug(
        "Compressed '%s' at quality=%d -> %d bytes", input_file, quality, output_size
    )
    return output_size


# #############################################################################
# Core business logic
# #############################################################################


def _compress_file(
    input_dir: str,
    output_dir: str,
    input_file: str,
    target_kb: int,
    *,
    in_place: bool,
    quality_step: int = 5,
    min_quality: int = 10,
    dry_run: bool = False,
) -> Dict[str, object]:
    """
    Compress a single image file if it is above `target_kb`.

    :param input_dir: root directory `input_file` was discovered under, used
        to compute its destination path under `output_dir`
    :param output_dir: directory to write the (possibly compressed) file to
    :param input_file: path to the PNG/JPG file to check/compress
    :param target_kb: target maximum size, in KB
    :param in_place: if True, `input_dir` and `output_dir` are the same
        directory: compress/overwrite the file in place instead of writing a
        copy to `output_dir`
    :param quality_step: amount to decrease JPEG quality by at each attempt
    :param min_quality: lowest JPEG quality to try before giving up
    :param dry_run: if True, report what would happen without touching files
    :return: report row with keys `file`, `old_format`, `new_format`,
        `old_size_kb`, `new_size_kb`, `status`
        ```
        {'file': 'foo.png', 'old_format': 'png', 'new_format': 'jpg',
         'old_size_kb': 620.3, 'new_size_kb': 480.1, 'status': 'compressed'}
        ```
    """
    rel_path = os.path.relpath(input_file, input_dir)
    old_format = os.path.splitext(input_file)[1].lstrip(".").lower()
    old_size = os.path.getsize(input_file)
    target_bytes = target_kb * 1024
    row: Dict[str, object] = {
        "file": rel_path,
        "old_format": old_format,
        "new_format": old_format,
        "old_size_kb": old_size / 1024.0,
        "new_size_kb": old_size / 1024.0,
        "status": "skipped",
    }
    # Destination if the file ends up untouched: same relative path/extension.
    unchanged_file = os.path.join(output_dir, rel_path)
    if old_size <= target_bytes:
        _LOG.debug(
            "Skipping '%s': %d bytes already <= target %d bytes",
            input_file,
            old_size,
            target_bytes,
        )
        _copy_unchanged(
            input_file, unchanged_file, in_place=in_place, dry_run=dry_run
        )
        return row
    # Compressed output always goes to `<basename>.jpg` under `output_dir`.
    output_file = os.path.join(
        output_dir, f"{os.path.splitext(rel_path)[0]}.{_TARGET_FORMAT}"
    )
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would compress '%s' (%.1f KB) -> '%s' (target %d KB)",
            input_file,
            old_size / 1024.0,
            output_file,
            target_kb,
        )
        row["new_format"] = _TARGET_FORMAT
        row["status"] = "would_compress"
        return row
    # Guard against clobbering an unrelated file that happens to already have
    # the target name (e.g. a `foo.png` and an unrelated pre-existing `foo.jpg`).
    if os.path.exists(output_file) and os.path.abspath(
        output_file
    ) != os.path.abspath(input_file):
        raise RuntimeError(
            f"Target '{output_file}' already exists and differs from "
            f"'{input_file}': refusing to overwrite it"
        )
    hio.create_dir(os.path.dirname(output_file) or ".", incremental=True)
    # Compress into a temporary file first, then atomically swap it in, so a
    # failed/interrupted run never leaves a half-written image on disk.
    tmp_output_file = f"{output_file}.tmp"
    new_size = _compress_image_to_target(
        input_file,
        tmp_output_file,
        target_bytes,
        quality_step=quality_step,
        min_quality=min_quality,
    )
    if new_size >= old_size:
        # JPEG re-encoding can grow simple/flat-color images (e.g. plots with
        # large solid areas) instead of shrinking them: keep the original.
        os.remove(tmp_output_file)
        _LOG.warning(
            "'%s': JPEG re-encoding (%.1f KB) is not smaller than the "
            "original (%.1f KB), keeping original",
            input_file,
            new_size / 1024.0,
            old_size / 1024.0,
        )
        _copy_unchanged(
            input_file, unchanged_file, in_place=in_place, dry_run=dry_run
        )
        row["status"] = "kept_original"
        return row
    os.replace(tmp_output_file, output_file)
    if in_place and output_file != input_file:
        # Format changed (e.g. PNG -> JPG): drop the now-superseded original.
        os.remove(input_file)
    row["new_format"] = _TARGET_FORMAT
    row["new_size_kb"] = new_size / 1024.0
    row["status"] = "compressed"
    return row


def _compress_dir(
    input_dir: str,
    output_dir: str,
    target_kb: int,
    *,
    recursive: bool = False,
    quality_step: int = 5,
    min_quality: int = 10,
    dry_run: bool = False,
    force: bool = False,
) -> pd.DataFrame:
    """
    Compress every PNG/JPG figure above `target_kb` under `input_dir`.

    :param input_dir: directory containing the figures
    :param output_dir: directory to write (possibly compressed) figures to
        - If it differs from `input_dir`, figures are copied/compressed into
          it and `input_dir` is left untouched
        - If it is the same as `input_dir`, `force` must be True and figures
          are compressed in place
    :param target_kb: target maximum size, in KB
    :param recursive: if True, also process subdirectories
    :param quality_step: amount to decrease JPEG quality by at each attempt
    :param min_quality: lowest JPEG quality to try before giving up
    :param dry_run: if True, report what would happen without touching files
    :param force: if True, allow `input_dir` and `output_dir` to be the same
    :return: one row per processed file, see `_compress_file()`
    """
    _dassert_magick_installed()
    _dassert_dirs_same_requires_force(input_dir, output_dir, force=force)
    in_place = os.path.realpath(input_dir) == os.path.realpath(output_dir)
    image_files = _find_image_files(input_dir, recursive=recursive)
    _LOG.info(
        "Found %d PNG/JPG file(s) under '%s' (target=%d KB, output_dir='%s')",
        len(image_files),
        input_dir,
        target_kb,
        output_dir,
    )
    if not in_place and not dry_run:
        hio.create_dir(output_dir, incremental=True)
    rows = []
    for input_file in tqdm.tqdm(image_files, desc="Compressing figures"):
        row = _compress_file(
            input_dir,
            output_dir,
            input_file,
            target_kb,
            in_place=in_place,
            quality_step=quality_step,
            min_quality=min_quality,
            dry_run=dry_run,
        )
        rows.append(row)
    report = pd.DataFrame(rows)
    return report


def _print_report(report: pd.DataFrame, target_kb: int) -> None:
    """
    Print a summary of the compression report, highlighting format changes
    and size reduction.

    :param report: report returned by `_compress_dir()`
    :param target_kb: target maximum size, in KB, used for the summary line
    """
    if report.empty:
        _LOG.info("No PNG/JPG files found")
        return
    # Full per-file report.
    report_out = report.copy()
    report_out["old_size_kb"] = report_out["old_size_kb"].round(1)
    report_out["new_size_kb"] = report_out["new_size_kb"].round(1)
    _LOG.info("\n%s", hprint.frame("Compression report"))
    _LOG.info("\n%s", report_out.to_string(index=False))
    # Files that changed format (e.g., PNG -> JPG).
    changed = report[report["old_format"] != report["new_format"]]
    _LOG.info("\n%s", hprint.frame("Files that changed type"))
    if changed.empty:
        _LOG.info("No file changed type")
    else:
        for _, row in changed.iterrows():
            _LOG.info(
                "'%s': %s -> %s", row["file"], row["old_format"], row["new_format"]
            )
    # Overall size savings, restricted to files that were actually touched.
    above_target = report[
        report["status"].isin(["compressed", "would_compress", "kept_original"])
    ]
    touched = report[report["status"].isin(["compressed", "would_compress"])]
    kept_original = report[report["status"] == "kept_original"]
    total_old_kb = touched["old_size_kb"].sum()
    total_new_kb = touched["new_size_kb"].sum()
    _LOG.info("\n%s", hprint.frame("Summary"))
    _LOG.info("Target size: %d KB", target_kb)
    _LOG.info("Files above target: %d / %d", len(above_target), len(report))
    if not kept_original.empty:
        _LOG.info(
            "Files kept unchanged (JPEG would be larger): %d",
            len(kept_original),
        )
    if total_old_kb > 0:
        savings_pct = 100.0 * (1.0 - total_new_kb / total_old_kb)
        _LOG.info(
            "Total size: %.1f KB -> %.1f KB (%.1f%% reduction)",
            total_old_kb,
            total_new_kb,
            savings_pct,
        )


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        action="store",
        required=True,
        help="Directory containing PNG/JPG figures to compress",
    )
    parser.add_argument(
        "--output_dir",
        action="store",
        required=True,
        help="Directory to write (possibly compressed) figures to",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Allow --input_dir and --output_dir to be the same directory "
            "(compress figures in place)"
        ),
    )
    parser.add_argument(
        "--target_kb",
        action="store",
        type=int,
        default=500,
        help="Target maximum file size, in KB",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Also process figures in subdirectories",
    )
    parser.add_argument(
        "--quality_step",
        action="store",
        type=int,
        default=5,
        help="Amount to decrease JPEG quality by at each compression attempt",
    )
    parser.add_argument(
        "--min_quality",
        action="store",
        type=int,
        default=10,
        help="Lowest JPEG quality to try before giving up on reaching the target",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be compressed without touching any file",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    report = _compress_dir(
        args.input_dir,
        args.output_dir,
        args.target_kb,
        recursive=args.recursive,
        quality_step=args.quality_step,
        min_quality=args.min_quality,
        dry_run=args.dry_run,
        force=args.force,
    )
    _print_report(report, args.target_kb)


if __name__ == "__main__":
    _main(_parse())
