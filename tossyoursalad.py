import sys, os, queue, termios, time, tty, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class SaladHandler(BaseHTTPRequestHandler):
    def version_string(self):
        return 'Toss Your Salad'

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
        self._write_chunk('<h1>simple fucking flips if you dont give my BUP boy some proper adhesive i will take a bullet')
        time.sleep(8)
        self._write_chunk(' train to your house and toss your salad')
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()


assert sys.stdin.isatty()

server = ThreadingHTTPServer(("", 8000), SaladHandler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down.")
finally:
    server.server_close()

