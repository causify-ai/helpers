#!/usr/bin/env python
"""
Restart Docker Desktop if `docker container ps` hangs.

Runs `docker container ps` bounded by a timeout. If the command does not
complete in time, the script kills it, restarts Docker Desktop, and waits
until Docker is responsive again before exiting.

Usage examples:
```
# Check with the default 10s timeout and restart Docker Desktop if needed.
> docker_restart_if_needed.py

# Use a shorter timeout and poll more frequently while waiting for Docker.
> docker_restart_if_needed.py --timeout_in_secs 5 --poll_interval_in_secs 2
```

Import as:

import dev_scripts_helpers.system_tools.docker_restart_if_needed as dsstdrin
"""

import argparse
import logging
import subprocess
import time

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Docker health check.
# #############################################################################


def _is_docker_ps_hanging(*, timeout_in_secs: int) -> bool:
    """
    Run `docker container ps` and report whether it exceeds the timeout.

    Kills the underlying process if it does not complete in time, since a
    hanging `docker container ps` is a common symptom of a wedged Docker
    Desktop daemon on macOS.

    :param timeout_in_secs: max number of seconds to wait for `docker
        container ps` to complete
    :return: True if the command did not complete within
        `timeout_in_secs`
    """
    _LOG.debug(hprint.to_str("timeout_in_secs"))
    cmd = ["docker", "container", "ps"]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # `Popen.wait(timeout=...)` is the standard way to bound a subprocess and
    # detect a hang via `TimeoutExpired`; `hsystem.system()` has no
    # equivalent timeout support, so we drop to `subprocess` directly here.
    try:
        process.wait(timeout=timeout_in_secs)
        is_hanging = False
    except subprocess.TimeoutExpired:
        _LOG.warning(
            "'docker container ps' did not complete within %d seconds: "
            "killing it",
            timeout_in_secs,
        )
        process.kill()
        process.wait()
        is_hanging = True
    _LOG.debug("return=%s", is_hanging)
    return is_hanging


def _restart_docker_desktop() -> None:
    """
    Restart Docker Desktop via `docker desktop restart`.
    """
    _LOG.info("Restarting Docker Desktop")
    hsystem.system("docker desktop restart")


def _wait_for_docker_to_be_ready(*, poll_interval_in_secs: int) -> None:
    """
    Poll `docker info` until Docker responds, then log readiness.

    :param poll_interval_in_secs: number of seconds to sleep between
        polls
    """
    _LOG.debug(hprint.to_str("poll_interval_in_secs"))
    _LOG.info("Waiting for Docker to come back up")
    while True:
        rc = hsystem.system(
            "docker info", abort_on_error=False, suppress_output=True
        )
        if rc == 0:
            break
        time.sleep(poll_interval_in_secs)
    _LOG.info("ready")


# #############################################################################
# CLI.
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--timeout_in_secs",
        type=int,
        default=5,
        help="Max number of seconds to wait for `docker container ps`",
    )
    parser.add_argument(
        "--poll_interval_in_secs",
        type=int,
        default=1,
        help="Number of seconds to wait between `docker info` polls",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug(hprint.to_str("args.timeout_in_secs args.poll_interval_in_secs"))
    is_hanging = _is_docker_ps_hanging(timeout_in_secs=args.timeout_in_secs)
    if is_hanging:
        _restart_docker_desktop()
        _wait_for_docker_to_be_ready(
            poll_interval_in_secs=args.poll_interval_in_secs
        )
    else:
        _LOG.info("Docker is responsive: nothing to do")


if __name__ == "__main__":
    _main(_parse())
