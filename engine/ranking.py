# ============================================================
# ranking.py
# B3 FUNDAMENTALISTA ENGINE
# Rankings Institucionais
# ============================================================

import pandas as pd


ORDEM_RATING = {
    "AAA": 1,
    "AA+": 2,
    "AA": 3,
    "AA-": 4,
    "A+": 5,
    "A": 6,
    "A-": 7,
    "BBB+": 8,
    "BBB": 9,
    "BBB-": 10,
    "BB+": 11,
    "BB": 12,
    "BB-": 13,
    "B+": 14,
    "B": 15,
    "CCC": 16,
    "N/A": 99
}


def limitar_por_setor(df, coluna_score, limite_setor=3, top_n=30):
    selecionadas = []
    contagem_setor = {}

    df_ordenado = df.sort_values(coluna_score, ascending=False)

    for _, row in df_ordenado.iterrows():
        setor = row.get("setor", "SEM SETOR")
        contagem_setor[setor] = contagem_setor.get(setor, 0)

        if contagem_setor[setor] < limite_setor:
            selecionadas.append(row)
            contagem_setor[setor] += 1

        if len(selecionadas) >= top_n:
            break

    return pd.DataFrame(selecionadas)


def ranking_premium(df, top_n=30):
    df = df.copy()

    df["rating_ordem"] = df["rating"].map(ORDEM_RATING).fillna(99)

    premium = df[
        (df["moat_score"] >= 60) &
        (df["rating_ordem"] <= ORDEM_RATING["BBB+"])
    ].copy()

    premium = premium.sort_values(
        ["score_balanceado", "moat_score"],
        ascending=False
    )

    return limitar_por_setor(
        premium,
        "score_balanceado",
        limite_setor=3,
        top_n=top_n
    )


def gerar_ranking_institucional(df):
    df = df.copy()

    rankings = {}

    if "score_profitability" in df.columns:
        rankings["profitability"] = limitar_por_setor(df, "score_profitability")

    if "score_growth" in df.columns:
        rankings["growth"] = limitar_por_setor(df, "score_growth")

    if "score_leverage" in df.columns:
        rankings["leverage"] = limitar_por_setor(df, "score_leverage")

    if "score_cashflow" in df.columns:
        rankings["cashflow"] = limitar_por_setor(df, "score_cashflow")

    if "score_valuation" in df.columns:
        rankings["valuation"] = limitar_por_setor(df, "score_valuation")

    if "moat_score" in df.columns:
        rankings["moat"] = limitar_por_setor(df, "moat_score")

    if "score_balanceado" in df.columns:
        rankings["balanceado"] = limitar_por_setor(df, "score_balanceado")
        rankings["premium"] = ranking_premium(df)

    rankings["base"] = df

    return rankings
