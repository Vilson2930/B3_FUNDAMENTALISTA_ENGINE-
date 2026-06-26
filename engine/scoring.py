# ============================================================
# scoring.py
# B3 FUNDAMENTALISTA ENGINE
# Motor de Score Institucional
# ============================================================

from engine.profitability import calcular_profitability, score_profitability
from engine.growth import calcular_growth, score_growth
from engine.leverage import calcular_leverage, score_leverage
from engine.cashflow import calcular_cashflow, score_cashflow
from engine.valuation import calcular_valuation, calcular_score_valuation
from engine.moat import calcular_moat, aplicar_classificacao_moat
from engine.rating import aplicar_rating
from engine.utils import limitar_por_setor


def gerar_rankings(base):
    base = base.copy()

    base = calcular_profitability(base)
    base = score_profitability(base)

    base = calcular_growth(base)
    base = score_growth(base)

    base = calcular_leverage(base)
    base = score_leverage(base)

    base = calcular_cashflow(base)
    base = score_cashflow(base)

    base = calcular_valuation(base)
    base = calcular_score_valuation(base)

    base["score_balanceado"] = (
        base["score_profitability"].fillna(50) * 0.25 +
        base["score_growth"].fillna(50) * 0.20 +
        base["score_leverage"].fillna(50) * 0.15 +
        base["score_cashflow"].fillna(50) * 0.10 +
        base["score_valuation"].fillna(50) * 0.30
    )

    base = calcular_moat(base)
    base = aplicar_classificacao_moat(base)
    base = aplicar_rating(base)

    rankings = {}

    rankings["qualidade"] = limitar_por_setor(
        base,
        "score_profitability",
        limite_setor=3,
        top_n=30
    )

    rankings["crescimento"] = limitar_por_setor(
        base,
        "score_growth",
        limite_setor=3,
        top_n=30
    )

    rankings["valuation"] = limitar_por_setor(
        base,
        "score_valuation",
        limite_setor=3,
        top_n=30
    )

    rankings["moat"] = limitar_por_setor(
        base,
        "moat_score",
        limite_setor=3,
        top_n=30
    )

    rankings["balanceado"] = limitar_por_setor(
        base,
        "score_balanceado",
        limite_setor=3,
        top_n=30
    )

    rankings["premium"] = limitar_por_setor(
        base,
        "score_balanceado",
        limite_setor=2,
        top_n=20
    )

    rankings["base"] = base

    return rankings
