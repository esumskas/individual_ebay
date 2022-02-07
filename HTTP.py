import requests
import logging
from config import load_config, load_credentials
from time import sleep

cfg = load_config()
creds = load_credentials()

log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)
console = logging.StreamHandler()
log.addHandler(console)

class HTTP:
    def __init__(self):
        self.s = requests.Session()

    def request(self, method, address, data=None):
        retries = 0
        while retries < cfg['request_retry_count']:
            try:
                if method == "GET" or method == "get":
                    r = self.s.get(address,
                                   headers={'User-agent': cfg['user_agent'],
                                            'Accept-Language': 'en-US,en;q=0.9'})
                    return r
                elif method == "POST" or method == "post":
                    if data is not None:
                        r = self.s.post(address,
                                        headers={'User-agent': cfg['user_agent'],
                                                 'Accept-Language': 'en-US,en;q=0.9'},
                                        data=data)
                        return r
                    else:
                        r = self.s.post(address,
                                        headers={'User-agent': cfg['user_agent'],
                                                 'Accept-Language': 'en-US,en;q=0.9'})
                        return r
                else:
                    log.error("Error, method not recognized.")
            except requests.exceptions.ConnectionError:
                log.error("Got ConnectionError while making request, retrying.")
                sleep(1)
        raise Exception("Retry count exceeded while making request, exiting.")
