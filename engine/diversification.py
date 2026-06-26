# ============================================================
# diversification.py
# B3 FUNDAMENTALISTA ENGINE
# Diversificação setorial independente
# ============================================================

from pathlib import Path
import pandas as pd


INPUT_FILE = Path("output/top20_premium.csv")
OUTPUT_FILE = Path("output/top20_diversificado.csv")


def carregar_top20():
    if not INPUT_FILE.exists():
        print("Arquivo top20_premium.csv não encontrado.")
        return pd.DataFrame()

    return pd.read_csv(INPUT_FILE)


def diversificar_por_setor(
    df,
    score_col="score_balanceado",
    setor_col="setor",
    top_n=20,
    limite_por_setor=2
):
    if df.empty:
        return df

    df = df.copy()

    if setor_col not in df.columns:
        df[setor_col] = "SEM SETOR"

    df[setor_col] = df[setor_col].fillna("SEM SETOR")

    df = df.sort_values(
        score_col,
        ascending=False
    )

    selecionadas = []
    contador_setor = {}

    for _, row in df.iterrows():
        setor = row[setor_col]

        contador_setor[setor] = contador_setor.get(setor, 0)

        if contador_setor[setor] >= limite_por_setor:
            continue

        selecionadas.append(row)
        contador_setor[setor] += 1

        if len(selecionadas) >= top_n:
            break

    return pd.DataFrame(selecionadas).reset_index(drop=True)


def analisar_diversificacao():
    df = carregar_top20()

    if df.empty:
        print("Nenhuma empresa para diversificar.")
        return df

    resultado = diversificar_por_setor(
        df,
        score_col="score_balanceado",
        setor_col="setor",
        top_n=20,
        limite_por_setor=2
    )

    Path("output").mkdir(exist_ok=True)

    resultado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("Arquivo de diversificação salvo:")
    print(OUTPUT_FILE)

    return resultado


if __name__ == "__main__":
    analisar_diversificacao()
