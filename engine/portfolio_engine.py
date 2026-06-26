# ============================================================
# portfolio_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Carteira Institucional Final
# ============================================================

from pathlib import Path
import pandas as pd


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

    excesso = 0

    while True:

        acima = df["peso_sugerido"] > peso_maximo

        if not acima.any():
            break

        excesso = (
            df.loc[acima, "peso_sugerido"] - peso_maximo
        ).sum()

        df.loc[acima, "peso_sugerido"] = peso_maximo

        abaixo = df["peso_sugerido"] < peso_maximo

        if abaixo.sum() == 0:
            break

        proporcao = (
            df.loc[abaixo, "peso_sugerido"]
            / df.loc[abaixo, "peso_sugerido"].sum()
        )

        df.loc[abaixo, "peso_sugerido"] += excesso * proporcao

    df["peso_sugerido"] = (
        df["peso_sugerido"] / df["peso_sugerido"].sum()
    )

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

    # -------------------------------------------------------
    # Junta Análise Técnica
    # -------------------------------------------------------

    if not tecnico.empty and "ticker" in tecnico.columns:

        cols_tecnico = [
            "ticker",
            "score_tecnico",
            "sinal_tecnico",
            "rsi14",
            "retorno_20d",
            "dist_mm200",
            "volume_forca"
        ]

        cols_tecnico = [
            c for c in cols_tecnico
            if c in tecnico.columns
        ]

        base = base.merge(
            tecnico[cols_tecnico],
            on="ticker",
            how="left"
        )

    # -------------------------------------------------------
    # Apenas informa se passou pela diversificação
    # -------------------------------------------------------

    if (
        not diversificado.empty
        and "ticker" in diversificado.columns
    ):

        base["selecionada_diversificacao"] = (
            base["ticker"].isin(
                diversificado["ticker"]
            )
        )

    else:

        base["selecionada_diversificacao"] = True

    # -------------------------------------------------------
    # Score Técnico
    # -------------------------------------------------------

    if "score_tecnico" not in base.columns:
        base["score_tecnico"] = 50

    base["score_tecnico"] = (
        pd.to_numeric(
            base["score_tecnico"],
            errors="coerce"
        )
        .fillna(50)
    )

    # -------------------------------------------------------
    # Score Final Institucional
    #
    # 70% Fundamentalista
    # 30% Técnico
    # -------------------------------------------------------

    base["score_final_carteira"] = (

        base["score_balanceado"].fillna(50) * 0.70 +

        base["score_tecnico"] * 0.30

    )

    # -------------------------------------------------------

    base = base.sort_values(
        "score_final_carteira",
        ascending=False
    ).reset_index(drop=True)

    base = base.head(20)

    base = calcular_peso_por_score(base)

    base = limitar_peso_maximo(
        base,
        peso_maximo=0.10
    )

    Path("output").mkdir(exist_ok=True)

    base.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 70)
    print("CARTEIRA INSTITUCIONAL")
    print("=" * 70)

    print(
        base[
            [
                "ticker",
                "score_balanceado",
                "score_tecnico",
                "score_final_carteira",
                "peso_sugerido_pct"
            ]
        ]
    )

    print("\nCarteira institucional salva em:")
    print(OUTPUT_FILE)

    return base


if __name__ == "__main__":
    montar_carteira()
