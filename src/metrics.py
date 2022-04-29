from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class Metrics:
    def __init__(self):
        self.total_targets = 0
        self.successful_targets = 0
        pass

    def start_server(self):
        port = 8000
        daemon = threading.Thread(name='daemon_server',
                                  target=self._start_http_server,
                                  args=(port,))

        # Set as a daemon so it will be killed once the main thread is dead.
        daemon.setDaemon(True)
        daemon.start()

    def _start_http_server(self, port):
        metrics = self

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                message = ""
                message += self.simple_metric("total_targets",
                                              "gauge", "help text", metrics.total_targets)
                message += self.simple_metric("successful_targets",
                                              "gauge", "help text", metrics.successful_targets)

                self.protocol_version = "HTTP/1.1"
                self.send_response(200)
                self.send_header("Content-Length", len(message))
                self.end_headers()

                self.wfile.write(bytes(message, "utf8"))
                return

            def simple_metric(self, name, type, help, value):
                return f"# HELP {name} {help}\n# TYPE {name} {type}\n{name} {value}\n"

        with HTTPServer(('', port), RequestHandler) as httpd:
            httpd.serve_forever()
