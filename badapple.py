import sys, os, queue, termios, time, tty, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

frame_paths = os.listdir('frames-ascii')
frame_paths.sort()
frames = []
j = 0
for frame_path in frame_paths:
    j += 1
    if j%3: continue
    with open('frames-ascii/'+frame_path) as file:
        frames.append(file.read().strip().replace('\n','<br>'*1+'\n'))

class Handler(BaseHTTPRequestHandler):
    def version_string(self):
        return "Vivian's Python script"

    def _write_chunk(self, text):
        data = text.encode('utf8')
        if not data: return
        self.wfile.write(f"{len(data):X}\r\n".encode("ascii"))
        self.wfile.write(data + b"\r\n")
        self.wfile.flush()

    def do_GET(self):
        print(f"\n» From {self.client_address[0]}")
        print(self.requestline)
        for k, v in self.headers.items():
            print('', k + ': ' + v)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        last_frame = None
        for frame in frames:
            if frame != last_frame:
                self._write_chunk('<dialog open>\n'+frame+'\n</dialog>')
            time.sleep(.1)
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()


assert sys.stdin.isatty()

server = ThreadingHTTPServer(("", 8000), Handler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    server.server_close()

