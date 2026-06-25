# ============================================================
# valuation.py
# B3 FUNDAMENTALISTA ENGINE
# Valuation Institucional
# ============================================================

import numpy as np


def score_percentil_invertido(serie):
    return 100 - (
        serie.rank(pct=True, method="average") * 100
    )


def calcular_valuation(df):
    df = df.copy()

    # CVM publica valores em MIL REAIS.
    # Market cap da BRAPI vem em REAIS.
    df["lucro_liquido_reais"] = df["lucro_liquido"] * 1000
    df["patrimonio_liquido_reais"] = df["patrimonio_liquido"] * 1000
    df["ebit_reais"] = df["ebit"] * 1000

    df["divida_liquida"] = (
        df["passivo_total"] -
        df["caixa"]
    )

    df["divida_liquida_reais"] = df["divida_liquida"] * 1000

    df["enterprise_value"] = (
        df["market_cap"] +
        df["divida_liquida_reais"]
    )

    df["pl_ratio"] = (
        df["market_cap"] /
        df["lucro_liquido_reais"]
    )

    df["pvp_ratio"] = (
        df["market_cap"] /
        df["patrimonio_liquido_reais"]
    )

    df["ev_ebit"] = (
        df["enterprise_value"] /
        df["ebit_reais"]
    )

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    for coluna in ["pl_ratio", "pvp_ratio", "ev_ebit"]:
        df.loc[df[coluna] <= 0, coluna] = np.nan

    return df


def calcular_score_valuation(df):
    df = df.copy()

    df["score_pl"] = score_percentil_invertido(
        df["pl_ratio"]
    )

    df["score_pvp"] = score_percentil_invertido(
        df["pvp_ratio"]
    )

    df["score_ev_ebit"] = score_percentil_invertido(
        df["ev_ebit"]
    )

    df["score_valuation"] = (
        df["score_pl"].fillna(50) * 0.40 +
        df["score_pvp"].fillna(50) * 0.30 +
        df["score_ev_ebit"].fillna(50) * 0.30
    )

    return df
