#!/usr/bin/env python3

# https://ai.google.dev/gemini-api/docs/video?example=dialogue

import argparse
import base64
import logging
import mimetypes
import os
import pprint
import time
from typing import Dict, List, Optional

import tqdm
import google.genai as genai
import google.genai.types as genai_types

import helpers.hdbg as hdbg
import helpers.hprint as hprint
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)


def wait_for_video_generation(client, operation, poll_interval_secs: int = 2) -> None:
    """
    Wait for video generation to complete and print progress.
    
    :param operation: The video generation operation to monitor
    :param poll_interval_secs: How often to check status in seconds (default: 2)
    """
    start_time = time.time()
    while not operation.done:
        elapsed = int(time.time() - start_time)
        print(f"Waiting for video generation to complete... ({elapsed}s)")
        time.sleep(poll_interval_secs)
        operation = client.operations.get(operation)


def save_generated_video(client, operation, output_file: str) -> None:
    """
    Save the generated video from the operation to a file.

    :param operation: The completed video generation operation
    :param output_file: Path where the video should be saved
    """
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video)
    generated_video.video.save(output_file)
    print(f"Generated video saved to {output_file}")


def run_test(test_name: str) -> None:
    api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    hdbg.dassert(api_key, "Environment variable GOOGLE_GENAI_API_KEY is not set")
    # Initialize client.
    client = genai.Client(api_key=api_key)
    # Get Veo model.
    model_name = "veo-3.0-fast-generate-preview"
    #model = client.models.get(model="veo-3.0-generate-001")
    # veo-3.0-fast-generate-001
    # veo-3.0-generate-preview
    # veo-3.0-fast-generate-preview
    _LOG.info("Veo model name=%s", model_name)
    #
    if test_name == "dialogue":
        prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
        A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'"""
        operation = client.models.generate_videos(
            model=model_name,
            prompt=prompt,
        )
        file_name = "dialogue_example.%s.mp4" % model_name
    elif test_name == "imagen":
        prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"
        # Step 1: Generate an image with Imagen.
        imagen = client.models.generate_images(
            client=client,
            model="imagen-4.0-generate-001",
            prompt=prompt,
        )
        # Step 2: Generate video with Veo 3 using the image.
        operation = client.models.generate_videos(
            client=client,
            model=model_name,
            prompt=prompt,
            image=imagen.generated_images[0].image,
        )
        file_name = "imagen_example.%s.mp4" % model_name
    elif test_name == "parameters":
        prompt="A cinematic shot of a majestic lion in the savannah."
        config = genai_types.GenerateVideosConfig(negative_prompt="cartoon, drawing, low quality")
        operation = client.models.generate_videos(
            client=client,
            model=model_name,
            prompt=prompt,
            config=config
        )
        file_name = "parameters_example.%s.mp4" % model_name
    else:
        raise ValueError(f"Invalid test name: {test_name}")
    wait_for_video_generation(client, operation)
    save_generated_video(client, operation, file_name)

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
        "--low_res",
        action="store_true",
        help="Use low resolution settings for faster rendering (480p, 4s duration, seed=42)"
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Main function to generate videos from storyboard.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    run_test(args.test_name)

if __name__ == "__main__":
    _main(_parse())
