python3 -c "
import socket, threading
def forward(src, dst_host, dst_port):
    dst = socket.socket()
    dst.connect((dst_host, dst_port))
    def pipe(a, b):
        try:
            while True:
                d = a.recv(4096)
                if not d: break
                b.sendall(d)
        except: pass
        finally: a.close(); b.close()
    threading.Thread(target=pipe, args=(src, dst), daemon=True).start()
    threading.Thread(target=pipe, args=(dst, src), daemon=True).start()

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('127.0.0.1', 8888))
s.listen(10)
print('Forwarding localhost:8888 -> 192.168.64.3:8888')
while True:
    conn, _ = s.accept()
    forward(conn, '192.168.64.3', 8888)
"
