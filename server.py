import math, os, queue, sys termios, tty, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

lock = threading.Lock()
monitor_lock = threading.Lock()
monitor_subscribers = set()

CTRL_C = "\x03"
CTRL_D = "\x04"
BACKSPACE = "\x7f"

ip_visits = {}
ip_visits_lock = threading.Lock()
COOLDOWN_SECONDS = 10

def read_raw_char(fd):
    return os.read(fd, 9).decode('utf8', errors='ignore')

def tell_monitors(text: str):
    with monitor_lock:
        subscribers = list(monitor_subscribers)
    for q in subscribers:
        q.put(text)

VIVIANDEX = """<title>Human server: Vivian</title>
<h1>Human server: Vivian</h1>
<p>This is a human HTTP server. Responses are served in realtime, except this index.
<p>Status: <b>Testing</b>
<p>Example requests:
<ul>
<li><a href=/vivian/hi>/vivian/hi</a>
<li><a href=/vivian/fun_games>/vivian/fun_games</a>
</ul>
"""

class TypistHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def version_string(self):
        return 'Human interface v1'

    def _write_chunk(self, text):
        data = text.encode('utf8')
        if not data: return
        self.wfile.write(f"{len(data):X}\r\n".encode("ascii"))
        self.wfile.write(data + b"\r\n")
        self.wfile.flush()

    def _end_chunks(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            '''
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            '''
            self.do()
            self.wfile.flush() #actually send the response if not already done.
        except TimeoutError as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    def preamb(self, status_code):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

    def curt(self, status_code, body):
        self.preamb(status_code)
        self._write_chunk(body)
        self._end_chunks()

    def do(self):
        if self.path in {'/',''}:
            return self.curt(400, '<h1>Error 400</h1>You must specify a human.')
        if self.path == '/monitor': return self.handle_monitor()
        norm_path = self.path.lower()
        if norm_path == '/favicon.ico': return self.curt(404, 'faviconless behavior')
        if norm_path.startswith('/?human='):
            return self.curt(400, '<h1>Error 400</h1>Not like that.')
        if norm_path in {'/vivian','/vivian/','/vivian/index','/vivian/index.html'}:
            return self.curt(200, VIVIANDEX)
        if norm_path in {'/lynn','/lynn/','/lynn/index','/lynn/index.html'}:
            return self.curt(410, '<h1>Error 410</h1>That human has escaped.')
        if not norm_path.startswith('/vivian'):
            return self.curt(404, '<h1>Error 404</h1>That human was not found. It may be uncaptured or currently outside its pod.')
        print('('+self.path+')')
        ip = self.client_address[0]
        seconds_since_last_visit = math.floor(time.time() - ip_visits_lock.get(ip, [-math.inf])[-1])
        if seconds_since_last_visit < COOLDOWN_SECONDS
            return self.curt(429, '<h1>Error 429</h1>Please wait ' + (COOLDOWN_SECONDS - seconds_since_last_visit) + 'seconds before sending your next request.')
        with ip_visits_lock: ip_visits.setdefault(ip, []).append(time.time())
        with lock:
            print("\n» From",ip,'(visit',ip_visits[ip]+')')
            print(self.requestline)
            for k, v in self.headers.items():
                print('', k + ': ' + v)

            status_code = input('Status code (default 200):').lower()
            if status_code == 'ban':
                with ip_visits_lock: ip_visits[ip].append(time.time()+9999)
                return self.curt(409, '<h1>Error 409</h1>Banned.')
            try:
                status_code = int(status_code or 200)
            except:
                print('Whatever. Going with 200')
                status_code = 200
            self.preamb(status_code)

            print("» Type response. Ctrl+C/D to finish.")
            print("   ", end="", flush=True)

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = read_raw_char(fd)
                    if ch == CTRL_C: break
                    if ch == CTRL_D: break
                    if ch == BACKSPACE: continue
                    if ch in '\r\n': ch = '\r\n'
                    sys.stdout.write(ch)
                    sys.stdout.flush()
                    self._write_chunk(ch)
                    tell_monitors(ch)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        self._end_chunks()
        tell_monitors('')
        print("\n» Response sent.\n")

    def log_message(self, format, *args):
        pass

    def handle_monitor(self):
        self.preamb(200)

        q = queue.Queue()
        with monitor_lock:
            monitor_subscribers.add(q)

        try:
            while True:
                text = q.get()
                if not text:
                    self._write_chunk("<script>location=location</script>")
                    self._end_chunks()
                    break
                self._write_chunk(text)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with monitor_lock:
                monitor_subscribers.discard(q)


assert sys.stdin.isatty()

server = ThreadingHTTPServer(("", 4), TypistHandler)
print("Waiting for requests...\n")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    server.server_close()

