# ============================================================
# profitability.py
# B3 FUNDAMENTALISTA ENGINE
# Indicadores de Rentabilidade
# ============================================================

import numpy as np


def calcular_profitability(df):
    df = df.copy()

    # ========================================================
    # ROE
    # Lucro Líquido / Patrimônio Líquido
    # ========================================================

    df["roe"] = (
        df["lucro_liquido"] /
        df["patrimonio_liquido"]
    )

    # ========================================================
    # ROA
    # Lucro Líquido / Ativo Total
    # ========================================================

    df["roa"] = (
        df["lucro_liquido"] /
        df["ativo_total"]
    )

    # ========================================================
    # Margem Líquida
    # Lucro Líquido / Receita
    # ========================================================

    df["margem_liquida"] = (
        df["lucro_liquido"] /
        df["receita"]
    )

    # ========================================================
    # Margem EBIT
    # EBIT / Receita
    # ========================================================

    df["margem_ebit"] = (
        df["ebit"] /
        df["receita"]
    )

    # ========================================================
    # ROIC aproximado
    # EBIT / Capital Investido
    #
    # Capital Investido aproximado:
    # Patrimônio Líquido + Dívida Líquida
    # ========================================================

    df["capital_investido"] = (
        df["patrimonio_liquido"] +
        df["divida_liquida"]
    )

    df["roic_aproximado"] = (
        df["ebit"] /
        df["capital_investido"]
    )

    # ========================================================
    # Limpeza
    # ========================================================

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return df


def score_profitability(df):
    df = df.copy()

    def score_percentil(serie):
        return serie.rank(
            pct=True,
            method="average"
        ) * 100

    df["score_roe"] = score_percentil(df["roe"])
    df["score_roa"] = score_percentil(df["roa"])
    df["score_margem_liquida"] = score_percentil(df["margem_liquida"])
    df["score_margem_ebit"] = score_percentil(df["margem_ebit"])
    df["score_roic"] = score_percentil(df["roic_aproximado"])

    df["score_profitability"] = (
        df["score_roe"].fillna(50) * 0.25 +
        df["score_roa"].fillna(50) * 0.20 +
        df["score_margem_liquida"].fillna(50) * 0.20 +
        df["score_margem_ebit"].fillna(50) * 0.20 +
        df["score_roic"].fillna(50) * 0.15
    )

    return df
