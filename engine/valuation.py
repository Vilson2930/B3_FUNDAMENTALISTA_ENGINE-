# ============================================================
# valuation.py
# B3 FUNDAMENTALISTA ENGINE
# Valuation Institucional
# ============================================================

import numpy as np


# ============================================================
# SCORE INVERTIDO
# MENOR MÚLTIPLO = MELHOR
# ============================================================

def score_percentil_invertido(serie):

    return 100 - (
        serie.rank(
            pct=True,
            method="average"
        ) * 100
    )


# ============================================================
# CALCULAR VALUATION
# ============================================================

def calcular_valuation(df):

    df = df.copy()

    # --------------------------------------------------------
    # P/L
    # --------------------------------------------------------

    df["pl_ratio"] = (
        df["market_cap"] /
        df["lucro_liquido"]
    )

    # --------------------------------------------------------
    # P/VP
    # --------------------------------------------------------

    df["pvp_ratio"] = (
        df["market_cap"] /
        df["patrimonio_liquido"]
    )

    # --------------------------------------------------------
    # DÍVIDA LÍQUIDA
    # --------------------------------------------------------

    df["divida_liquida"] = (
        df["passivo_total"] -
        df["caixa"]
    )

    # --------------------------------------------------------
    # ENTERPRISE VALUE
    # --------------------------------------------------------

    df["enterprise_value"] = (
        df["market_cap"] +
        df["divida_liquida"]
    )

    # --------------------------------------------------------
    # EV / EBIT
    # --------------------------------------------------------

    df["ev_ebit"] = (
        df["enterprise_value"] /
        df["ebit"]
    )

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return df


# ============================================================
# SCORE VALUATION
# ============================================================

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
