import base64
import hashlib
import hmac
import json
import logging
import os
import time
from json.decoder import JSONDecodeError

import requests

logger = logging.getLogger(__name__)


class BFXException(Exception):
    pass


class BFXClient(object):
    """
    Client for the bitfinex.com API (both v1 and v2).

    See https://www.bitfinex.com/pages/api for API documentation.
    """

    def __init__(self, key=None, secret=None, nonce_multiplier=1.0, timeout=5):
        self.key = key or os.environ.get("BITFINEX_KEY")
        self.secret = secret or os.environ.get("BITFINEX_SECRET")
        self.nonce_multiplier = float(nonce_multiplier)
        self.timeout = timeout
        self.base_url = "https://api.bitfinex.com"

    def _get_nonce(self):
        """Returns a nonce used in authentication.
        Nonce must be an increasing number, if the API key has been used
        earlier or other frameworks that have used higher numbers you might
        need to increase the nonce_multiplier."""
        return str(float(time.time()) * self.nonce_multiplier)

    def _get_headers_v1(self, payload):
        json_payload = json.dumps(payload)
        data = base64.standard_b64encode(json_payload.encode('utf8'))
        hm = hmac.new(self.secret.encode('utf8'), data, hashlib.sha384)
        signature = hm.hexdigest()
        return {"X-BFX-APIKEY": self.key, "X-BFX-SIGNATURE": signature, "X-BFX-PAYLOAD": data}

    def _handle_request(self, method, url, data=None, params=None):
        if data and params:
            raise ValueError("You can't specify both `data` and `params`")
        response = method(url, params=params, data=data, timeout=self.timeout, verify=True)
        if response.status_code == 200:
            return response.json()
        else:
            try:
                content = response.json()
            except JSONDecodeError:
                content = response.text
            logger.exception("Couldn't access: %s", response.url)
            raise BFXException(response.status_code, response.reason, content)

    def _url_for(self, path):
        return self.base_url + path

    def _get(self, url, params=None):
        return self._handle_request(requests.get, url, params=params)

    def _post(self, url, payload=None):
        return self._handle_request(requests.post, url, payload=payload)

    # V1 Public Endpoints #

    def today(self, symbol):
        """
        GET /v1/today/:symbol

            curl "https://api.bitfinex.com/v1/today/btcusd"

            {"low":"550.09","high":"572.2398","volume":"7305.33119836"}
        """
        path = f"/v1/today/{symbol}"
        return self._get(self._url_for(path))

    # V2 Public Endpoints #

    def platform_status(self):
        """
        Get the current status of the platform.

        Maintenance periods last for just few minutes and might be necessary from time to time
        during upgrades of core components of our infrastructure. Even if rare it is important to
        have a way to notify users. For a real-time notification we suggest to use websockets and
        listen to events 20060/20061

            curl "https://api.bitfinex.com/v2/platform/status"
            [1]

        Returns
        -------
        status: bool
            True if the platform is operative, False otherwise.

        """
        # curl https://api.bitfinex.com/v2/platform/status
        path = "/v2/platform/status"
        return bool(self._get(self._url_for(path))[0])


__all__ = [
    "BFXClient",
]
