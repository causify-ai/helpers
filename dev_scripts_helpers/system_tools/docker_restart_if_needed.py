#!/usr/bin/env python
"""
Restart a container engine if it hangs.

Runs a lightweight list command (`docker container ps` / `container list`)
bounded by a timeout, for the selected engine(s). If the command does not
complete in time, the script kills it, restarts the engine, and waits until
it is responsive again before exiting.

Usage examples:
```
# Check both engines with the default 5s timeout and restart whichever
# engine is hanging.
> docker_restart_if_needed.py

# Check only Docker Desktop.
> docker_restart_if_needed.py --docker_engine docker

# Check only the Apple `container` system.
> docker_restart_if_needed.py --docker_engine apple

# Use a shorter timeout and poll more frequently while waiting for the
# engine to come back up.
> docker_restart_if_needed.py --timeout_in_secs 5 --poll_interval_in_secs 2
```

Import as:

import dev_scripts_helpers.system_tools.docker_restart_if_needed as dsstdrin
"""

import argparse
import logging
import subprocess
import time
from typing import List

import helpers.hdbg as hdbg
import helpers.hdocker as hdocker
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)


# #############################################################################
# Engine health check.
# #############################################################################


def _is_engine_hanging(engine: str, *, timeout_in_secs: int) -> bool:
    """
    Run a lightweight list command for `engine` and report whether it
    exceeds the timeout.

    Kills the underlying process if it does not complete in time, since a
    hanging list command is a common symptom of a wedged engine daemon on
    macOS.

    :param engine: `"docker"` or `"apple"`
    :param timeout_in_secs: max number of seconds to wait for the list
        command to complete
    :return: True if the command did not complete within
        `timeout_in_secs`
    """
    _LOG.debug(hprint.to_str("engine timeout_in_secs"))
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    if engine == "docker":
        cmd = [cmd_name, "container", "ps"]
    elif engine == "apple":
        cmd = [cmd_name, "list"]
    else:
        raise ValueError(f"Invalid engine='{engine}'")
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
            "'%s' did not complete within %d seconds: killing it",
            " ".join(cmd),
            timeout_in_secs,
        )
        process.kill()
        process.wait()
        is_hanging = True
    _LOG.debug("return=%s", is_hanging)
    return is_hanging


def _is_engine_process_running(engine: str) -> bool:
    """
    Check whether `engine`'s background process(es) are still alive.

    :param engine: `"docker"` or `"apple"`
    :return: True if the corresponding process(es) are still running
    """
    if engine == "docker":
        cmd = 'pgrep -f "Docker.app|com.docker.vmnetd"'
    elif engine == "apple":
        cmd = 'pgrep -f "container-apiserver"'
    else:
        raise ValueError(f"Invalid engine='{engine}'")
    rc = hsystem.system(cmd, abort_on_error=False, suppress_output=True)
    is_running = rc == 0
    _LOG.debug("return=%s", is_running)
    return is_running


def _quit_docker_desktop() -> None:
    """
    Ask Docker Desktop to quit gracefully via AppleScript.
    """
    _LOG.info("Quitting Docker Desktop")
    hsystem.system("osascript -e 'quit app \"Docker\"'", abort_on_error=False)


def _stop_apple_container_system() -> None:
    """
    Ask the Apple `container` system services to stop gracefully.
    """
    _LOG.info("Stopping the Apple 'container' system services")
    hsystem.system("container system stop", abort_on_error=False)


def _force_kill_engine(engine: str) -> None:
    """
    Force-kill `engine`'s background process(es) (nuclear option).

    Used when a graceful stop does not stop `engine`, e.g., because it is
    wedged.

    :param engine: `"docker"` or `"apple"`
    """
    _LOG.warning("Force-killing engine '%s' processes", engine)
    if engine == "docker":
        hsystem.system('pkill -9 -f "Docker.app"', abort_on_error=False)
        hsystem.system(
            'sudo pkill -9 -f "com.docker.vmnetd"', abort_on_error=False
        )
    elif engine == "apple":
        hsystem.system(
            'pkill -9 -f "container-apiserver"', abort_on_error=False
        )
    else:
        raise ValueError(f"Invalid engine='{engine}'")


def _shutdown_engine(engine: str, *, poll_interval_in_secs: int) -> None:
    """
    Shut down `engine`, escalating to a force-kill if needed.

    First try a graceful stop (`docker`: AppleScript quit of Docker Desktop;
    `apple`: `container system stop`). If the underlying process(es) are
    still alive afterwards, fall back to killing them directly and poll
    until they are gone.

    :param engine: `"docker"` or `"apple"`
    :param poll_interval_in_secs: number of seconds to sleep between
        polls while waiting for processes to die
    """
    if engine == "docker":
        _quit_docker_desktop()
    elif engine == "apple":
        _stop_apple_container_system()
    else:
        raise ValueError(f"Invalid engine='{engine}'")
    time.sleep(poll_interval_in_secs)
    if _is_engine_process_running(engine):
        _LOG.warning(
            "Engine '%s' did not stop gracefully: using the nuclear option",
            engine,
        )
        _force_kill_engine(engine)
        while _is_engine_process_running(engine):
            time.sleep(poll_interval_in_secs)
    _LOG.info("Engine '%s' is fully shut down", engine)


def _start_engine(engine: str) -> None:
    """
    Start `engine`.

    :param engine: `"docker"` or `"apple"`
    """
    _LOG.info("Starting engine '%s'", engine)
    if engine == "docker":
        hsystem.system("open -a Docker", abort_on_error=False)
    elif engine == "apple":
        hsystem.system("container system start", abort_on_error=False)
    else:
        raise ValueError(f"Invalid engine='{engine}'")


def _restart_engine(engine: str, *, poll_interval_in_secs: int) -> None:
    """
    Restart `engine`.

    Shut `engine` down completely (escalating to a force-kill if a graceful
    stop does not work) and then start it back up.

    :param engine: `"docker"` or `"apple"`
    :param poll_interval_in_secs: number of seconds to sleep between
        polls while waiting for `engine`'s process(es) to die
    """
    _shutdown_engine(engine, poll_interval_in_secs=poll_interval_in_secs)
    _start_engine(engine)


def _wait_for_engine_to_be_ready(
    engine: str, *, poll_interval_in_secs: int
) -> None:
    """
    Poll `engine` until it responds, then log readiness.

    :param engine: `"docker"` or `"apple"`
    :param poll_interval_in_secs: number of seconds to sleep between
        polls
    """
    _LOG.debug(hprint.to_str("engine poll_interval_in_secs"))
    hdocker.set_docker_engine(engine)
    _LOG.info("Waiting for engine '%s' to come back up", engine)
    while not hdocker.is_docker_running():
        time.sleep(poll_interval_in_secs)
    _LOG.info("ready")


def _is_engine_installed(engine: str) -> bool:
    """
    Check whether `engine`'s CLI is installed.

    Logs a warning (not an error) when unavailable, so callers can skip the
    engine instead of crashing.

    :param engine: `"docker"` or `"apple"`
    :return: True if the engine's CLI is installed
    """
    hdocker.set_docker_engine(engine)
    cmd_name = hdocker.get_docker_command()
    is_installed = hsystem.check_exec(cmd_name)
    if not is_installed:
        _LOG.warning(
            "Engine '%s': '%s' CLI is not installed: skipping",
            engine,
            cmd_name,
        )
    return is_installed


def _get_engines(docker_engine: str) -> List[str]:
    """
    Resolve the `--docker_engine` CLI value into a list of engines to
    process.

    :param docker_engine: value of `--docker_engine` (`"docker"`, `"apple"`,
        or `"all"`)
    :return: list of engine names to process, in order
    """
    if docker_engine == "all":
        engines = ["docker", "apple"]
    else:
        engines = [docker_engine]
    return engines


# #############################################################################
# CLI.
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--docker_engine",
        action="store",
        choices=["docker", "apple", "all"],
        default="all",
        help="Container engine(s) to check and restart if needed",
    )
    parser.add_argument(
        "--timeout_in_secs",
        type=int,
        default=5,
        help="Max number of seconds to wait for the engine's list command",
    )
    parser.add_argument(
        "--poll_interval_in_secs",
        type=int,
        default=1,
        help="Number of seconds to wait between readiness polls",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.debug(
        hprint.to_str(
            "args.docker_engine args.timeout_in_secs args.poll_interval_in_secs"
        )
    )
    engines = _get_engines(args.docker_engine)
    for engine in engines:
        if not _is_engine_installed(engine):
            continue
        is_hanging = _is_engine_hanging(
            engine, timeout_in_secs=args.timeout_in_secs
        )
        if is_hanging:
            _restart_engine(
                engine, poll_interval_in_secs=args.poll_interval_in_secs
            )
            _wait_for_engine_to_be_ready(
                engine, poll_interval_in_secs=args.poll_interval_in_secs
            )
        else:
            _LOG.info("Engine '%s' is responsive: nothing to do", engine)


if __name__ == "__main__":
    _main(_parse())
