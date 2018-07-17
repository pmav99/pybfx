import pytest


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


class TestV2Public(BasicTestClient):

    @pytest.mark.parametrize("json_response, result", [([1], True), ([0], False)])
    def test_platform_status(self, requests_mock, json_response, result):
        requests_mock.get(self.client._url_for("/v2/platform/status"), json=json_response)
        assert self.client.platform_status() == result
