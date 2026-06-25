# ============================================================
# rating.py
# B3 FUNDAMENTALISTA ENGINE
# Rating Institucional
# ============================================================

import pandas as pd


# ============================================================
# RATING
# ============================================================

def gerar_rating(score):

    if pd.isna(score):
        return "N/A"

    elif score >= 95:
        return "AAA"

    elif score >= 90:
        return "AA+"

    elif score >= 85:
        return "AA"

    elif score >= 80:
        return "AA-"

    elif score >= 75:
        return "A+"

    elif score >= 70:
        return "A"

    elif score >= 65:
        return "A-"

    elif score >= 60:
        return "BBB+"

    elif score >= 55:
        return "BBB"

    elif score >= 50:
        return "BBB-"

    elif score >= 45:
        return "BB+"

    elif score >= 40:
        return "BB"

    elif score >= 35:
        return "BB-"

    elif score >= 30:
        return "B+"

    elif score >= 25:
        return "B"

    else:
        return "CCC"


# ============================================================
# DESCRIÇÃO
# ============================================================

def descricao_rating(rating):

    mapa = {

        "AAA": "Qualidade Excepcional",

        "AA+": "Qualidade Muito Alta",

        "AA": "Qualidade Muito Alta",

        "AA-": "Qualidade Muito Alta",

        "A+": "Empresa Forte",

        "A": "Empresa Forte",

        "A-": "Empresa Forte",

        "BBB+": "Boa Empresa",

        "BBB": "Boa Empresa",

        "BBB-": "Boa Empresa",

        "BB+": "Qualidade Moderada",

        "BB": "Qualidade Moderada",

        "BB-": "Qualidade Moderada",

        "B+": "Empresa Frágil",

        "B": "Empresa Frágil",

        "CCC": "Alto Risco"
    }

    return mapa.get(rating, "N/A")


# ============================================================
# APLICAR
# ============================================================

def aplicar_rating(df):

    df = df.copy()

    df["rating"] = df["moat_score"].apply(
        gerar_rating
    )

    df["descricao_rating"] = df["rating"].apply(
        descricao_rating
    )

    return df
