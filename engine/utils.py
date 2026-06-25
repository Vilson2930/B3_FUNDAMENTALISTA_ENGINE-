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


def winsorizar(
    serie,
    limite_inferior=0.01,
    limite_superior=0.99
):
    inferior = serie.quantile(limite_inferior)
    superior = serie.quantile(limite_superior)

    return serie.clip(
        lower=inferior,
        upper=superior
    )


def limitar_por_setor(
    df,
    coluna_score,
    top_n=20,
    limite_setor=2,
    limite_subsetor=1
):
    """
    Seleciona empresas respeitando limite por setor
    e subsetor.
    """

    if df.empty:
        return df.copy()

    df = df.copy()

    if "setor" not in df.columns:
        df["setor"] = "SEM SETOR"

    if "subsetor" not in df.columns:
        df["subsetor"] = df["setor"]

    df["setor"] = df["setor"].fillna("SEM SETOR")
    df["subsetor"] = df["subsetor"].fillna(df["setor"])

    df = df.sort_values(
        coluna_score,
        ascending=False
    )

    selecionadas = []
    contador_setor = {}
    contador_subsetor = {}

    for _, row in df.iterrows():

        setor = row["setor"]
        subsetor = row["subsetor"]

        if contador_setor.get(setor, 0) >= limite_setor:
            continue

        if contador_subsetor.get(subsetor, 0) >= limite_subsetor:
            continue

        selecionadas.append(row)

        contador_setor[setor] = contador_setor.get(setor, 0) + 1
        contador_subsetor[subsetor] = contador_subsetor.get(subsetor, 0) + 1

        if len(selecionadas) >= top_n:
            break

    resultado = pd.DataFrame(selecionadas)

    return resultado.reset_index(drop=True)


def distribuicao_setorial(df):
    if df.empty or "setor" not in df.columns:
        return pd.DataFrame()

    return (
        df["setor"]
        .fillna("SEM SETOR")
        .value_counts()
        .reset_index()
        .rename(
            columns={
                "index": "setor",
                "setor": "quantidade"
            }
        )
    )


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
