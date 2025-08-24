#!/usr/bin/env python3
"""
Synthesia API helper: create a video from a text script and a chosen avatar,
then poll until it's ready and download the MP4 (plus captions if available).

Usage (CLI):
  python synthesia_video.py \
    --script "Hello from the Synthesia API!" \
    --avatar anna_costume1_cameraA \
    --title "Demo via API" \
    --out demo.mp4

Environment:
  SYNTHESIA_API_KEY  Your Synthesia API key (Creator plan or above).

Notes:
- Avatar IDs: see https://docs.synthesia.io/reference/avatars (e.g. 'anna_costume1_cameraA').
- The script uses the v2 endpoints: POST /v2/videos and GET /v2/videos/{id}.
- By default, runs in test mode ("--no-test" to disable).
- If captions are available, the script will also download .srt and .vtt.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict

import requests

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser

_LOG = logging.getLogger(__name__)

API_BASE = "https://api.synthesia.io/v2"
TIMEOUT = 30  # seconds per HTTP request
POLL_EVERY = 6  # seconds between status polls
MAX_WAIT = 60 * 30  # 30 minutes max


# #############################################################################
# SynthesiaError
# #############################################################################


class SynthesiaError(RuntimeError):
    pass


def _headers(api_key: str) -> Dict[str, str]:
    # Synthesia docs instruct to place the API key in the Authorization header.
    # Do not prefix with "Bearer" unless your account specifically requires it.
    return {
        "Authorization": api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_video(
    api_key: str,
    script_text: str,
    avatar: str,
    title: str,
    background: str,
    *,
    aspect_ratio: str = "5:4",
    resolution: str = "720p",
    audio_only: bool = False,
    test: bool = False,
    # extra_scene_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a Synthesia video. Returns the video_id from the 201 response.

    The minimal required fields per docs are provided below: title, input (scenes),
    and inside a scene: scriptText + avatar. Background is optional.
    """
    url = f"{API_BASE}/videos"
    scene: Dict[str, Any] = {
        "scriptText": script_text,
    }

    # Always set avatar and background - Synthesia API requires these fields
    scene["avatar"] = avatar
    if background:
        scene["background"] = background

    # if extra_scene_overrides:
    #     scene.update(extra_scene_overrides)

    payload: Dict[str, Any] = {
        "title": title,
        "input": [scene],
    }

    # Add video parameters (required even for audio-only in this API)
    if aspect_ratio:
        payload["aspectRatio"] = aspect_ratio
    if resolution:
        payload["resolution"] = resolution

    if test:
        payload["test"] = test
    # payload["test"] = False
    # payload["test"] = True

    resp = requests.post(
        url, headers=_headers(api_key), data=json.dumps(payload), timeout=TIMEOUT
    )
    if resp.status_code != 201:
        raise SynthesiaError(
            f"Create video failed ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    video_id = data.get("id") or data.get("videoId")
    if not video_id:
        raise SynthesiaError(f"Unexpected response (no video id): {data}")
    return video_id


# def get_video(api_key: str, video_id: str) -> Dict[str, Any]:
#     url = f"{API_BASE}/videos/{video_id}"
#     resp = requests.get(url, headers=_headers(api_key), timeout=TIMEOUT)
#     if resp.status_code != 200:
#         raise SynthesiaError(
#             f"Retrieve video failed ({resp.status_code}): {resp.text}"
#         )
#     return resp.json()


# def wait_until_ready(api_key: str, video_id: str, *, max_wait: int = MAX_WAIT, poll_every: int = POLL_EVERY) -> Dict[str, Any]:
#     """Poll the video until status == 'completed' or failure/timeout. Returns the final video object."""
#     started = time.time()
#     last_status = None
#     while True:
#         video = get_video(api_key, video_id)
#         status = video.get("status") or video.get("state")
#         if status != last_status:
#             print(f"[status] {status}")
#             last_status = status
#         if status == "completed":
#             return video
#         if status in {"failed", "rejected", "error"}:
#             raise SynthesiaError(f"Video processing did not complete successfully: {status} -> {video}")
#         if time.time() - started > max_wait:
#             raise SynthesiaError("Timed out waiting for video to complete")
#         time.sleep(poll_every)


# def _download(url: str, out_path: str) -> None:
#     with requests.get(url, stream=True, timeout=TIMEOUT) as r:
#         r.raise_for_status()
#         with open(out_path, "wb") as f:
#             for chunk in r.iter_content(chunk_size=1024 * 512):
#                 if chunk:
#                     f.write(chunk)


# def download_assets(video_obj: Dict[str, Any], out_video: str, out_dir: Optional[str] = None) -> None:
#     """Download the MP4 and any available captions from the retrieve response.

#     The retrieve endpoint returns a 'download' object with short-lived URLs for
#     mp4, captions, and thumbnails. We only download MP4/SRT/VTT here.
#     """
#     dl = video_obj.get("download") or {}

#     mp4_url = dl.get("video") or dl.get("mp4")
#     if not mp4_url:
#         raise SynthesiaError("No downloadable MP4 URL found in response")

#     _download(mp4_url, out_video)
#     print(f"Saved video to {out_video}")

#     # Try captions if present
#     if out_dir is None:
#         out_dir = os.path.dirname(os.path.abspath(out_video)) or "."

#     srt_url = dl.get("captions", {}).get("srt") or dl.get("srt")
#     vtt_url = dl.get("captions", {}).get("vtt") or dl.get("vtt")

#     if srt_url:
#         srt_path = os.path.join(out_dir, os.path.splitext(os.path.basename(out_video))[0] + ".srt")
#         _download(srt_url, srt_path)
#         print(f"Saved captions (SRT) to {srt_path}")
#     if vtt_url:
#         vtt_path = os.path.join(out_dir, os.path.splitext(os.path.basename(out_video))[0] + ".vtt")
#         _download(vtt_url, vtt_path)
#         print(f"Saved captions (VTT) to {vtt_path}")


def _parse() -> argparse.Namespace:
    """
    Parse command line arguments.

    :return: parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Create a Synthesia video from text + avatar and download it."
    )
    hparser.add_verbosity_arg(parser)
    # parser.add_argument("--script", required=True, help="The text to speak in the scene (scriptText)")
    # parser.add_argument("--avatar", required=False, help="Avatar ID (e.g. anna_costume1_cameraA) - not needed for audio-only")
    # parser.add_argument("--title", default="API Video via Python")
    # parser.add_argument("--background", default="green_screen", help="Optional background identifier")
    # parser.add_argument("--aspect", default="16:9", help="Aspect ratio, e.g. 16:9, 9:16, 1:1")
    # parser.add_argument("--resolution", default="360p", help="Video resolution, e.g. 360p, 480p, 720p, 1080p")
    # parser.add_argument("--audio-only", action="store_true", help="Generate audio-only output (voice without video)")
    # parser.add_argument("--out", default="output.mp4", help="Where to save the MP4")
    # parser.add_argument("--no-test", action="store_true", help="Disable test mode (videos may count against your quota)")
    # parser.add_argument("--extra", default=None, help="JSON for extra per-scene overrides (advanced)")
    parser.add_argument("--slide", type=int, default=0, help="Slide number")
    parser.add_argument("--in_dir", default="videos", help="Directory containing xyz_text.txt files")
    parser.add_argument("--slides", help="Range of slides to process (e.g., '001:003', '002:005,007:009')")
    args = parser.parse_args()
    return args


def _main(args: argparse.Namespace) -> None:
    """
    Main function to create Synthesia videos.

    :param args: parsed arguments
    """
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    api_key = os.getenv("SYNTHESIA_API_KEY")
    hdbg.dassert(api_key, "Environment variable SYNTHESIA_API_KEY is not set")
    # extra = None
    # if args.extra:
    #     try:
    #         extra = json.loads(args.extra)
    #     except json.JSONDecodeError as e:
    #         print(f"--extra must be valid JSON: {e}", file=sys.stderr)
    #         sys.exit(2)
    slides = []
    in_dir = args.in_dir
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "001_text.txt"))
    out_file = "slide1"
    slides.append((script, out_file))
    #
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "002_text.txt"))
    out_file = "slide2"
    slides.append((script, out_file))
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "003_text.txt"))
    out_file = "slide3"
    slides.append((script, out_file))
    #
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "004_text.txt"))
    out_file = "slide4"
    slides.append((script, out_file))
    #
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "005_text.txt"))
    out_file = "slide5"
    slides.append((script, out_file))
    #
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "007_text.txt"))
    out_file = "slide7"
    slides.append((script, out_file))
    # Read script from file.
    script = hio.from_file(os.path.join(in_dir, "009_text.txt"))
    out_file = "slide8"
    slides.append((script, out_file))
    for script, out_file in slides[1:]:
        try:
            avatar = "f4f1005e-6851-414a-9120-d48122613fa0"
            background = "workspace-media.c4ab7049-8479-4855-9856-e0d7f2854027"
            aspect = "5:4"
            resolution = "720p"
            audio_only = False
            test = False
            video_id = create_video(
                api_key=api_key,
                script_text=script,
                avatar=avatar,
                title=out_file,
                background=background,
                aspect_ratio=aspect,
                resolution=resolution,
                audio_only=audio_only,
                test=test,
                # extra_scene_overrides=extra,
            )
            _LOG.info(f"Created video: id={video_id}")
        except requests.RequestException as e:
            _LOG.error(f"HTTP error: {e}")
            sys.exit(1)
        except SynthesiaError as e:
            _LOG.error(f"Synthesia API error: {e}")
            sys.exit(1)


def main() -> None:
    """
    Main entry point.
    """
    args = _parse()
    _main(args)


if __name__ == "__main__":
    main()
