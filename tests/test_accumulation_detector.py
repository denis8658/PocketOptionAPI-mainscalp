from signal_client.accumulation_detector import AccumulationDetector, detect_accumulation
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


def bearish_context(count=45):
    rows = []
    price = 1.2400
    for index in range(count):
        rows.append(candle(index, price, price + 0.0008, price - 0.0024, price - 0.0018, 95))
        price -= 0.0018
    return rows


def accumulation_range(start_ts=45, base=1.1580, count=62):
    rows = []
    for offset in range(count):
        ts = start_ts + offset
        phase = offset % 8
        support = base - 0.0012
        resistance = base + 0.0015
        if offset == count - 4:
            rows.append(
                candle(
                    ts,
                    base - 0.0006,
                    base + 0.0005,
                    support - 0.0030,
                    base + 0.0003,
                    220,
                )
            )
        elif phase in (0, 5):
            rows.append(
                candle(
                    ts,
                    base - 0.0004,
                    base + 0.0008,
                    support - 0.0008,
                    base + 0.0002,
                    145 + offset,
                )
            )
        elif phase == 3:
            rows.append(
                candle(
                    ts,
                    base + 0.0008,
                    resistance + 0.0007,
                    base - 0.0002,
                    base + 0.0004,
                    135 + offset,
                )
            )
        else:
            rows.append(
                candle(
                    ts,
                    base - 0.0002,
                    base + 0.0010,
                    base - 0.0009,
                    base + 0.0001,
                    125 + offset,
                )
            )
    return rows


def volatile_directional_market(count=80):
    rows = []
    price = 1.1000
    for index in range(count):
        close = price + 0.0025
        rows.append(candle(index, price, close + 0.0014, price - 0.0006, close, 100))
        price = close
    return rows


def test_detects_institutional_accumulation_zone():
    rows = bearish_context() + accumulation_range()

    result = detect_accumulation(rows, lookback=60)

    assert result["is_accumulation"] is True
    assert result["confidence"] >= 0.58
    assert result["zone"]["support"] < result["zone"]["resistance"]
    assert result["metrics"]["rejection_count"] >= 3
    assert result["metrics"]["fake_breakouts"] >= 1
    assert result["context"]["previous_trend"] == "baixa"


def test_rejects_directional_non_accumulation_market():
    result = AccumulationDetector(lookback=60).detect(volatile_directional_market())

    assert result["is_accumulation"] is False
    assert result["confidence"] < 0.58


def test_handles_bad_and_short_data_without_exception():
    result = detect_accumulation(
        [
            {"open": "nan", "high": 1, "low": 1, "close": 1, "timestamp": 1},
            {"open": 1, "high": 1, "low": 1, "close": 1, "timestamp": 2},
        ]
    )

    assert result["is_accumulation"] is False
    assert result["context"]["reason"] == "dados insuficientes"


def test_generate_signal_exposes_accumulation_metrics():
    rows = bearish_context() + accumulation_range()

    signal = generate_signal(rows, payout=82, min_confidence=50, channel_period=20)

    assert "accumulation" in signal.stats
    assert signal.stats["accumulation"]["quality"] in {
        "fraca",
        "moderada",
        "forte",
        "institucional",
        "sem_acumulacao",
    }
