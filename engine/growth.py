# ============================================================
# growth.py
# B3 FUNDAMENTALISTA ENGINE
# Indicadores de Crescimento
# ============================================================

import numpy as np


def calcular_growth(df):

    df = df.copy()

    # ========================================================
    # Crescimento da Receita
    # ========================================================

    if (
        "penultima_receita" in df.columns and
        "receita" in df.columns
    ):

        df["crescimento_receita"] = (
            (
                df["receita"] -
                df["penultima_receita"]
            ) /
            df["penultima_receita"].replace(0, np.nan)
        )

    # ========================================================
    # Crescimento do Lucro
    # ========================================================

    if (
        "penultimo_lucro" in df.columns and
        "lucro_liquido" in df.columns
    ):

        df["crescimento_lucro"] = (
            (
                df["lucro_liquido"] -
                df["penultimo_lucro"]
            ) /
            df["penultimo_lucro"].replace(0, np.nan)
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


def score_growth(df):

    df = df.copy()

    def score_percentil(serie):

        return (
            serie.rank(
                pct=True,
                method="average"
            ) * 100
        )

    df["score_crescimento_receita"] = score_percentil(
        df["crescimento_receita"]
    )

    df["score_crescimento_lucro"] = score_percentil(
        df["crescimento_lucro"]
    )

    df["score_growth"] = (
        df["score_crescimento_receita"].fillna(50) * 0.50 +
        df["score_crescimento_lucro"].fillna(50) * 0.50
    )

    return df
