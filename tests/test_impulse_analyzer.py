from signal_client.impulse_analyzer import (
    DIRECTION_BULLISH,
    DIRECTION_NEUTRAL,
    ImpulseAnalyzer,
    detect_impulse,
)
from signal_client.signal_engine import generate_signal


def candle(ts, open_, high, low, close, volume=100):
    return {
        "timestamp": ts,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def compressed_context(count=35):
    rows = []
    base = 1.2000
    for index in range(count):
        width = 0.0012 if index < count // 2 else 0.00045
        open_ = base - 0.00008 if index % 2 else base + 0.00008
        close = base + 0.00005 if index % 2 else base - 0.00005
        rows.append(candle(index, open_, base + width, base - width, close, 90 + index % 3))
    return rows


def bullish_impulse():
    rows = compressed_context()
    price = 1.2010
    for offset in range(6):
        ts = len(rows)
        open_ = price
        close = price + 0.0022 + offset * 0.00025
        rows.append(candle(ts, open_, close + 0.00035, open_ - 0.00015, close, 180 + offset * 15))
        price = close + 0.00015
    return rows


def choppy_market(count=60):
    rows = []
    base = 1.1000
    for index in range(count):
        high = base + 0.0010
        low = base - 0.0010
        close = base + (0.0002 if index % 2 else -0.0002)
        rows.append(candle(index, base, high, low, close, 100))
    return rows


def test_detects_bullish_institutional_impulse():
    result = detect_impulse(bullish_impulse())

    assert result["is_impulsive"] is True
    assert result["direction"] == DIRECTION_BULLISH
    assert result["impulse_strength"] >= 58
    assert result["metrics"]["atr_expansion"] > 1
    assert result["context"]["previous_state"] == "COMPRESSION"


def test_rejects_choppy_market_as_impulse():
    result = ImpulseAnalyzer().analyze(choppy_market())

    assert result["is_impulsive"] is False
    assert result["direction"] in {DIRECTION_NEUTRAL, "BULLISH", "BEARISH"}
    assert result["impulse_strength"] < 58


def test_handles_short_bad_data():
    result = detect_impulse([{"open": None}, {"open": 1, "high": 1, "low": 1, "close": 1}])

    assert result["is_impulsive"] is False
    assert result["context"]["previous_state"] == "INSUFFICIENT_DATA"


def test_generate_signal_exposes_impulse_stats():
    signal = generate_signal(bullish_impulse(), payout=82, min_confidence=50)

    assert "impulse" in signal.stats
    assert signal.stats["impulse"]["direction"] == DIRECTION_BULLISH
