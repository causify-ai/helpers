#!/usr/bin/env python

"""
Forward a local TCP port to a running container via the bridge100 interface.

Apple's container tool (`container run -p`) has a bug in v1.0.0 where port
forwarding accepts TCP connections but resets the return path. However, the
host can reach containers directly via the vmnet `bridge100` interface. This
script looks up the bridge IP of a running container, then starts a threaded
TCP forwarder on the host that relays `localhost:<host_port>` to
`<container_ip>:<container_port>` through the bridge. On macOS it also opens
the forwarded URL in the browser once the forwarder is up. Runs in the
foreground until interrupted with Ctrl+C.

# Usage Example

- After `docker_jupyter.sh` has started the container, forward its Jupyter
  port to localhost:
> docker_jupyter_port_forward.py umd_project_l12_reinforcement_learning.jupyter

- Forward a specific host/container port pair:
> docker_jupyter_port_forward.py my_container 8888 8888
"""

import argparse
import logging
import socket
import socketserver
import threading
import time
from typing import List, Type

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hsystem as hsystem
import helpers.htmux as htmux

_LOG = logging.getLogger(__name__)

# #############################################################################


def _get_pids_listening_on_port(host_port: int) -> List[int]:
    """
    Find the PIDs of processes listening on `host_port`.

    :param host_port: local TCP port to inspect
    :return: list of PIDs currently listening on `host_port`
    """
    cmd = f"lsof -nP -iTCP:{host_port} -sTCP:LISTEN -t"
    _, output = hsystem.system_to_string(cmd, abort_on_error=False)
    pids = [int(pid) for pid in output.split()]
    return pids


def _free_host_port(host_port: int) -> None:
    """
    Kill any stale process already bound to `host_port`.

    This forwarder is the only process meant to bind `host_port` on the
    host. If a previous forwarder was not shut down cleanly (e.g., the
    terminal or tmux pane was closed instead of pressing Ctrl+C), it keeps
    holding the port and the next run fails to bind with `Address already
    in use`. Free the port proactively instead of failing.

    :param host_port: local port to free before binding
    """
    pids = _get_pids_listening_on_port(host_port)
    if not pids:
        return
    for pid in pids:
        _LOG.warning(
            "Killing stale process holding port %s (PID %s)", host_port, pid
        )
        hsystem.system(f"kill {pid}", abort_on_error=False)
    time.sleep(1)
    # Escalate to SIGKILL for anything still alive.
    for pid in _get_pids_listening_on_port(host_port):
        _LOG.warning("PID %s still alive, sending SIGKILL", pid)
        hsystem.system(f"kill -9 {pid}", abort_on_error=False)
        time.sleep(0.5)


def _pipe(src: socket.socket, dst: socket.socket) -> None:
    """
    Relay data from `src` to `dst` until the connection closes.

    :param src: socket to read data from
    :param dst: socket to write data to
    """
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for sock in (src, dst):
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def _get_forwarder_handler_class(
    container_ip: str, container_port: int
) -> Type[socketserver.BaseRequestHandler]:
    """
    Build a request handler that forwards each connection to a container.

    :param container_ip: IP address of the container to forward to
    :param container_port: port of the container to forward to
    :return: `socketserver.BaseRequestHandler` subclass that relays every
        accepted connection to `container_ip:container_port`
    """

    class _Forwarder(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream.settimeout(60)
            try:
                upstream.connect((container_ip, container_port))
                thread = threading.Thread(
                    target=_pipe, args=(self.request, upstream), daemon=True
                )
                thread.start()
                _pipe(upstream, self.request)
            except OSError as e:
                _LOG.error("Forward error: %s", e)

    return _Forwarder


def _get_container_ip(container_name: str) -> str:
    """
    Look up the bridge100 IP address of a running container.

    :param container_name: name of the running container (as reported by
        `container list`)
    :return: container's bridge IP address
    """
    cmd = f"container exec {container_name} hostname -I"
    rc, output = hsystem.system_to_string(cmd, abort_on_error=False)
    hdbg.dassert_eq(
        rc,
        0,
        msg=f"Failed to get container IP for '{container_name}'. "
        "Is the container running? Check with: container list",
    )
    container_ip = output.split()[0]
    return container_ip


def _open_browser_when_up(host_port: int) -> None:
    """
    Open the forwarded URL in the default browser, macOS only.

    Meant to run in a background thread so it does not delay the forwarder from
    starting.

    :param host_port: local port the forwarder listens on
    """
    if hsystem.get_os_name() != "Darwin":
        return
    # Give the forwarder a moment to start listening before opening.
    time.sleep(1)
    url = f"http://localhost:{host_port}"
    hsystem.system(f"open {url}", abort_on_error=False)


def _run_forwarder(
    container_name: str, host_port: int, container_port: int
) -> None:
    """
    Look up the container's bridge IP and run the TCP forwarder.

    :param container_name: name of the running container to forward to
    :param host_port: local port to listen on
    :param container_port: container port to forward to
    """
    container_ip = _get_container_ip(container_name)
    _LOG.info("Container: %s", container_name)
    _LOG.info("Bridge IP: %s", container_ip)
    _LOG.info(
        "Forwarding localhost:%s -> %s:%s",
        host_port,
        container_ip,
        container_port,
    )
    _LOG.info("Press Ctrl+C to stop.")
    # Open the forwarded URL once the forwarder is up (no-op outside macOS).
    threading.Thread(
        target=_open_browser_when_up, args=(host_port,), daemon=True
    ).start()
    _free_host_port(host_port)
    handler_class = _get_forwarder_handler_class(container_ip, container_port)
    server = socketserver.ThreadingTCPServer(
        ("0.0.0.0", host_port), handler_class, bind_and_activate=False
    )
    server.allow_reuse_address = True
    server.server_bind()
    server.server_activate()
    server.serve_forever()


# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "container_name",
        help="Name of the running container to forward to",
    )
    parser.add_argument(
        "host_port",
        nargs="?",
        type=int,
        default=8888,
        help="Local port to listen on",
    )
    parser.add_argument(
        "container_port",
        nargs="?",
        type=int,
        default=8888,
        help="Container port to forward to",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    with htmux.window_name("tunnel"):
        try:
            _run_forwarder(
                args.container_name, args.host_port, args.container_port
            )
        except KeyboardInterrupt:
            _LOG.info("Stopping forwarder.")


if __name__ == "__main__":
    _main(_parse())
