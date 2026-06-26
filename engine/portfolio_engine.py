# ============================================================
# portfolio_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Carteira Institucional Final
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


INPUT_PREMIUM = Path("output/top20_premium.csv")
INPUT_TECNICO = Path("output/top20_tecnico.csv")
INPUT_DIVERSIFICADO = Path("output/top20_diversificado.csv")

OUTPUT_FILE = Path("output/carteira_institucional.csv")


def carregar_csv(caminho):
    if caminho.exists():
        return pd.read_csv(caminho)

    return pd.DataFrame()


def calcular_peso_por_score(df, score_col="score_final_carteira"):
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


def montar_carteira():
    premium = carregar_csv(INPUT_PREMIUM)
    tecnico = carregar_csv(INPUT_TECNICO)
    diversificado = carregar_csv(INPUT_DIVERSIFICADO)

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

        cols_tecnico = [col for col in cols_tecnico if col in tecnico.columns]

        base = base.merge(
            tecnico[cols_tecnico],
            on="ticker",
            how="left"
        )

    if not diversificado.empty and "ticker" in diversificado.columns:
        base["selecionada_diversificacao"] = base["ticker"].isin(
            diversificado["ticker"]
        )
    else:
        base["selecionada_diversificacao"] = True

    if "score_tecnico" not in base.columns:
        base["score_tecnico"] = 50

    if "sinal_tecnico" not in base.columns:
        base["sinal_tecnico"] = "NEUTRO"

    if "score_balanceado" not in base.columns:
        base["score_balanceado"] = 50

    if "moat_score" not in base.columns:
        base["moat_score"] = 50

    base["score_tecnico"] = pd.to_numeric(
        base["score_tecnico"], errors="coerce"
    ).fillna(50)

    base["score_balanceado"] = pd.to_numeric(
        base["score_balanceado"], errors="coerce"
    ).fillna(50)

    base["moat_score"] = pd.to_numeric(
        base["moat_score"], errors="coerce"
    ).fillna(50)

    sinal = base["sinal_tecnico"].astype(str).str.upper()

    base["ajuste_tecnico"] = np.select(
        [
            sinal.str.contains("COMPRA FORTE", na=False),
            sinal.eq("COMPRA"),
            sinal.str.contains("AGUARDAR", na=False),
            sinal.str.contains("FRACO", na=False),
            sinal.str.contains("EVITAR", na=False),
        ],
        [5, 2, -3, -12, -20],
        default=0,
    )

    base["score_final_carteira"] = (
        base["score_balanceado"] * 0.50
        + base["score_tecnico"] * 0.35
        + base["moat_score"] * 0.15
        + base["ajuste_tecnico"]
    )

    base["score_final_carteira"] = base["score_final_carteira"].clip(0, 100)

    base = base.sort_values(
        "score_final_carteira",
        ascending=False
    ).reset_index(drop=True)

    base = base.head(20)

    base = calcular_peso_por_score(base)
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
