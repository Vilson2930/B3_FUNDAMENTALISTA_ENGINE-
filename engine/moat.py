# ============================================================
# moat.py
# B3 FUNDAMENTALISTA ENGINE
# Moat Score — Vantagem Competitiva Quantitativa
# ============================================================


def calcular_moat(df):
    df = df.copy()

    componentes = []

    if "score_profitability" in df.columns:
        componentes.append(("score_profitability", 0.30))

    if "score_leverage" in df.columns:
        componentes.append(("score_leverage", 0.20))

    if "score_growth" in df.columns:
        componentes.append(("score_growth", 0.20))

    if "score_cashflow" in df.columns:
        componentes.append(("score_cashflow", 0.15))

    if "score_valuation" in df.columns:
        componentes.append(("score_valuation", 0.15))

    if not componentes:
        df["moat_score"] = 50
        return df

    total_peso = sum(peso for _, peso in componentes)

    df["moat_score"] = 0

    for coluna, peso in componentes:
        df["moat_score"] += df[coluna].fillna(50) * (peso / total_peso)

    return df


def classificar_moat(score):
    if score >= 90:
        return "MOAT MUITO FORTE"
    elif score >= 80:
        return "MOAT FORTE"
    elif score >= 70:
        return "MOAT BOM"
    elif score >= 60:
        return "MOAT MODERADO"
    elif score >= 50:
        return "MOAT FRACO"
    else:
        return "SEM MOAT"


def aplicar_classificacao_moat(df):
    df = df.copy()

    df["moat_classificacao"] = df["moat_score"].apply(classificar_moat)

    return df
