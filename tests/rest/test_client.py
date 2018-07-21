import pandas as pd
import pytest
import requests


class BasicTestClient(object):

    def setup(self):
        from pybfx import BFXClient
        self.client = BFXClient(key="key", secret="secret")


class TestBFXClient(BasicTestClient):

    def test_can_create_client_instance(self):
        from pybfx import BFXClient
        BFXClient()

    @pytest.mark.parametrize("method", [requests.get, requests.post])
    def test_can_make_requests(self, requests_mock, method):
        url = self.client._url_for("/random_endpoint")
        expected = {"ok": True}
        requests_mock.get(url, json=expected)
        requests_mock.post(url, json=expected)
        results = self.client._handle_request(method, url=url)
        assert results == expected

    @pytest.mark.parametrize("method", [requests.get, requests.post])
    def test_make_request_at_endpoint_that_does_not_return_to_json(self, requests_mock, method):
        from pybfx import BFXException
        url = self.client._url_for("/random_endpoint")
        expected = "gibberish"
        requests_mock.get(url, text=expected)
        requests_mock.post(url, text=expected)
        with pytest.raises(BFXException) as error:
            self.client._handle_request(method, url)
        assert expected in str(error.value)


class TestV1Public(BasicTestClient):

    def test_today(self, requests_mock):
        expected = {'low': '6327.1', 'high': '6711.0', 'volume': '29054.15345665'}
        requests_mock.get(self.client._url_for("/v1/today/BTCUSD"), json=expected)
        assert expected == self.client.today("BTCUSD")

    def test_ticker(self, requests_mock):
        symbol = "btcusd"
        expected = {"ask": "6689.7", "bid": "6689.6", "high": "6771.0", "last_price": "6689.6", "low": "6576.9", "mid": "6689.65", "timestamp": "1531828672.2591913", "volume": "22255.610510320003"}  # noqa E501
        requests_mock.get(self.client._url_for(f"/v1/pubticker/{symbol}"), json=expected)
        assert expected == self.client.ticker(symbol)

    def test_stats(self, requests_mock):
        symbol = "btcusd"
        expected = [{"period": 1, "volume": "22302.52773652"}, {"period": 7, "volume": "132145.49652158"}, {"period": 30, "volume": "651144.20420434"}]  # noqa E501
        requests_mock.get(self.client._url_for(f"/v1/stats/{symbol}"), json=expected)
        assert expected == self.client.stats(symbol)

    def test_symbols(self, requests_mock):
        expected = ["atmbtc", "atmeth", "hotusd", "hotbtc", "hoteth", "dtausd"]
        requests_mock.get(self.client._url_for(f"/v1/symbols"), json=expected)
        assert expected == self.client.symbols()

    def test_symbol_details(self, requests_mock):
        expected = [{"expiration": "NA", "initial_margin": "30.0", "margin": False, "maximum_order_size": "100000.0", "minimum_margin": "15.0", "minimum_order_size": "190.0", "pair": "iqxeos", "price_precision": 5}]  # noqa E501
        requests_mock.get(self.client._url_for("/v1/symbols_details"), json=expected)
        assert expected == self.client.symbols_details()


class TestV1Private(BasicTestClient):

    def test_account_info(self, requests_mock):
        expected = [{"maker_fees": "0.1", "taker_fees": "0.2", "fees": [{ "pairs": "BTC", "maker_fees": "0.1", "taker_fees": "0.2" },{ "pairs": "LTC", "maker_fees": "0.1", "taker_fees": "0.2" }, { "pairs": "ETH", "maker_fees": "0.1", "taker_fees": "0.2" }]}]  # noqa E501
        requests_mock.post(self.client._url_for("/v1/account_infos"), json=expected)
        assert expected == self.client.account_info()

    def test_key_info(self, requests_mock):
        expected = {
            "account": {"read": True, "write": False},
            "history": {"read": True, "write": False},
            "orders": {"read": True, "write": True},
        }
        requests_mock.post(self.client._url_for("/v1/key_info"), json=expected)
        assert expected == self.client.key_info()

    def test_balances(self, requests_mock):
        expected = [
            {"type": "deposit", "currency": "btc", "amount": "0.0", "available": "0.0"},
            {"type": "deposit", "currency": "usd", "amount": "1.0", "available": "1.0"}
        ]
        requests_mock.post(self.client._url_for("/v1/balances"), json=expected)
        assert expected == self.client.balances()


class TestV2Public(BasicTestClient):

    @pytest.mark.parametrize("json_response, result", [([1], True), ([0], False)])
    def test_platform_status(self, requests_mock, json_response, result):
        requests_mock.get(self.client._url_for("/v2/platform/status"), json=json_response)
        assert self.client.platform_status() == result

    def test_tickers_mixed_symbols(self):
        symbols = ["tBTCUSD", "fUSD"]
        with pytest.raises(ValueError) as error:
            self.client.tickers(*symbols)
        assert all(symbol in str(error.value) for symbol in symbols)

    @pytest.mark.parametrize("symbols, expected", [
        (["tBTCUSD"], ["tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9]),   # noqa E501
        (["fUSD"], ["fUSD", 0.00020966, 0.00019301, 30, 4062509.97073771, 0.00017034, 5, 813114.16312721, -3.418e-05, -0.1593, 0.00018034, 231276127.5778418, 0.00021999, 4.9e-07]),  # noqa E501
        (["tBTCUSD", "tBTCEUR"], [
            ["tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9],  # noqa E501
            ["tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9],  # noqa E501
        ]),
    ])
    def test_tickers_df(self, requests_mock, symbols, expected):
        requests_mock.get(self.client._url_for("/v2/tickers?symbols=%s" % ",".join(symbols)), json=expected)
        results = self.client.tickers(*symbols)
        assert isinstance(results, pd.DataFrame)
        assert len(results) == len(symbols)
        assert self.client._tickers_to_df(expected).equals(results)

    def test_tickers_raw(self, requests_mock):
        symbol = "tBTCUSD"
        expected = ["tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9]  # noqa E501
        requests_mock.get(self.client._url_for(f"/v2/tickers?symbols={symbol}"), json=expected)
        results = self.client.tickers(symbol, raw=True)
        assert isinstance(results, list)
        assert results == expected

    def test_candles_raw(self, requests_mock):
        raw = True
        symbol = "tBTCUSD"
        timeframe = "1D"
        json_response = [[100, 300, 400, 450, 270, 10000], [101, 410, 500, 350, 580, 20000]]
        expected = json_response
        url = self.client._url_for(f"/v2/candles/trade:{timeframe}:{symbol}/hist?limit=100&sort=False")
        requests_mock.get(url, json=json_response)
        results = self.client.candles(symbol, timeframe, raw=raw)
        assert len(results) == 2
        assert all(len(item) == 6 for item in results)
        assert expected == results

    def test_candles_dataframe(self, requests_mock):
        raw = False
        symbol = "tBTCUSD"
        timeframe = "1D"
        json_response = [[100, 300, 400, 450, 270, 10000], [101, 410, 500, 350, 580, 20000]]
        expected = self.client._candles_to_df(symbol, json_response)
        url = self.client._url_for(f"/v2/candles/trade:{timeframe}:{symbol}/hist?limit=100&sort=False")
        requests_mock.get(url, json=json_response)
        results = self.client.candles(symbol, timeframe, raw=raw)
        assert len(results) == 2
        assert isinstance(results, pd.DataFrame)
        assert set(results.columns) == {"symbol", "open", "close", "high", "low", "volume"}
        assert results.index.name == "ts"
        assert results.equals(expected)
