# ============================================================
# correlation_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Correlation Engine Institucional
# Parte 1 - Matriz de Correlação
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/carteira_diversificada.csv")

OUTPUT_MATRIX = Path("output/correlation_matrix.csv")
OUTPUT_SUMMARY = Path("output/correlation_summary.csv")


PERIODO = "3y"


def carregar_carteira():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

    df.columns = [str(c).strip() for c in df.columns]

    if "ticker" not in df.columns:
        raise ValueError("ticker não encontrado.")

    return df


def yahoo(ticker):

    ticker = str(ticker).upper().strip()

    if ticker.endswith(".SA"):
        return ticker

    return f"{ticker}.SA"


def baixar_precos(lista):

    dados = yf.download(
        lista,
        period=PERIODO,
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if isinstance(dados.columns, pd.MultiIndex):
        dados = dados["Close"]

    return dados


def resumo_correlacao(corr):

    ativos = corr.columns.tolist()

    pares = []

    for i in range(len(ativos)):
        for j in range(i + 1, len(ativos)):

            valor = corr.iloc[i, j]

            if np.isnan(valor):
                continue

            pares.append({

                "ativo_1": ativos[i],
                "ativo_2": ativos[j],
                "correlacao": float(valor)

            })

    pares = pd.DataFrame(pares)

    pares["correlacao_abs"] = pares["correlacao"].abs()

    maior = pares.sort_values(
        "correlacao_abs",
        ascending=False
    ).iloc[0]

    menor = pares.sort_values(
        "correlacao_abs"
    ).iloc[0]

    media = pares["correlacao_abs"].mean()

    return pares, maior, menor, media


def classificar(media):

    if media >= 0.80:
        return "MUITO ALTA"

    if media >= 0.60:
        return "ALTA"

    if media >= 0.40:
        return "MODERADA"

    if media >= 0.20:
        return "BAIXA"

    return "MUITO BAIXA"


def executar_correlation_engine():

    print("=" * 70)
    print("CORRELATION ENGINE V1")
    print("=" * 70)

    carteira = carregar_carteira()

    tickers = [
        yahoo(t)
        for t in carteira["ticker"]
    ]

    print()

    print("Baixando preços...")

    precos = baixar_precos(tickers)

    retornos = precos.pct_change().dropna()

    corr = retornos.corr()

    pares, maior, menor, media = resumo_correlacao(corr)

    resumo = pd.DataFrame([{

        "ativos": len(corr),

        "correlacao_media": media,

        "classificacao": classificar(media),

        "maior_correlacao":

            f"{maior['ativo_1']} x {maior['ativo_2']}",

        "valor_maior":

            maior["correlacao"],

        "menor_correlacao":

            f"{menor['ativo_1']} x {menor['ativo_2']}",

        "valor_menor":

            menor["correlacao"]

    }])

    Path("output").mkdir(exist_ok=True)

    corr.to_csv(
        OUTPUT_MATRIX,
        encoding="utf-8-sig"
    )

    resumo.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig"
    )

    print()

    print("=" * 70)
    print("RESUMO")
    print("=" * 70)

    print(resumo.to_string(index=False))

    print()

    print("Arquivos gerados:")

    print(OUTPUT_MATRIX)

    print(OUTPUT_SUMMARY)

    return corr


if __name__ == "__main__":

    executar_correlation_engine()
