import sys, os, queue, termios, tty, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

lock = threading.Lock()
monitor_lock = threading.Lock()
monitor_subscribers = set()

CTRL_C = "\x03"
CTRL_D = "\x04"
BACKSPACE = "\x7f"

def read_raw_char(fd):
    return os.read(fd, 1).decode('utf8', errors='ignore')

def tell_monitors(text: str):
    with monitor_lock:
        subscribers = list(monitor_subscribers)
    for q in subscribers:
        q.put(text)


class TypistHandler(BaseHTTPRequestHandler):
    def version_string(self):
        return 'Vivian'

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

    def do(self):
        if self.path == '/favicon.ico':
            self.send_error(404)
            return
        if self.path == '/monitor':
            return self.handle_monitor()

        with lock:
            print(f"\n» From {self.client_address[0]}")
            print(self.requestline)
            for k, v in self.headers.items():
                print('', k + ': ' + v)

            status_code = input('Status code (default 200):')
            try:
                status_code = int(status_code or 200)
            except:
                print('whatever. going with 200')
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

server = ThreadingHTTPServer(("localhost", 8000), TypistHandler)
print("Typist server running on http://localhost:8000")
print("Waiting for requests...\n")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    server.server_close()

