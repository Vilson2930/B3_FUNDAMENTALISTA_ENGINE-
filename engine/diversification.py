# ============================================================
# diversification.py
# B3 FUNDAMENTALISTA ENGINE
# Diversificação setorial das melhores ações
# ============================================================

import pandas as pd


def aplicar_diversificacao_setorial(
    df,
    score_col="score_balanceado",
    setor_col="setor",
    top_n=20,
    limite_por_setor=2,
    score_minimo=0,
):
    df = df.copy()

    if df.empty:
        return df

    df = df.sort_values(score_col, ascending=False)

    selecionadas = []
    contagem_setor = {}

    for _, row in df.iterrows():
        setor = row.get(setor_col, "SEM SETOR")
        score = row.get(score_col, 0)

        if pd.isna(setor):
            setor = "SEM SETOR"

        if score < score_minimo:
            continue

        contagem_setor[setor] = contagem_setor.get(setor, 0)

        if contagem_setor[setor] < limite_por_setor:
            selecionadas.append(row)
            contagem_setor[setor] += 1

        if len(selecionadas) >= top_n:
            break

    resultado = pd.DataFrame(selecionadas)

    return resultado.reset_index(drop=True)


def aplicar_diversificacao(rankings, top_n=20, limite_por_setor=2):
    rankings = rankings.copy()

    base = rankings.get("base")

    if base is None or base.empty:
        rankings["premium_diversificado"] = pd.DataFrame()
        return rankings

    universo = rankings.get("premium", base)

    premium_diversificado = aplicar_diversificacao_setorial(
        universo,
        score_col="score_balanceado",
        setor_col="setor",
        top_n=top_n,
        limite_por_setor=limite_por_setor,
    )

    rankings["premium_diversificado"] = premium_diversificado

    return rankings
