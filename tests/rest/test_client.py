import pytest

from pybfx import TradingPairData, FundingCurrencyData


class BasicTestClient(object):

    def setup(self):
        from pybfx import BFXClient
        self.client = BFXClient()


class TestBFXClient(BasicTestClient):

    def test_can_create_client_instance(self):
        from pybfx import BFXClient
        client = BFXClient()  # noqa F481


class TestV1Public(BasicTestClient):

    def test_today(self, requests_mock):
        expected = {'low': '6327.1', 'high': '6711.0', 'volume': '29054.15345665'}
        requests_mock.get(self.client._url_for("/v1/today/BTCUSD"), json=expected)
        assert expected == self.client.today("BTCUSD")

    def test_ticker(self, requests_mock):
        symbol = "btcusd"
        expected = {"ask": "6689.7", "bid": "6689.6", "high": "6771.0", "last_price": "6689.6", "low": "6576.9", "mid": "6689.65", "timestamp": "1531828672.2591913", "volume": "22255.610510320003"}
        requests_mock.get(self.client._url_for(f"/v1/pubticker/{symbol}"), json=expected)
        assert expected == self.client.ticker(symbol)

    def test_stats(self, requests_mock):
        symbol = "btcusd"
        expected = [{"period": 1, "volume": "22302.52773652"}, {"period": 7, "volume": "132145.49652158"}, {"period": 30, "volume": "651144.20420434"}]
        requests_mock.get(self.client._url_for(f"/v1/stats/{symbol}"), json=expected)
        assert expected == self.client.stats(symbol)

    def test_symbols(self, requests_mock):
        expected = ["atmbtc", "atmeth", "hotusd", "hotbtc", "hoteth", "dtausd"]
        requests_mock.get(self.client._url_for(f"/v1/symbols"), json=expected)
        assert expected == self.client.symbols()

    def test_symbol_details(self, requests_mock):
        expected = [{"expiration": "NA", "initial_margin": "30.0", "margin": False, "maximum_order_size": "100000.0", "minimum_margin": "15.0", "minimum_order_size": "190.0", "pair": "iqxeos", "price_precision": 5}]
        requests_mock.get(self.client._url_for("/v1/symbol_details"), json=expected)
        assert expected == self.client.symbol_details()


class TestV2Public(BasicTestClient):

    @pytest.mark.parametrize("json_response, result", [([1], True), ([0], False)])
    def test_platform_status(self, requests_mock, json_response, result):
        requests_mock.get(self.client._url_for("/v2/platform/status"), json=json_response)
        assert self.client.platform_status() == result

    @pytest.mark.parametrize("symbols, expected", [
        (["tBTCUSD"], [TradingPairData("tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9)]),
        (["fUSD"], [FundingCurrencyData("fUSD", 0.00020966, 0.00019301, 30, 4062509.97073771, 0.00017034, 5, 813114.16312721, -3.418e-05, -0.1593, 0.00018034, 231276127.5778418, 0.00021999, 4.9e-07)]),
        (["tBTCUSD", "fUSD"], [
            TradingPairData("tBTCUSD", 6702.2, 82.42873442, 6702.3, 146.14652325, 82.2, 0.0124, 6702.3, 22520.92767376, 6771, 6576.9),
            FundingCurrencyData("fUSD", 0.00020966, 0.00019301, 30, 4062509.97073771, 0.00017034, 5, 813114.16312721, -3.418e-05, -0.1593, 0.00018034, 231276127.5778418, 0.00021999, 4.9e-07),
        ])
    ])
    def test_tickers(self, requests_mock, symbols, expected):
        requests_mock.get(self.client._url_for("/v2/tickers?symbols=%s" % ",".join(symbols)), json=expected)
        results = self.client.tickers(*symbols)
        assert all(isinstance(r, (TradingPairData, FundingCurrencyData)) for r in results)
        assert expected == results
