import collections

TradingPairData = collections.namedtuple(
    "TradingPairData",
    "symbol, bid, bid_size, ask, ask_size, daily_change, daily_change_perc, last_price, volume, high, low"
)

FundingCurrencyData = collections.namedtuple(
    "FundingCurrencyData",
    "symbol, frr, bid, bid_size, bid_period, ask, ask_size, ask_period, daily_change, daily_change_perc, last_price, volume, high, low"
)

__all__ = [
    "TradingPairData",
    "FundingCurrencyData",
]
