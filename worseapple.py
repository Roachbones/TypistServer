import sys, os, queue, termios, time, tty, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

frame_paths = os.listdir('frames-ascii')
frame_paths.sort()
frames = []
j = 0

I = " ͕"[-1]
X = " ͚"[-1]
HOOK = "a"
DASH = "𒐫"
DASH = "﷽"
DASH = "𒐪"
DASH = "aaaaaaaaa"
diacriticism = {"I":I,"X":X}

for frame_path in frame_paths:
    j += 1
    if j%3: continue
    hangers = []
    with open('frames-ascii/'+frame_path) as file:
        flines = file.read().strip().split('\n')
        hangers = [HOOK] * len(flines[0])
        for fline in flines:
            for n, c in enumerate(fline):
                hangers[n] += diacriticism[c]
        frames.append(DASH * 30 + ''.join(hangers))

#frames[0] = "‮"+frames[0]

#print(''.join(frames))

#e()

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
        if self.path=='/favicon.ico': return self.send_error(404)
        print(f"\n» From {self.client_address[0]}")
        print(self.requestline)
        for k, v in self.headers.items():
            print('', k + ': ' + v)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        last_frame = None
        self._write_chunk("This page has zero HTML tags. BADAPPLE‮")
        for frame in frames:
            if frame != last_frame:
                self._write_chunk(frame)
            time.sleep(.1/2)
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

