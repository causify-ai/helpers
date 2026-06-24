#!/bin/bash
# """
# Forward a local port to an Apple container via the bridge100 interface.
#
# Apple's container tool (container run -p) has a bug in v1.0.0 where port
# forwarding accepts TCP connections but resets the return path. However, the
# host can reach containers directly via the vmnet bridge100 interface.
#
# This script creates a Python TCP forwarder on the host that relays
# localhost:<host_port> to <container_ip>:<container_port> through the bridge.
#
# Usage:
#   # After docker_jupyter.sh has started the container:
#   > ./docker_jupyter_port_forward.sh <container_name> [host_port] [container_port]
#
# Examples:
#   > ./docker_jupyter_port_forward.sh umd_project_l12_reinforcement_learning.jupyter
#   > ./docker_jupyter_port_forward.sh my_container 8888 8888
#
# The script runs in the foreground. Press Ctrl+C to stop forwarding.
# """

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
source "$SCRIPT_DIR/../thin_client/thin_client_utils.sh"

OLD_TMUX_TITLE=$(tmux_rename_on_entry "tunnel" || true)

# ---------------------------------------------------------------------------
# Parse arguments.
# ---------------------------------------------------------------------------
CONTAINER_NAME=${1:-}
HOST_PORT=${2:-8888}
CONTAINER_PORT=${3:-8888}

if [[ -z "$CONTAINER_NAME" ]]; then
    echo "Usage: $0 <container_name> [host_port] [container_port]"
    echo ""
    echo "Example: $0 umd_project_l12_reinforcement_learning.jupyter 8888 8888"
    exit 1
fi

# ---------------------------------------------------------------------------
# Get the container's bridge100 IP.
# ---------------------------------------------------------------------------
CONTAINER_IP=$(container exec "$CONTAINER_NAME" hostname -I 2>/dev/null | awk '{print $1}')
if [[ -z "$CONTAINER_IP" ]]; then
    echo "ERROR: Failed to get container IP for '$CONTAINER_NAME'."
    echo "Is the container running? Check with: container list"
    exit 1
fi

echo "Container: $CONTAINER_NAME"
echo "Bridge IP: $CONTAINER_IP"
echo "Forwarding localhost:$HOST_PORT -> $CONTAINER_IP:$CONTAINER_PORT"
echo "Press Ctrl+C to stop."
echo ""

# ---------------------------------------------------------------------------
# Start the Python TCP forwarder.
# ---------------------------------------------------------------------------
python3 -c "
import socketserver, threading, socket, sys

class _Forwarder(socketserver.BaseRequestHandler):
    def handle(self):
        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.settimeout(60)
        try:
            upstream.connect(('$CONTAINER_IP', $CONTAINER_PORT))
            thr = threading.Thread(target=_pipe, args=(self.request, upstream), daemon=True)
            thr.start()
            _pipe(upstream, self.request)
        except Exception as e:
            sys.stderr.write(f'Forward error: {e}\n')
            sys.stderr.flush()

def _pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except:
                pass

s = socketserver.ThreadingTCPServer(('0.0.0.0', $HOST_PORT), _Forwarder, bind_and_activate=False)
s.allow_reuse_address = True
s.server_bind()
s.server_activate()
host, port = s.server_address
sys.stderr.write(f'Forwarding :{port} -> $CONTAINER_IP:$CONTAINER_PORT\n')
sys.stderr.write(f'Open http://localhost:{port} in your browser\n')
sys.stderr.flush()
s.serve_forever()
"

# Restore the TMUX.
tmux_restore_on_exit "$OLD_TMUX_TITLE"