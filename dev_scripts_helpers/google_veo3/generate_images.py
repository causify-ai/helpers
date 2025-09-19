#!/usr/bin/env python3

# https://ai.google.dev/gemini-api/docs/video?example=dialogue

import argparse
import base64
import logging
import mimetypes
import os
from platform import java_ver
import pprint
import time
from typing import Any, Dict, List, Optional

import tqdm
import google.genai as genai
import google.genai.types as genai_types

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def run_test(test_name: str, dst_dir: str) -> None:
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    hdbg.dassert(api_key, "Environment variable GOOGLE_GENAI_API_KEY is not set")
    # Initialize client.
    client = genai.Client(api_key=api_key)
    # Ensure destination directory exists.
    hio.create_dir(dst_dir, incremental=True)
    #
    if test_name == "dialogue":
        prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
        A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'"""
    elif test_name == "imagen":
        prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"
    elif test_name == "parameters":
        prompt="A cinematic shot of a majestic lion in the savannah."
    else:
        raise ValueError(f"Invalid test name: {test_name}")
    count = 1
    for i in range(count):
        # Step 1: Generate an image with Imagen.
        imagen = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=genai_types.GenerateImagesConfig(
                number_of_images= 4,
            )
        )
        for j in range(4):
            file_name = "%s/imagen_example.%s.%s.png" % (dst_dir, i, j)
            imagen.generated_images[j].image.save(file_name)
            _LOG.info("Saved image to %s", file_name)
    _LOG.info("Image generation complete. Images saved to: %s", dst_dir)


def _parse() -> argparse.ArgumentParser:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--test_name",
        required=True,
    )
    parser.add_argument(
        "--dst_dir",
        required=True,
        help="Destination directory for generated images",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    run_test(args.test_name, args.dst_dir)

if __name__ == "__main__":
    _main(_parse())
