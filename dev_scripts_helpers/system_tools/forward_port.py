#!/usr/bin/env python3
"""
Port forwarding utility.

Listens on localhost:8888 and forwards traffic to 192.168.64.3:8888.
"""

import socket
import threading
from typing import Tuple

# Import debugging and logging helpers from the helpers package
from helpers.hdbg import _LOG, dassert


def _forward(src: socket.socket, dst_host: str, dst_port: int) -> None:
    """
    Forward data between a source socket and a destination address.

    :param src: Accepted client socket.
    :param dst_host: Destination hostname or IP address.
    :param dst_port: Destination port number.
    """
    # Establish connection to the destination
    dst = socket.socket()
    dst.connect((dst_host, dst_port))

    def _pipe(a: socket.socket, b: socket.socket) -> None:
        """
        Transfer data from socket `a` to socket `b` until EOF.

        :param a: Source socket.
        :param b: Destination socket.
        """
        try:
            while True:
                data = a.recv(4096)
                if not data:
                    break
                b.sendall(data)
        finally:
            a.close()
            b.close()

    # Run bidirectional forwarding in daemon threads
    threading.Thread(target=_pipe, args=(src, dst), daemon=True).start()
    threading.Thread(target=_pipe, args=(dst, src), daemon=True).start()


def _main() -> None:
    """
    Set up the listening socket and handle incoming connections.
    """
    listen_addr: Tuple[str, int] = ("127.0.0.1", 8888)
    target_host: str = "192.168.64.3"
    target_port: int = 8888

    # Validate parameters using dassert from helpers.hdbg
    dassert(isinstance(listen_addr[0], str), "Listen address must be a string")
    dassert(isinstance(listen_addr[1], int), "Listen port must be an integer")
    dassert(isinstance(target_host, str), "Target host must be a string")
    dassert(isinstance(target_port, int), "Target port must be an integer")

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(listen_addr)
    server.listen(10)
    _LOG.info("Forwarding '%s:%d' -> '%s:%d'",
              listen_addr[0], listen_addr[1], target_host, target_port)

    while True:
        conn, _ = server.accept()
        _forward(conn, target_host, target_port)

if __name__ == "__main__":
    _main()
