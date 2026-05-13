from signal_client.signal_engine import generate_signal
from signal_client.statistical_models import ModelManager, StatisticalEngine
from tests.test_impulse_analyzer import bullish_impulse


def test_model_manager_loads_balanced_model_by_alias():
    model = ModelManager.load("MODELO_B_BALANCEADO")

    assert model.key == "MODEL_B"
    assert model.market_context["candle_row"] == 4
    assert model.market_context["betting_chance"] == 72
    assert model.filters["require_impulse_confirmation"] is True


def test_statistical_engine_returns_automatic_buy_direction():
    decision = StatisticalEngine("MODEL_B").decide(
        "CALL",
        84,
        {
            "call_score": 84,
            "put_score": 18,
            "breakout_score": 88,
            "impulse_score": 82,
            "volatility_score": 30,
            "payout_score": 70,
            "payout_allowed": True,
            "pattern_score": 45,
            "accumulation_score": 20,
        },
    )

    assert decision.direction == "CALL"
    assert decision.is_trade_signal is True
    assert decision.to_dict()["auto_direction"] is True


def test_statistical_engine_blocks_when_scores_are_too_close():
    decision = StatisticalEngine("MODEL_B").decide(
        "CALL",
        76,
        {
            "call_score": 76,
            "put_score": 70,
            "breakout_score": 55,
            "impulse_score": 80,
            "volatility_score": 30,
            "payout_score": 70,
            "payout_allowed": True,
            "pattern_score": 20,
            "accumulation_score": 0,
        },
    )

    assert decision.direction == "AGUARDAR"
    assert decision.blocked_reason == "placar_comprador_vendedor_muito_proximo"


def test_generate_signal_uses_selected_model_for_auto_call_signal():
    signal = generate_signal(
        bullish_impulse(),
        payout=85,
        min_confidence=50,
        min_payout=0.80,
        selected_model="MODEL_B",
    )

    assert signal.direction == "CALL"
    assert signal.stats["model_decision"]["active_model"] == "MODEL_B"
    assert signal.stats["model_decision"]["auto_direction"] is True
