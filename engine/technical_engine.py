# ============================================================
# technical_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Análise Técnica das TOP 20 ações premium
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/top20_premium.csv")
OUTPUT_FILE = Path("output/top20_entrada_tecnica.csv")


def carregar_top20():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "Arquivo output/top20_premium.csv não encontrado. "
            "Execute primeiro o motor fundamentalista."
        )

    df = pd.read_csv(INPUT_FILE)

    if "ticker" not in df.columns:
        raise ValueError("Coluna 'ticker' não encontrada no top20_premium.csv")

    return df


def baixar_precos(ticker, periodo="1y"):
    ticker_yahoo = f"{ticker}.SA"

    df = yf.download(
        ticker_yahoo,
        period=periodo,
        interval="1d",
        auto_adjust=True,
        progress=False
    )

    if df.empty:
        return pd.DataFrame()

    # Corrige MultiIndex do yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    return df


def garantir_serie(df, coluna):
    dado = df[coluna]

    if isinstance(dado, pd.DataFrame):
        return dado.iloc[:, 0]

    return dado


def calcular_indicadores_tecnicos(df):
    df = df.copy()

    if "Close" not in df.columns or "Volume" not in df.columns:
        return pd.DataFrame()

    close = garantir_serie(df, "Close")
    volume = garantir_serie(df, "Volume")

    df["close_ajustado"] = close
    df["volume_ajustado"] = volume

    df["mm21"] = close.rolling(21).mean()
    df["mm50"] = close.rolling(50).mean()
    df["mm200"] = close.rolling(200).mean()

    delta = close.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.rolling(14).mean()
    media_perda = perda.rolling(14).mean()

    rs = media_ganho / media_perda
    df["rsi14"] = 100 - (100 / (1 + rs))

    df["retorno_20d"] = close.pct_change(20)
    df["dist_mm200"] = (close / df["mm200"]) - 1

    df["volume_medio_20d"] = volume.rolling(20).mean()
    df["volume_forca"] = volume / df["volume_medio_20d"]

    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    return df


def calcular_entry_score(linha):
    score = 0

    preco = linha.get("close_ajustado", np.nan)
    mm21 = linha.get("mm21", np.nan)
    mm50 = linha.get("mm50", np.nan)
    mm200 = linha.get("mm200", np.nan)
    rsi = linha.get("rsi14", np.nan)
    retorno_20d = linha.get("retorno_20d", np.nan)
    dist_mm200 = linha.get("dist_mm200", np.nan)
    volume_forca = linha.get("volume_forca", np.nan)

    if pd.notna(preco) and pd.notna(mm200) and preco > mm200:
        score += 25

    if pd.notna(preco) and pd.notna(mm50) and preco > mm50:
        score += 20

    if pd.notna(mm21) and pd.notna(mm50) and mm21 > mm50:
        score += 15

    if pd.notna(rsi) and 45 <= rsi <= 65:
        score += 15
    elif pd.notna(rsi) and 35 <= rsi < 45:
        score += 10

    if pd.notna(retorno_20d) and retorno_20d > 0:
        score += 10

    if pd.notna(dist_mm200) and -0.05 <= dist_mm200 <= 0.20:
        score += 10

    if pd.notna(volume_forca) and volume_forca >= 1:
        score += 5

    return score


def classificar_entrada(score):
    if score >= 85:
        return "COMPRA FORTE"
    elif score >= 70:
        return "COMPRA"
    elif score >= 55:
        return "AGUARDAR"
    elif score >= 40:
        return "FRACO"
    else:
        return "EVITAR"


def analisar_top20():
    top20 = carregar_top20()
    resultados = []

    for _, empresa in top20.head(20).iterrows():
        ticker = empresa["ticker"]

        print(f"Analisando {ticker}...")

        precos = baixar_precos(ticker)

        if precos.empty or len(precos) < 200:
            print(f"{ticker}: dados insuficientes.")
            continue

        precos = calcular_indicadores_tecnicos(precos)

        if precos.empty:
            print(f"{ticker}: erro ao calcular indicadores técnicos.")
            continue

        ultima = precos.iloc[-1].copy()
        entry_score = calcular_entry_score(ultima)

        resultados.append({
            "ticker": ticker,
            "empresa": empresa.get("empresa", ""),
            "score_balanceado": empresa.get("score_balanceado", np.nan),
            "moat_score": empresa.get("moat_score", np.nan),
            "rating": empresa.get("rating", ""),
            "preco": ultima.get("close_ajustado", np.nan),
            "mm21": ultima.get("mm21", np.nan),
            "mm50": ultima.get("mm50", np.nan),
            "mm200": ultima.get("mm200", np.nan),
            "rsi14": ultima.get("rsi14", np.nan),
            "retorno_20d": ultima.get("retorno_20d", np.nan),
            "dist_mm200": ultima.get("dist_mm200", np.nan),
            "volume_forca": ultima.get("volume_forca", np.nan),
            "entry_score": entry_score,
            "sinal_tecnico": classificar_entrada(entry_score)
        })

    df_resultado = pd.DataFrame(resultados)

    if df_resultado.empty:
        print("Nenhum resultado técnico gerado.")
        return df_resultado

    df_resultado = df_resultado.sort_values(
        ["entry_score", "score_balanceado"],
        ascending=False
    )

    Path("output").mkdir(exist_ok=True)

    df_resultado.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("=" * 80)
    print("TOP 20 — ANÁLISE TÉCNICA")
    print("=" * 80)

    print(
        df_resultado[
            [
                "ticker",
                "entry_score",
                "sinal_tecnico",
                "rsi14",
                "dist_mm200",
                "retorno_20d"
            ]
        ].head(20)
    )

    print(f"\nArquivo salvo: {OUTPUT_FILE}")

    return df_resultado


if __name__ == "__main__":
    analisar_top20()
