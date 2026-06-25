# ============================================================
# cashflow.py
# B3 FUNDAMENTALISTA ENGINE
# Fluxo de Caixa Institucional
# ============================================================

import numpy as np


# ============================================================
# CÁLCULO DOS INDICADORES
# ============================================================

def calcular_cashflow(df):

    df = df.copy()

    # --------------------------------------------------------
    # Fluxo de Caixa Livre (aproximado)
    # FCO - CAPEX
    # --------------------------------------------------------

    if (
        "fluxo_operacional" in df.columns and
        "capex" in df.columns
    ):

        df["fcf"] = (
            df["fluxo_operacional"] -
            df["capex"]
        )

    # --------------------------------------------------------
    # FCF Yield
    # --------------------------------------------------------

    if (
        "fcf" in df.columns and
        "market_cap" in df.columns
    ):

        df["fcf_yield"] = (
            df["fcf"] /
            df["market_cap"]
        )

    # --------------------------------------------------------
    # Conversão Lucro → Caixa
    # --------------------------------------------------------

    if (
        "fluxo_operacional" in df.columns and
        "lucro_liquido" in df.columns
    ):

        df["conversao_caixa"] = (
            df["fluxo_operacional"] /
            df["lucro_liquido"]
        )

    # --------------------------------------------------------
    # Fluxo Operacional / Receita
    # --------------------------------------------------------

    if (
        "fluxo_operacional" in df.columns and
        "receita" in df.columns
    ):

        df["margem_fco"] = (
            df["fluxo_operacional"] /
            df["receita"]
        )

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return df


# ============================================================
# SCORE
# ============================================================

def score_cashflow(df):

    df = df.copy()

    def score_percentil(serie):

        return (
            serie.rank(
                pct=True,
                method="average"
            ) * 100
        )

    if "fcf_yield" in df.columns:
        df["score_fcf_yield"] = score_percentil(
            df["fcf_yield"]
        )
    else:
        df["score_fcf_yield"] = 50

    if "conversao_caixa" in df.columns:
        df["score_conversao_caixa"] = score_percentil(
            df["conversao_caixa"]
        )
    else:
        df["score_conversao_caixa"] = 50

    if "margem_fco" in df.columns:
        df["score_margem_fco"] = score_percentil(
            df["margem_fco"]
        )
    else:
        df["score_margem_fco"] = 50

    df["score_cashflow"] = (
        df["score_fcf_yield"] * 0.40 +
        df["score_conversao_caixa"] * 0.35 +
        df["score_margem_fco"] * 0.25
    )

    return df
