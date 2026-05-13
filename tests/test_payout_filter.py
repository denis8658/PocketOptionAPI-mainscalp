from signal_client.payout_filter import classify_payout, final_trade_score, normalize_payout
from signal_client.signal_engine import generate_signal
from tests.test_impulse_analyzer import bullish_impulse


def test_normalizes_percent_and_decimal_payouts():
    assert normalize_payout(87) == 0.87
    assert normalize_payout(0.87) == 0.87
    assert normalize_payout(None) is None


def test_classifies_payout_priorities():
    assert classify_payout(69).priority == "IGNORE"
    assert classify_payout(75).priority == "LOW_PRIORITY"
    assert classify_payout(85).priority == "GOOD"
    assert classify_payout(92).priority == "PREMIUM"
    assert classify_payout(None).trade_allowed is False


def test_final_score_formula_weights_components():
    score = final_trade_score(
        breakout_score=90,
        impulse_score=80,
        volatility_score=70,
        payout_score=100,
    )

    assert score == 84.0


def test_signal_blocks_trade_below_minimum_payout():
    signal = generate_signal(bullish_impulse(), payout=75, min_confidence=50, min_payout=0.80)

    assert signal.direction == "AGUARDAR"
    assert signal.stats["trade_allowed"] is False
    assert signal.stats["priority"] == "LOW_PRIORITY"


def test_signal_allows_trade_at_or_above_minimum_payout():
    signal = generate_signal(bullish_impulse(), payout=85, min_confidence=50, min_payout=0.80)

    assert signal.stats["trade_allowed"] is True
    assert signal.stats["priority"] == "GOOD"
    assert signal.stats["final_score"] > 0
