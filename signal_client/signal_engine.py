"""Signal generation helpers for PocketSignalClient."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SignalResult:
    direction: str
    confidence: int
    summary: str
    entry_price: Optional[float]
    reasons: List[str]
    stats: Dict[str, Any]


def sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(values: List[float], period: int = 14) -> Optional[float]:
    if len(values) <= period:
        return None

    gains = []
    losses = []
    window = values[-period - 1 :]
    for previous, current in zip(window, window[1:]):
        change = current - previous
        if change >= 0:
            gains.append(change)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(change))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def normalize_candles(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for candle in candles:
        try:
            normalized.append(
                {
                    "open": float(candle["open"]),
                    "close": float(candle["close"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "timestamp": int(candle["timestamp"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(normalized, key=lambda item: item["timestamp"])


def generate_signal(
    candles: List[Dict[str, Any]],
    payout: Optional[float] = None,
    min_confidence: int = 62,
) -> SignalResult:
    data = normalize_candles(candles)
    if len(data) < 25:
        return SignalResult(
            direction="AGUARDAR",
            confidence=0,
            summary="Poucos candles para leitura confiavel",
            entry_price=None,
            reasons=["Busque pelo menos 50 candles para gerar sinal."],
            stats={"candles": len(data), "payout": payout},
        )

    closes = [item["close"] for item in data]
    last = data[-1]
    previous = data[-2]
    price = closes[-1]

    fast = sma(closes, 5)
    slow = sma(closes, 20)
    rsi_value = rsi(closes, 14)
    momentum_3 = closes[-1] - closes[-4]
    body = last["close"] - last["open"]
    previous_body = previous["close"] - previous["open"]

    call_score = 0
    put_score = 0
    reasons: List[str] = []

    if fast is not None and slow is not None:
        if fast > slow:
            call_score += 28
            reasons.append("Media curta acima da media longa")
        elif fast < slow:
            put_score += 28
            reasons.append("Media curta abaixo da media longa")

    if momentum_3 > 0:
        call_score += 20
        reasons.append("Momentum dos ultimos candles positivo")
    elif momentum_3 < 0:
        put_score += 20
        reasons.append("Momentum dos ultimos candles negativo")

    if body > 0 and previous_body >= 0:
        call_score += 18
        reasons.append("Ultimos candles fechando comprador")
    elif body < 0 and previous_body <= 0:
        put_score += 18
        reasons.append("Ultimos candles fechando vendedor")

    if rsi_value is not None:
        if 52 <= rsi_value <= 70:
            call_score += 17
            reasons.append(f"RSI em zona compradora ({rsi_value:.1f})")
        elif 30 <= rsi_value <= 48:
            put_score += 17
            reasons.append(f"RSI em zona vendedora ({rsi_value:.1f})")
        elif rsi_value > 78 or rsi_value < 22:
            reasons.append(f"RSI extremo ({rsi_value:.1f}); melhor aguardar")
            call_score -= 12
            put_score -= 12

    if payout is not None:
        if payout >= 80:
            call_score += 8
            put_score += 8
            reasons.append(f"Payout favoravel ({payout:.0f}%)")
        elif payout < 70:
            call_score -= 10
            put_score -= 10
            reasons.append(f"Payout baixo ({payout:.0f}%)")

    if call_score > put_score:
        direction = "CALL"
        confidence = max(0, min(100, call_score))
    elif put_score > call_score:
        direction = "PUT"
        confidence = max(0, min(100, put_score))
    else:
        direction = "AGUARDAR"
        confidence = 0

    if confidence < min_confidence:
        direction = "AGUARDAR"
        summary = "Sem confluencia suficiente"
    else:
        summary = f"Sinal {direction} com {confidence}% de confianca"

    return SignalResult(
        direction=direction,
        confidence=confidence,
        summary=summary,
        entry_price=price,
        reasons=reasons[:6],
        stats={
            "candles": len(data),
            "payout": payout,
            "price": price,
            "sma_5": fast,
            "sma_20": slow,
            "rsi_14": rsi_value,
            "momentum_3": momentum_3,
            "call_score": call_score,
            "put_score": put_score,
        },
    )
