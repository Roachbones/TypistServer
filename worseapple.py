import sys, os, queue, termios, time, tty, threading
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

frames = []
j = 0

I = " ͕"[-1]
X = " ͚"[-1]
HOOK = "„"
DASH = "𒐫"
DASH = "﷽"
DASH = "𒐪"
DASH = "„"*9
diacriticism = {"I":I,"X":X}

for frame_path in sorted(os.listdir('frames-ascii-2')):
    j += 1
    if j%3: continue
    hangers = []
    with open('frames-ascii-2/'+frame_path) as file:
        flines = file.read().strip().split('\n')
        hangers = [HOOK] * len(flines[0])
        for fline in flines:
            for n, c in enumerate(fline):
                hangers[n] += diacriticism[c]
        frames.append(DASH * 30 + ''.join(hangers))

FRAMES_WORSE = frames

frames = []
j = 0
for frame_path in sorted(os.listdir('frames-ascii')):
    j += 1
    if j%3: continue
    with open('frames-ascii/'+frame_path) as file:
        frames.append(file.read().strip().replace('\n','<br>'*1+'\n'))

FRAMES_DIALOG = frames

cΔts = []

actpaths = os.listdir('performance/acts')
actpaths.sort()
for act in actpaths:
    with open('performance/acts/'+act) as file:
        if act != 'actO': continue
        for line in file:
            cΔts.append(json.loads(line))

#frames[0] = "‮"+frames[0]

#print(''.join(frames))

#e()

THANKS = 'Thanks for watching. Read how it works at /explainer'

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def version_string(self):
        return "Vivian's Python script"

    def write_chunk(self, text):
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
        if self.path == '/explainer': return self.explainer()
        if self.path == '/dialog': return self.dialogstyle()
        if self.path == '/zero': return self.zerostyle()
        if self.path in ('/', '/index'): return self.index()
        if self.path == '/favicon.ico':
            with open('badapple.ico', 'rb') as file: b = file.read()
            self.send_response(200)
            self.send_header('Content-Type', 'image/x-icon')
            self.send_header('Content-Length', len(b))
            self.end_headers()
            self.wfile.write(b)
            return self.wfile.flush()
        self.zerostyle()

    def preamb(self, status_code):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def end_chunks(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def curt(self, status_code, body):
        self.preamb(status_code)
        self.write_chunk(body)
        self.end_chunks()

    def index(self):
        s = """
This site <a href="https://en.wikipedia.org/wiki/Touhou_Project#Music:~:text=staple%20in%20the%20demoscene%20and%20retrocomputing%20communities">demos</a> <a href="https://www.youtube.com/watch?v=FtutLA63Cp8"><i>Bad Apple</i></a> with no JS, no CSS, and an impressively minimal subset of HTML. See:
<ul>
<li><a href=/dialog>No JS, no CSS, & no HTML tags except &lt;dialog open&gt; & &lt;br&gt;</a>. Even works over curl.
<li><a href=/zero>No JS, no CSS, & no HTML tags at all!</a>
<li><s>Explainer</s> WIP
"""
        self.curt(200, s)

    def explainer(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for cΔt in cΔts:
            c, Δt = cΔt[:2]
            time.sleep(Δt * 0.05)
            self.write_chunk(c)
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def zerostyle(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        last_frame = None
        self.write_chunk("This page has zero HTML tags. (View the source!) ↘‮")
        for frame in FRAMES_WORSE:
            if frame != last_frame:
                self.write_chunk(frame)
            time.sleep((.1 / 3) * 3)
        self.write_chunk(' ' + THANKS[::-1] + '⠀' * 12)
        self.end_chunks()

    def dialogstyle(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        last_frame = None
        self.write_chunk('This page uses no JS, no CSS, and no HTML tags except &lt;dialog open&gt; & &lt;br&gt;.<br><br>')
        for frame in FRAMES_DIALOG:
            if frame != last_frame:
                self.write_chunk('<dialog open>\n'+frame+'\n</dialog>')
            time.sleep(.1)
        self.write_chunk('\n' + '<br>'*12 + '<dialog open>' + THANKS)
        self.end_chunks()


assert sys.stdin.isatty()

server = ThreadingHTTPServer(("", 80), Handler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    server.server_close()

