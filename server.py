import sys, os, termios, tty, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

lock = threading.Lock()

CTRL_C = "\x03"
CTRL_D = "\x04"
BACKSPACE = "\x7f"

def read_raw_char(fd):
    return os.read(fd, 1).decode('utf8', errors='ignore')

class TypistHandler(BaseHTTPRequestHandler):
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
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
        except TimeoutError as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    def do_GET(self):
        self.do()

    def do_POST(self):
        self.do()

    def do(self):
        self.send_response(200) # todo
        self.send_header("Content-Type", "text/plain; charset=utf-8") # todo
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        with lock:
            print(f"\n» {self.command} {self.path} from {self.client_address[0]}")
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
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        self._end_chunks()
        print(">> Response sent.\n")

    def log_message(self, format, *args):
        pass

assert sys.stdin.isatty()

server = ThreadingHTTPServer(("localhost", 8000), TypistHandler)
print("Typist server running on http://localhost:8000")
print("Waiting for requests... (Ctrl+C here to quit)\n")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    server.server_close()

