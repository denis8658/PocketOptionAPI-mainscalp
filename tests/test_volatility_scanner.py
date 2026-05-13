from signal_client.volatility_scanner import (
    STATE_COMPRESSION,
    STATE_HIGH_VOLATILITY,
    STATE_PRE_BREAKOUT,
    MarketScanner,
    VolatilityAnalyzer,
)


def candle(ts, open_, high, low, close, volume=100):
    return {
        "timestamp": ts,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def trending_market(symbol_shift=0.0, count=120):
    rows = []
    price = 1.1000 + symbol_shift
    for index in range(count):
        close = price + 0.0018
        rows.append(candle(index, price, close + 0.0012, price - 0.0004, close, 140 + index % 5))
        price = close
    return rows


def compressed_market(count=120):
    rows = []
    base = 1.2500
    for index in range(count):
        width = 0.0025 if index < count // 2 else 0.00055
        open_ = base + (0.0001 if index % 2 == 0 else -0.0001)
        close = base + (-0.00008 if index % 2 == 0 else 0.00008)
        rows.append(candle(index, open_, base + width, base - width, close, 150 + index % 7))
    return rows


def quiet_market(count=120):
    rows = []
    base = 1.0500
    for index in range(count):
        rows.append(candle(index, base, base + 0.00025, base - 0.00025, base + 0.00002, 80))
    return rows


def test_analyzer_calculates_core_metrics():
    metrics = VolatilityAnalyzer().analyze("TREND", trending_market(), 15)

    assert metrics.atr > 0
    assert metrics.atr_percent > 0
    assert metrics.directional_efficiency > 0.8
    assert metrics.liquidity_score > 80


def test_scanner_ranks_high_volatility_above_quiet_market():
    scanner = MarketScanner()
    result = scanner.scan(
        {
            "TREND|15": trending_market(),
            "QUIET|15": quiet_market(),
            "COMPRESS|15": compressed_market(),
        }
    )

    assert result["ranking"][0]["symbol"] in {"TREND", "COMPRESS"}
    assert result["ranking"][0]["trade_quality"] >= result["ranking"][-1]["trade_quality"]
    assert result["benchmark"]["markets"] == 3


def test_detects_compression_or_pre_breakout_state():
    scanner = MarketScanner()
    result = scanner.scan({"COMPRESS|15": compressed_market()})

    assert result["ranking"][0]["state"] in {STATE_COMPRESSION, STATE_PRE_BREAKOUT}


def test_handles_incomplete_data_without_exception():
    scanner = MarketScanner()
    result = scanner.scan({"BAD|60": [{"open": None}, {"open": 1, "close": 1}]})

    assert result["ranking"][0]["symbol"] == "BAD"
    assert result["ranking"][0]["metrics"]["candles"] == 0


def test_cross_market_multi_timeframe_shape():
    markets = []
    for symbol in ("AAA", "BBB", "CCC"):
        for timeframe in (5, 15, 60):
            markets.append({"symbol": symbol, "timeframe": timeframe, "candles": trending_market()})

    result = MarketScanner().scan(markets)

    assert len(result["ranking"]) == 9
    assert result["best"]["state"] in {
        "TRENDING",
        "EXPANSION",
        STATE_HIGH_VOLATILITY,
        "EXTREME_VOLATILITY",
        "NORMAL",
    }
