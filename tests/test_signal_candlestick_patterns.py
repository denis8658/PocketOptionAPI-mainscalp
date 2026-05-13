from signal_client.candlestick_patterns import detect_candlestick_patterns
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


def trend_down(start=1.2000, count=24, step=0.0010):
    rows = []
    price = start
    for index in range(count):
        rows.append(candle(index, price, price + 0.0002, price - step - 0.0002, price - step))
        price -= step
    return rows


def trend_up(start=1.1000, count=24, step=0.0010):
    rows = []
    price = start
    for index in range(count):
        rows.append(candle(index, price, price + step + 0.0002, price - 0.0002, price + step))
        price += step
    return rows


def pattern_names(rows):
    return {item["name"] for item in detect_candlestick_patterns(rows).ranking}


def test_detects_hammer_with_context_and_confirmation():
    rows = trend_down()
    rows.extend(
        [
            candle(24, 1.1760, 1.1762, 1.1710, 1.1758, 140),
            candle(25, 1.1759, 1.1785, 1.1758, 1.1782, 150),
        ]
    )

    analysis = detect_candlestick_patterns(rows)

    assert "Hammer" in {item["name"] for item in analysis.ranking}
    assert analysis.bullish_score > analysis.bearish_score


def test_detects_shooting_star_bearish_reversal():
    rows = trend_up()
    rows.extend(
        [
            candle(24, 1.1240, 1.1300, 1.1239, 1.1242, 140),
            candle(25, 1.1241, 1.1242, 1.1210, 1.1212, 150),
        ]
    )

    analysis = detect_candlestick_patterns(rows)

    assert "Shooting Star" in {item["name"] for item in analysis.ranking}
    assert analysis.bearish_score > 0


def test_detects_requested_multi_candle_patterns():
    bullish_engulfing = trend_down() + [
        candle(24, 1.1760, 1.1761, 1.1730, 1.1735),
        candle(25, 1.1730, 1.1770, 1.1728, 1.1765),
    ]
    morning_star = trend_down() + [
        candle(24, 1.1760, 1.1762, 1.1720, 1.1725),
        candle(25, 1.1724, 1.1726, 1.1719, 1.17245),
        candle(26, 1.1725, 1.1760, 1.1724, 1.1750),
    ]
    three_soldiers = trend_up(count=20) + [
        candle(20, 1.1200, 1.1224, 1.1198, 1.1220),
        candle(21, 1.1221, 1.1246, 1.1220, 1.1242),
        candle(22, 1.1243, 1.1269, 1.1241, 1.1265),
    ]

    assert "Bullish Engulfing" in pattern_names(bullish_engulfing)
    assert "Morning Star" in pattern_names(morning_star)
    assert "Three White Soldiers" in pattern_names(three_soldiers)


def test_detects_bearish_family_patterns():
    bearish_engulfing = trend_up() + [
        candle(24, 1.1240, 1.1265, 1.1238, 1.1260),
        candle(25, 1.1265, 1.1268, 1.1228, 1.1232),
    ]
    evening_star = trend_up() + [
        candle(24, 1.1240, 1.1280, 1.1238, 1.1275),
        candle(25, 1.1276, 1.1280, 1.1273, 1.12765),
        candle(26, 1.1275, 1.1277, 1.1235, 1.1240),
    ]
    three_crows = trend_down(count=20) + [
        candle(20, 1.1800, 1.1802, 1.1775, 1.1778),
        candle(21, 1.1777, 1.1779, 1.1750, 1.1754),
        candle(22, 1.1753, 1.1755, 1.1728, 1.1730),
    ]

    assert "Bearish Engulfing" in pattern_names(bearish_engulfing)
    assert "Evening Star" in pattern_names(evening_star)
    assert "Three Black Crows" in pattern_names(three_crows)


def test_detects_indecision_harami_tweezer_and_marubozu():
    base_down = trend_down()
    doji_rows = base_down + [candle(24, 1.1760, 1.1770, 1.1750, 1.17604)]
    harami_rows = base_down + [
        candle(24, 1.1760, 1.1762, 1.1720, 1.1725),
        candle(25, 1.1730, 1.1750, 1.1729, 1.1745),
    ]
    tweezer_rows = base_down + [
        candle(24, 1.1760, 1.1762, 1.1720, 1.1728),
        candle(25, 1.1727, 1.1755, 1.17202, 1.1750),
    ]
    marubozu_rows = trend_up() + [candle(24, 1.1240, 1.1280, 1.12398, 1.12795)]

    assert "Doji" in pattern_names(doji_rows)
    assert "Bullish Harami" in pattern_names(harami_rows)
    assert "Tweezer Bottom" in pattern_names(tweezer_rows)
    assert "Bullish Marubozu" in pattern_names(marubozu_rows)


def test_generate_signal_exposes_pattern_ranking_without_breaking_api():
    rows = trend_down() + [
        candle(24, 1.1760, 1.1762, 1.1730, 1.1735),
        candle(25, 1.1730, 1.1770, 1.1728, 1.1765),
    ]

    signal = generate_signal(rows, payout=85, min_confidence=50)

    assert signal.direction in {"CALL", "PUT", "AGUARDAR"}
    assert "candlestick_patterns" in signal.stats
    assert signal.stats["candlestick_patterns"]
