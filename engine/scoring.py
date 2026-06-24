# ============================================================
# scoring.py
# B3 FUNDAMENTALISTA ENGINE
# Motor de Ranking
# ============================================================

import pandas as pd
import numpy as np

# ============================================================
# SCORE PERCENTIL
# ============================================================

def score_percentil(serie):

    return (
        serie.rank(
            pct=True,
            method="average"
        ) * 100
    )

# ============================================================
# LIMITADOR POR SETOR
# ============================================================

def limitar_por_setor(
    df,
    coluna_score,
    limite_setor=3,
    top_n=30
):

    selecionadas = []

    contagem = {}

    df = df.sort_values(
        coluna_score,
        ascending=False
    )

    for _, row in df.iterrows():

        setor = row["setor"]

        if setor not in contagem:
            contagem[setor] = 0

        if contagem[setor] < limite_setor:

            selecionadas.append(row)

            contagem[setor] += 1

        if len(selecionadas) >= top_n:
            break

    return pd.DataFrame(selecionadas)

# ============================================================
# QUALIDADE
# ============================================================

def calcular_score_qualidade(df):

    df = df.copy()

    df["score_qualidade"] = (

        score_percentil(df["roe"]) * 0.30 +

        score_percentil(df["roa"]) * 0.25 +

        score_percentil(
            df["margem_liquida"]
        ) * 0.20 +

        df["score_divida"] * 0.15 +

        score_percentil(
            np.log1p(df["market_cap"])
        ) * 0.05 +

        score_percentil(
            np.log1p(df["volume"])
        ) * 0.05

    )

    return df

# ============================================================
# CRESCIMENTO
# ============================================================

def calcular_score_crescimento(df):

    df = df.copy()

    df["score_crescimento"] = (

        df["score_crescimento_receita"] * 0.45 +

        df["score_crescimento_lucro"] * 0.45 +

        score_percentil(df["roe"]) * 0.10

    )

    return df

# ============================================================
# BALANCEADO
# ============================================================

def calcular_score_balanceado(df):

    df = df.copy()

    df["score_balanceado"] = (

        df["score_qualidade"] * 0.70 +

        df["score_crescimento"] * 0.30

    )

    return df

# ============================================================
# RANKINGS
# ============================================================

def gerar_rankings(base):

    base = base.copy()

    # --------------------------------------------------------
    # CONTROLE OUTLIERS
    # --------------------------------------------------------

    if "crescimento_receita" in base.columns:

        base[
            "crescimento_receita"
        ] = (
            base["crescimento_receita"]
            .clip(-1, 2)
        )

    if "crescimento_lucro" in base.columns:

        base[
            "crescimento_lucro"
        ] = (
            base["crescimento_lucro"]
            .clip(-1, 2)
        )

    # --------------------------------------------------------
    # SCORE DIVIDA
    # --------------------------------------------------------

    if "divida_patrimonio" in base.columns:

        base["score_divida"] = (

            100 -

            score_percentil(
                base["divida_patrimonio"]
            )

        )

    else:

        base["score_divida"] = 50

    # --------------------------------------------------------
    # SCORE CRESCIMENTO
    # --------------------------------------------------------

    if "crescimento_receita" in base.columns:

        base[
            "score_crescimento_receita"
        ] = score_percentil(
            base["crescimento_receita"]
        )

    else:

        base[
            "score_crescimento_receita"
        ] = 50

    if "crescimento_lucro" in base.columns:

        base[
            "score_crescimento_lucro"
        ] = score_percentil(
            base["crescimento_lucro"]
        )

    else:

        base[
            "score_crescimento_lucro"
        ] = 50

    # --------------------------------------------------------
    # SCORES
    # --------------------------------------------------------

    base = calcular_score_qualidade(base)

    base = calcular_score_crescimento(base)

    base = calcular_score_balanceado(base)

    # --------------------------------------------------------
    # RANKINGS
    # --------------------------------------------------------

    ranking_qualidade = limitar_por_setor(
        base,
        "score_qualidade",
        limite_setor=3,
        top_n=30
    )

    ranking_crescimento = limitar_por_setor(
        base,
        "score_crescimento",
        limite_setor=3,
        top_n=30
    )

    ranking_balanceado = limitar_por_setor(
        base,
        "score_balanceado",
        limite_setor=3,
        top_n=30
    )

    return {

        "base": base,

        "qualidade": ranking_qualidade,

        "crescimento": ranking_crescimento,

        "balanceado": ranking_balanceado

    }
