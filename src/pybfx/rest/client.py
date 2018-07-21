import base64
import hashlib
import hmac
import json
import logging
import os
import time
from json.decoder import JSONDecodeError

import pandas as pd
import requests
from munch import munchify

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

    def _handle_request(self, method, url, headers=None, data=None, params=None):
        if data and params:
            raise ValueError("You can't specify both `data` and `params`")
        response = method(
            url, params=params, headers=headers, data=data, timeout=self.timeout, verify=True
        )

        try:
            content = response.json()
        except JSONDecodeError:
            content = response.text
            logger.error("Couldn't access: %s", response.url)
            raise BFXException(response.status_code, response.reason, content)
        else:
            if response.status_code == 200:
                return content
            else:
                raise BFXException(response.status_code, response.reason, content)

    def _url_for(self, path):
        return self.base_url + path

    def _get(self, path, params=None):
        url = self._url_for(path)
        return self._handle_request(requests.get, url, params=params)

    def _post_v1(self, path, data=None):
        url = self._url_for(path)
        if data is None:
            data = {}
        data.update(**{
            "nonce": self._get_nonce(),
            "request": path,
        })
        headers = self._get_headers_v1(data)
        return self._handle_request(requests.post, url, headers=headers, data=data)

    # V1 Public Endpoints #

    def today(self, symbol):
        """
        Return day stats about the specified symbol.

        It shows the high, low and volume.

            GET /v1/today/:symbol
            curl "https://api.bitfinex.com/v1/today/btcusd"
            {"low":"550.09","high":"572.2398","volume":"7305.33119836"}

        """
        path = f"/v1/today/{symbol}"
        return munchify(self._get(path))

    def ticker(self, symbol):
        """
        The ticker is a high level overview of the state of the market.

        It shows you the current best bid and ask, as well as the last trade price. It also includes
        information such as daily volume and how much the price has moved over the last day.

            GET /v1/pubticker/:symbol
            curl https://api.bitfinex.com/v1/pubticker/btcusd
            {"ask": "6689.7", "bid": "6689.6", "high": "6771.0", "last_price": "6689.6", "low": "6576.9", "mid": "6689.65", "timestamp": "1531828672.2591913", "volume": "22255.610510320003"}   # noqa E501

        """
        path = f"/v1/pubticker/{symbol}"
        return munchify(self._get(path))

    def stats(self, symbol):
        """
        Various statistics about the requested pair.

            GET /v1/stats/:symbol
            curl https://api.bitfinex.com/v1/stats/btcusd
            [{"period": 1, "volume": "22302.52773652"}, {"period": 7, "volume": "132145.49652158"}, {"period": 30, "volume": "651144.20420434"}]  # noqa E501

        """
        path = f"/v1/stats/{symbol}"
        return munchify(self._get(path))

    def symbols(self):
        """
        Return the list of the available symbols.

            GET /v1/symbols
            curl "https://api.bitfinex.com/v1/symbols"
            ["atmbtc", "atmeth", "hotusd", "hotbtc", "hoteth", "dtausd", ...]

        """
        path = "/v1/symbols"
        return self._get(path)

    def symbols_details(self):
        """
        Return a list of valid symbol IDs and the pair details.

            GET /v1/symbol_details
            curl https://api.bitfinex.com/v1/symbols_details
            [{"expiration": "NA", "initial_margin": "30.0", "margin": False, "maximum_order_size": "100000.0", "minimum_margin": "15.0", "minimum_order_size": "190.0", "pair": "iqxeos", "price_precision": 5}]  # noqa E501

        """
        path = "/v1/symbols_details"
        return munchify(self._get(path))

    # V1 Private Endpoints #

    def account_info(self):
        """
        Return information about your account (trading fees).

            curl -X POST https://api.bitfinex.com/v1/account_infos

        """
        path = "/v1/account_infos"
        return munchify(self._post_v1(path))

    def key_info(self):
        """
        Return the permissions of the key being used to generate this request.

            curl -X POST https://api.bitfinex.com/v1/key_info

        """
        path = "/v1/key_info"
        return self._post_v1(path)

    def balances(self):
        """
        Return the balances of all the coins.

            curl -X POST https://api.bitfinex.com/v1/balances
            [{"type":"deposit", "currency":"btc", "amount":"0.0", "available":"0.0" },{ "type":"deposit", "currency":"usd", "amount":"1.0", "available":"1.0" }]  # noqa E501


        """
        path = "/v1/balances"
        return self._post_v1(path)

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
        return bool(self._get(path)[0])

    def _tickers_validate(self, symbols):
        if not len({s[0] for s in symbols}) == 1:
            msg = "Mixed trading and funding symbols. Please make separate calls: %r"
            raise ValueError(msg % str(symbols))

    def _tickers_to_df(self, results):
        # When we have a single symbol then `results` is a list.
        # When we have multiple symbols, then `results` is a list of lists.
        # In the former case we need to convert results to a list of lists too.
        if isinstance(results[0], str):
            results = [results]
        if results[0][0].startswith("t"):
            df = self._tickers_to_df_trading_pair(results)
        else:
            df = self._tickers_to_df_funding_currency(results)
        df = df.set_index("symbol")
        return df

    def _tickers_to_df_trading_pair(self, results):
        # This is a traiding pair
        columns = [
            'symbol', 'bid', 'bid_size', 'ask', 'ask_size', 'daily_change', 'daily_change_perc',
            'last_price', 'volume', 'high', 'low'
        ]
        df = pd.DataFrame(results, columns=columns)
        df = df.assign(
            base=df.symbol.str[1:4].str.lower(),
            quote=df.symbol.str[4:7].str.lower(),
        )
        df = df[["base", "quote"] + columns]
        return df

    def _tickers_to_df_funding_currency(self, results):
        # This is a funding Currency
        columns = [
            'symbol', 'frr', 'bid', 'bid_size', 'bid_period', 'ask', 'ask_size', 'ask_period',
            'daily_change', 'daily_change_perc', 'last_price', 'volume', 'high', 'low'
        ]
        df = pd.DataFrame(results, columns=columns)
        df = df.assign(base=df.symbol.str.lower()[1:4])
        df = df[["base"] + columns]
        return df

    def tickers(self, *symbols, raw=False):
        """
        Return a high level overview of the state of the market.

        It shows you the current best bid and ask, as well as the last trade price. It also includes
        information such as daily volume and how much the price has moved over the last day.

            GET /v2/tickers?symbols=...
            curl 'https://api.bitfinex.com/v2/tickers?symbols=tBTCUSD,tLTCUSD,fUSD'
            [
                ["tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9],  # noqa E501
                ["fUSD", 0.00020966, 0.00019301, 30, 4062509.97073771, 0.00017034, 5, 813114.16312721, -3.418e-05, -0.1593, 0.00018034, 231276127.5778418, 0.00021999, 4.9e-07]  # noqa E501
            ]

        """
        self._tickers_validate(symbols)
        params = {"symbols": ",".join(symbols)}
        path = "/v2/tickers"
        results = self._get(path, params=params)
        if not raw:
            results = self._tickers_to_df(results)
        return results

    def orderbook(self, symbol, limit_bids=50, limit_asks=50, group=True):
        # curl https://api.bitfinex.com/v:version/book/:symbol
        path = f"/v1/book/{symbol}"
        params = {"limit_bids": limit_bids, "limit_asks": limit_asks, "group": group}
        return self._get(path, params=params)

    def symbol_book(self, symbol, precision="P0", price_points=25):
        path = f"/v2/book/{symbol}/{precision}"
        params = {"asdf": price_points}
        return self._get(path, params=params)

    @staticmethod
    def _candles_to_df(symbol, results):
        df = pd.DataFrame(results, columns=["ts", "open", "close", "high", "low", "volume"])
        df = df.assign(
            symbol=symbol,
            ts=pd.to_datetime(df.ts, unit="ms"),
        )
        df = df.set_index("ts")
        return df

    @staticmethod
    def _candles_validate(symbol, timeframe):
        if not symbol.startswith("t"):
            raise ValueError("Invalid symbol: %s" % symbol)
        valid = {'1m', '5m', '15m', '30m', '1h', '3h', '6h', '12h', '1D', '7D', '14D', '1M'}
        if timeframe not in valid:
            raise ValueError("Invalid timeframe: %s" % timeframe)

    def candles(self, symbol, timeframe, limit=100, start=None, end=None, sort=False, raw=False):
        self._candles_validate(symbol, timeframe)
        path = f"/v2/candles/trade:{timeframe}:{symbol}/hist"
        params = {
            "limit": limit,
            "start": start,
            "end": end,
            "sort": sort,
        }
        results = self._get(path, params=params)
        if not raw:
            results = self._candles_to_df(symbol, results)
        return results


__all__ = [
    "BFXClient",
    "BFXException",
]
