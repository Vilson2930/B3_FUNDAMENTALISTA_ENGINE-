# ============================================================
# utils.py
# B3 FUNDAMENTALISTA ENGINE
# Funções auxiliares
# ============================================================

import numpy as np
import pandas as pd


def score_percentil(serie):
    return serie.rank(
        pct=True,
        method="average"
    ) * 100


def score_percentil_invertido(serie):
    return 100 - score_percentil(serie)


def limpar_inf_nan(df):
    df = df.copy()

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    return df


def winsorizar(serie, limite_inferior=0.01, limite_superior=0.99):
    inferior = serie.quantile(limite_inferior)
    superior = serie.quantile(limite_superior)

    return serie.clip(
        lower=inferior,
        upper=superior
    )


def limitar_por_setor(df, coluna_score, limite_setor=3, top_n=30):
    selecionadas = []
    contagem_setor = {}

    df_ordenado = df.sort_values(
        coluna_score,
        ascending=False
    )

    for _, row in df_ordenado.iterrows():
        setor = row.get("setor", "SEM SETOR")

        contagem_setor[setor] = contagem_setor.get(setor, 0)

        if contagem_setor[setor] < limite_setor:
            selecionadas.append(row)
            contagem_setor[setor] += 1

        if len(selecionadas) >= top_n:
            break

    return pd.DataFrame(selecionadas)


def formatar_percentual(valor):
    try:
        return f"{valor:.2%}"
    except Exception:
        return "N/A"


def formatar_numero(valor):
    try:
        return f"{valor:,.2f}"
    except Exception:
        return "N/A"
