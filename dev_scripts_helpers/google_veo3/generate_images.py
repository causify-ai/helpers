#!/usr/bin/env python3

# https://ai.google.dev/gemini-api/docs/video?example=dialogue

import argparse
import base64
import logging
import os
import requests

import google.genai as genai
import google.genai.types as genai_types

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


def _get_access_token() -> str:
    """
    Get Google Cloud access token using gcloud CLI.
    """
    # Get access token using gcloud.
    cmd = "gcloud auth print-access-token"
    _, output = hsystem.system_to_string(cmd)
    token = output.strip()
    hdbg.dassert(token, "Failed to get access token")
    return token


def _generate_images_rest_api(
    model_name: str,
    prompt: str,
    j: int,
    num_images: int,
    dst_dir: str,
    project_id: str,
    location: str = "us-central1",
) -> None:
    """
    Generate images using Vertex AI REST API.

    :param model_name: model name to use
    :param dst_dir: destination directory for images
    :param project_id: Google Cloud project ID
    :param location: Google Cloud location
    """
    # Get access token.
    access_token = _get_access_token()
    # Prepare REST API request.
    endpoint = "https://%s-aiplatform.googleapis.com/v1/projects/%s/locations/%s/publishers/google/models/%s:predict" % (
        location,
        project_id,
        location,
        model_name,
    )
    headers = {
        "Authorization": "Bearer %s" % access_token,
        "Content-Type": "application/json",
    }
    data = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "addWatermark": False,
            "enhancePrompt": False,
            "sampleCount": num_images,
            "seed": 42,
        },
    }
    # Make REST API call.
    _LOG.info("Making REST API call to: %s", endpoint)
    response = requests.post(endpoint, headers=headers, json=data)
    hdbg.dassert_eq(
        response.status_code,
        200,
        "REST API call failed with status code: %s, response: %s",
        response.status_code,
        response.text,
    )
    # Process response.
    result = response.json()
    predictions = result.get("predictions", [])
    hdbg.dassert(predictions, "No predictions in response")
    # Save images.
    hio.create_dir(dst_dir, incremental=True)
    for i, prediction in enumerate(predictions):
        # Decode base64 image data.
        image_data = prediction.get("bytesBase64Encoded", "")
        hdbg.dassert(image_data, "No image data in prediction %s", i)
        image_bytes = base64.b64decode(image_data)
        # Save image to file.
        file_name = "%s/imagen_rest.%s.%s.png" % (dst_dir, j, i)
        with open(file_name, "wb") as f:
            f.write(image_bytes)
        _LOG.info("Saved image to %s", file_name)
    _LOG.info("REST API image generation complete. Images saved to: %s", dst_dir)


def run_test(test_name: str, dst_dir: str, incremental: bool, use_rest_api: bool) -> None:
    # Ensure destination directory exists.
    hio.create_dir(dst_dir, incremental=incremental)
    if False:
        style = """
        Use a cartoon style, clean, modern flat-style business visual — the kind used in SaaS
        product demos or startup pitch decks, using a blue color palette, fresh,
        energetic look.
        """
    else:
        style = """
        Use a cartoon style like Studio Ghibli.
        """
    prompts = []
    prompts.append("""
    A busy boardroom with executives debating a decision (launching a product, investing in a new market)
    around a single table with 4 people around it.
    """)
    prompts.append("""
    An overconfident manager slams a report on the table.
    """)
    prompts.append("""
    Dice rolling across the table of a boardroom.
    """)
    prompts.append("""
    A decision-maker updates forecasts as new data arrives (market trends, customer feedback).
    """)
    prompts.append("""
    The executive team revisits their decision with a dashboard showing
    probabilities and confidence bands around the table. They nod with
    confidence and move forward.
    """)
    # # Determine prompt based on test name.
    # if test_name == "dialogue":
    #     prompt = """A close up of two people staring at a cryptic drawing on a wall, torchlight flickering.
    #     """
    # elif test_name == "imagen":
    #     prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"
    # elif test_name == "parameters":
    #     prompt = "A cinematic shot of a majestic lion in the savannah."
    # elif test_name == "test":
    #     prompt = """
    #     A busy boardroom with executives debating a decision (launching a product, investing in a new market).
    #     """
    # elif test_name == "test2":
    #     prompt = """
    #     A close up of two people staring at a cryptic drawing to a whiteboard.
    #     """
    # else:
    #     raise ValueError("Invalid test name: %s" % test_name)
    num_images = 4
    for i, prompt in enumerate(prompts):
        prompt += "\n\n" + style
        dst_dir_tmp = dst_dir
        # Generate images using Python SDK.
        #model_name = "imagen-4.0-fast-generate-001"
        model_name = "imagen-4.0-generate-001"
        # Choose API method.
        if use_rest_api:
            project_id = "skilled-bonus-472420-m5"
            hdbg.dassert(project_id, "Project ID is required when using REST API")
            _generate_images_rest_api(
                model_name,
                prompt,
                i,
                num_images,
                dst_dir_tmp,
                project_id=project_id,
            )
        else:
            # Use Python SDK.
            api_key = os.getenv("GOOGLE_GENAI_API_KEY")
            hdbg.dassert(api_key, "Environment variable GOOGLE_GENAI_API_KEY is not set")
            # Initialize client.
            client = genai.Client(api_key=api_key)
            # Step 1: Generate an image with Imagen.
            imagen = client.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=genai_types.GenerateImagesConfig(
                    number_of_images=num_images,
                )
            )
            hio.create_dir(dst_dir, incremental=True)
            for j in range(4):
                file_name = "%s/imagen.%s.%s.png" % (dst_dir, i, j)
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
        help="Destination directory for generated images",
    )
    parser.add_argument(
        "--use_rest_api",
        action="store_true",
        help="Use REST API instead of Python SDK",
    )
    parser.add_argument(
        "--from_scratch",
        action="store_true",
        help="Start from scratch",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    dst_dir = args.dst_dir or args.test_name
    run_test(
        args.test_name,
        dst_dir,
        not args.from_scratch,
        args.use_rest_api,
    )

if __name__ == "__main__":
    _main(_parse())
