# ============================================================
# portfolio_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Carteira Institucional Final
# Filosofia:
# 1) Fundamentalista escolhe as 20 melhores empresas
# 2) Técnico define prioridade/momento de entrada
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


INPUT_PREMIUM = Path("output/top20_premium.csv")
INPUT_TECNICO = Path("output/top20_tecnico.csv")
OUTPUT_FILE = Path("output/carteira_institucional.csv")

PESO_FUNDAMENTALISTA = 0.70
PESO_TECNICO = 0.30


def carregar_csv(caminho):
    if caminho.exists():
        return pd.read_csv(caminho)
    return pd.DataFrame()


def calcular_peso_por_score(df, score_col="score_gestor"):
    df = df.copy()
    total_score = df[score_col].sum()

    if total_score <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df[score_col] / total_score

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100
    return df


def limitar_peso_maximo(df, peso_maximo=0.10):
    df = df.copy()
    df["peso_sugerido"] = df["peso_sugerido"].clip(upper=peso_maximo)

    total = df["peso_sugerido"].sum()
    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100
    return df


def definir_decisao(score):
    if score >= 80:
        return "COMPRAR AGORA"
    if score >= 70:
        return "COMPRAR PARCIAL"
    if score >= 60:
        return "AGUARDAR MELHOR ENTRADA"
    return "NÃO PRIORIZAR AGORA"


def montar_carteira():
    premium = carregar_csv(INPUT_PREMIUM)
    tecnico = carregar_csv(INPUT_TECNICO)

    if premium.empty:
        print("Arquivo top20_premium.csv não encontrado.")
        return pd.DataFrame()

    base = premium.copy()

    if not tecnico.empty and "ticker" in tecnico.columns:
        cols_tecnico = [
            "ticker",
            "score_tecnico",
            "sinal_tecnico",
            "rsi14",
            "retorno_20d",
            "dist_mm200",
            "volume_forca",
        ]

        cols_tecnico = [c for c in cols_tecnico if c in tecnico.columns]

        base = base.merge(
            tecnico[cols_tecnico],
            on="ticker",
            how="left"
        )

    if "score_balanceado" not in base.columns:
        base["score_balanceado"] = 50

    if "score_tecnico" not in base.columns:
        base["score_tecnico"] = 50

    if "sinal_tecnico" not in base.columns:
        base["sinal_tecnico"] = "NEUTRO"

    base["score_balanceado"] = pd.to_numeric(
        base["score_balanceado"], errors="coerce"
    ).fillna(50)

    base["score_tecnico"] = pd.to_numeric(
        base["score_tecnico"], errors="coerce"
    ).fillna(50)

    base["score_qualidade"] = base["score_balanceado"]

    base["score_gestor"] = (
        base["score_balanceado"] * PESO_FUNDAMENTALISTA
        + base["score_tecnico"] * PESO_TECNICO
    )

    base["score_gestor"] = base["score_gestor"].clip(0, 100)

    base["decisao"] = base["score_gestor"].apply(definir_decisao)

    base = base.sort_values(
        "score_gestor",
        ascending=False
    ).reset_index(drop=True)

    base.insert(0, "ranking_carteira", base.index + 1)

    base = calcular_peso_por_score(base, "score_gestor")
    base = limitar_peso_maximo(base, peso_maximo=0.10)

    Path("output").mkdir(exist_ok=True)

    base.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("Carteira institucional salva:")
    print(OUTPUT_FILE)

    return base


if __name__ == "__main__":
    montar_carteira()
