# ============================================================
# leverage.py
# B3 FUNDAMENTALISTA ENGINE
# Indicadores de Endividamento
# ============================================================

import numpy as np


def calcular_leverage(df):

    df = df.copy()

    # ========================================================
    # Dívida / Patrimônio
    # ========================================================

    df["divida_patrimonio"] = (
        df["passivo_total"] /
        df["patrimonio_liquido"]
    )

    # ========================================================
    # Caixa / Dívida
    # ========================================================

    df["caixa_divida"] = (
        df["caixa"] /
        df["passivo_total"]
    )

    # ========================================================
    # Dívida Líquida
    # ========================================================

    df["divida_liquida"] = (
        df["passivo_total"] -
        df["caixa"]
    )

    # ========================================================
    # Dívida Líquida / Patrimônio
    # ========================================================

    df["divida_liquida_patrimonio"] = (
        df["divida_liquida"] /
        df["patrimonio_liquido"]
    )

    # ========================================================
    # Liquidez Patrimonial
    # ========================================================

    df["ativo_passivo"] = (
        df["ativo_total"] /
        df["passivo_total"]
    )

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return df


def score_leverage(df):

    df = df.copy()

    def score_invertido(serie):

        return 100 - (
            serie.rank(
                pct=True,
                method="average"
            ) * 100
        )

    def score_normal(serie):

        return (
            serie.rank(
                pct=True,
                method="average"
            ) * 100
        )

    df["score_divida_patrimonio"] = score_invertido(
        df["divida_patrimonio"]
    )

    df["score_divida_liquida"] = score_invertido(
        df["divida_liquida_patrimonio"]
    )

    df["score_caixa_divida"] = score_normal(
        df["caixa_divida"]
    )

    df["score_liquidez"] = score_normal(
        df["ativo_passivo"]
    )

    df["score_leverage"] = (
        df["score_divida_patrimonio"].fillna(50) * 0.35 +
        df["score_divida_liquida"].fillna(50) * 0.35 +
        df["score_caixa_divida"].fillna(50) * 0.15 +
        df["score_liquidez"].fillna(50) * 0.15
    )

    return df
