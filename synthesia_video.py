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
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

API_BASE = "https://api.synthesia.io/v2"
TIMEOUT = 30  # seconds per HTTP request
POLL_EVERY = 6  # seconds between status polls
MAX_WAIT = 60 * 30  # 30 minutes max


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
    aspect_ratio: str = "5:4",
    resolution: str = "720p",
    audio_only: bool = False,
    test: bool = False,
    #extra_scene_overrides: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a Synthesia video. Returns the video_id from the 201 response.

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
    #payload["test"] = False
    #payload["test"] = True

    resp = requests.post(url, headers=_headers(api_key), data=json.dumps(payload), timeout=TIMEOUT)
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Synthesia video from text + avatar and download it.")
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
    args = parser.parse_args()

    api_key = os.getenv("SYNTHESIA_API_KEY")
    if not api_key:
        print("Environment variable SYNTHESIA_API_KEY is not set.", file=sys.stderr)
        sys.exit(2)

    # extra = None
    # if args.extra:
    #     try:
    #         extra = json.loads(args.extra)
    #     except json.JSONDecodeError as e:
    #         print(f"--extra must be valid JSON: {e}", file=sys.stderr)
    #         sys.exit(2)
    slides = []
    script = """
Hi, I’m <sub alias="GP sah-JEH-seh">GP Saggese</sub>, co-founder and CTO of Causify AI.
I hold a PhD in Electrical and Computer Engineering from UIUC, and for the past 20 years I’ve built high-performance machine learning systems at companies such as NVIDIA, Intel, and Synopsys.

I also bring over 15 years of experience in systematic hedge funds—working as a portfolio manager, quant, head of data, and leading software platform development.
"""
    out_file="slide1"
    slides.append((script, out_file))
    #
    script = """
<sub alias="">https://docs.google.com/document/d/18SywZGD4HskyqMZyBsecZRJtbQo8fDH_eokeX_00S6E</sub>

Over the past two years, Causify has developed and licensed a powerful platform designed specifically for hedge funds and asset managers.

- Streamlines data onboarding, alpha signal development, risk model testing, and strategy optimization
- Supports the full lifecycle—from research and backtesting to deployment, live trading, monitoring, and refinement
- Operates seamlessly across time horizons ranging from minutes to weeks

The platform represents over a decade of engineering effort and more than one million lines of production code.
In short, it is best described as a quantitative hedge fund in a box.

It natively supports causal modeling, has been battle-tested in live markets, and today manages approximately $6 billion in AUM across equities and cryptocurrency for several hedge funds.
    """
    out_file="slide2"
    slides.append((script, out_file))
    #
    script = """
KaizenFlow allows teams to rapidly build, test, and deploy AI-driven trading strategies using state-of-the-art techniques, including:

- A fully probabilistic, explainable causal AI engine grounded in Bayesian theory
- An automated pipeline that accelerates the journey from idea to production—reducing deployment time from six months to under four weeks
- A proprietary real-time data processing engine that identifies alpha signals even in environments with non-stationarity and non-Gaussian distributions

The result:

- 5x increase in productivity
- Reduced engineering costs
- A platform that empowers quants, quant developers, and DevOps teams
- Managers scale faster by tapping into a wider pool of available talent

The platform is modular, covering the full workflow:

- Data Onboarding
- Feature Engineering
- Alpha Generation
- Risk Modeling
- Portfolio Optimization
- Risk & Execution Management

It supports both batch and streaming time-series workflows, enforces precise timing semantics, and prevents common pitfalls like look-ahead bias.

Additional features include:

- High observability and debuggability
- Incremental and cached computation
- Parallelism and scalability
- Direct integration with Jupyter notebooks and APIs
- Full support for Airflow scheduling and monitoring
    """
    out_file="slide3"
    slides.append((script, out_file))
    #
    script = """
We’ve begun releasing components of Kaizen Flow as standalone SaaS applications:

Strategy Manager Dashboard – For performance tracking, correlation analysis, and reporting
Risk & Performance Dashboard – For VaR, volatility, and exposure monitoring
Portfolio Optimization Tool – For mean-variance optimization and efficient frontier analysis

Each application is designed with modern, intuitive UIs, drag-and-drop data uploads, and flexible export/reporting options.
    """
    out_file="slide4"
    slides.append((script, out_file))
    #
    script = """
We provide interactive dashboards that let users:

- Track key performance metrics (e.g., Sharpe ratio, annualized return, volatility, drawdowns)
- Compare correlations across managers and strategies
- Generate automated reports in CSV or Excel format
- Slice, dice, and visualize data over selected time ranges or head-to-head comparisons

Our risk management components allow users to:

- Compute volatility and value-at-risk (VaR) at multiple confidence levels
- Perform rolling risk estimates and monitor exposures
- Run event analysis, measuring strategy performance under specific market conditions
    """
    out_file="slide5"
    slides.append((script, out_file))
    #
    script = """
The portfolio construction module enables:

- Optimal allocation of capital given alpha forecasts and current positions
- Mean-variance optimization and advanced risk-based approaches
- Incorporation of market impact models (both transient and persistent)
- Constraints such as diversification and risk-budgeting
- Scenario analysis with custom inputs and overrides

Outputs include:

- The efficient frontier for trade-offs between expected return and volatility
- Portfolio simulations under varying covariance matrix estimations and risk preferences
    """
    out_file="slide7"
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
                #extra_scene_overrides=extra,
            )
            print(f"Created video: id={video_id}")
        except requests.RequestException as e:
            print(f"HTTP error: {e}", file=sys.stderr)
            sys.exit(1)
        except SynthesiaError as e:
            print(f"Synthesia API error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

