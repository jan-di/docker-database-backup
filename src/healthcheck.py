import logging
import requests


class Healthcheck:
    def __init__(self, config):
        self.healthchecks_io_url = config.healthchecks_io_url

    def start(self, text):
        logging.debug("Healthcheck: Start")
        self._healthchecks_io_request('/start', text)

    def success(self, text):
        logging.debug("Healthcheck: Success")
        self._healthchecks_io_request('', text)

    def fail(self, text):
        logging.debug("Healthcheck: Fail")
        self._healthchecks_io_request('/fail', text)

    def _healthchecks_io_request(self, path, text=None):
        if self.healthchecks_io_url is not None:
            url = f"{self.healthchecks_io_url}{path}"
            logging.debug(f"Ping Healtchecks.io (URL: {url}")

            try:
                requests.post(url, data=text, timeout=5)
            except requests.RequestException as e:
                logging.error(
                    f"Failed to ping Healthchecks.io. Error Output: {e}")
