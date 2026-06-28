# ============================================================
# diversification.py
# B3 FUNDAMENTALISTA ENGINE
# Diversificação institucional da carteira final
# ============================================================

from pathlib import Path
import pandas as pd


INPUT_FILE = Path("output/carteira_institucional.csv")
OUTPUT_FILE = Path("output/carteira_diversificada.csv")


MAX_EMPRESAS = 15
MAX_EMPRESAS_POR_SETOR = 2
MAX_PESO_ATIVO = 0.10
MAX_PESO_SETOR = 0.20


def carregar_carteira():
    if not INPUT_FILE.exists():
        print("Arquivo carteira_institucional.csv não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    return df


def limitar_empresas_por_setor(df):
    df = df.copy()

    if "setor" not in df.columns:
        df["setor"] = "SEM SETOR"

    df["setor"] = df["setor"].fillna("SEM SETOR")

    score_col = "score_final_carteira"

    if score_col not in df.columns:
        score_col = "score_final"

    df = df.sort_values(score_col, ascending=False)

    selecionadas = []
    contador_setor = {}

    for _, row in df.iterrows():
        setor = row["setor"]

        contador_setor[setor] = contador_setor.get(setor, 0)

        if contador_setor[setor] >= MAX_EMPRESAS_POR_SETOR:
            continue

        selecionadas.append(row)
        contador_setor[setor] += 1

        if len(selecionadas) >= MAX_EMPRESAS:
            break

    return pd.DataFrame(selecionadas).reset_index(drop=True)


def recalcular_pesos(df):
    df = df.copy()

    score_col = "score_final_carteira"

    if score_col not in df.columns:
        score_col = "score_final"

    df["allocation_score_div"] = df[score_col].clip(lower=0) ** 2

    total = df["allocation_score_div"].sum()

    if total <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df["allocation_score_div"] / total

    df["peso_sugerido"] = df["peso_sugerido"].clip(upper=MAX_PESO_ATIVO)

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100

    return df


def calcular_exposicao_setorial(df):
    df = df.copy()

    exposicao = (
        df.groupby("setor")["peso_sugerido_pct"]
        .sum()
        .reset_index()
        .rename(columns={"peso_sugerido_pct": "peso_setor_pct"})
    )

    df = df.merge(exposicao, on="setor", how="left")

    df["alerta_setorial"] = df["peso_setor_pct"].apply(
        lambda x: "ACIMA DO LIMITE" if x > MAX_PESO_SETOR * 100 else "OK"
    )

    return df


def analisar_diversificacao():
    df = carregar_carteira()

    if df.empty:
        print("Nenhuma carteira para diversificar.")
        return df

    resultado = limitar_empresas_por_setor(df)
    resultado = recalcular_pesos(resultado)
    resultado = calcular_exposicao_setorial(resultado)

    Path("output").mkdir(exist_ok=True)

    resultado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 70)
    print("DIVERSIFICAÇÃO INSTITUCIONAL")
    print("=" * 70)

    colunas = [
        "ticker",
        "empresa",
        "setor",
        "score_final_carteira",
        "peso_sugerido_pct",
        "peso_setor_pct",
        "alerta_setorial",
    ]

    colunas = [c for c in colunas if c in resultado.columns]

    print(resultado[colunas])

    print("\nArquivo de diversificação salvo:")
    print(OUTPUT_FILE)

    return resultado


if __name__ == "__main__":
    analisar_diversificacao()
