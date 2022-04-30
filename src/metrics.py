from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import logging
import copy


class Metrics:
    def __init__(self, config):
        self._live_metrics = {}
        self._metrics = {}

        if config.openmetrics_enable:
            logging.info(
                f"Starting openmetrics endpoint at port {config.openmetrics_port}")
            daemon = threading.Thread(name='daemon_server',
                                      target=self._start_http_server,
                                      args=(config.openmetrics_port,))

            # Set as a daemon so it will be killed once the main thread is dead.
            daemon.setDaemon(True)
            daemon.start()

    def init_metrics(self):
        # General metrics
        self._init_single_metric(
            'targets', 'gauge', 'Count of configured/detected databases')
        self._init_single_metric(
            'successful_targets', 'gauge', 'Count of successfully backuped databases')
        self._init_single_metric(
            'cycle_duration', 'gauge', 'Duration of whole backup cycle in milliseconds')

        # Database specific
        self._init_multi_metric('backup_status', 'gauge',
                                'Status of latest backup')
        self._init_multi_metric('backup_duration', 'gauge',
                                'Time needed for backup in milliseconds')
        self._init_multi_metric(
            'backup_dump_raw_size', 'gauge', 'Size of dump before compression/encryption')
        self._init_multi_metric('backup_dump_size', 'gauge',
                                'Size of dump after compression/encryption')
        self._init_multi_metric('backup_retention_checked_files', 'gauge',
                                'Count of dumps check when applying retention policy')
        self._init_multi_metric('backup_retention_kept_files', 'gauge',
                                'Count of dumps kept after retention policy is applied')

    def _init_single_metric(self, name, type, help):
        self._metrics[name] = {
            'type': type,
            'help': help,
            'value': None
        }

    def _init_multi_metric(self, name, type, help):
        self._metrics[name] = {
            'type': type,
            'help': help,
            'values': []
        }

    def set_single_value(self, name, value):
        self._metrics[name]['value'] = value

    def add_multi_value(self, name, labels, value):
        pair = {
            'labels': labels,
            'value': value
        }
        self._metrics[name]['values'].append(pair)

    def flush_metrics(self):
        self._live_metrics = copy.deepcopy(self._metrics)

    def _start_http_server(self, port):
        metrics = self

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                message = ""
                for metric in metrics._live_metrics.items():
                    message += f"# HELP {metric[0]} {metric[1]['help']}\n# TYPE {metric[0]} {metric[1]['type']}\n"
                    if "value" in metric[1] and metric[1]['value'] is not None:
                        message += f"{metric[0]} {metric[1]['value']}\n"
                    elif "values" in metric[1]:
                        for entry in metric[1]['values']:
                            label_string = ','.join(
                                map(lambda lbl: f'{lbl[0]}="{lbl[1]}"', entry['labels'].items()))
                            message += f"{metric[0]}{{{label_string}}} {entry['value']}\n"

                self.protocol_version = "HTTP/1.1"
                self.send_response(200)
                self.send_header("Content-Length", len(message))
                self.end_headers()
                self.wfile.write(bytes(message, "utf8"))
                return

        with HTTPServer(('', port), RequestHandler) as httpd:
            httpd.serve_forever()
