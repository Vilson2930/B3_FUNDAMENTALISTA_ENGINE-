# ============================================================
# technical_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Camada Técnica Independente — TOP 20 Premium
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf


INPUT_FILE = Path("output/top20_premium.csv")
OUTPUT_FILE = Path("output/top20_tecnico.csv")


def carregar_top20():
    if not INPUT_FILE.exists():
        print("Arquivo top20_premium.csv não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE)

    if "ticker" not in df.columns:
        print("Coluna ticker não encontrada.")
        return pd.DataFrame()

    return df.head(20)


def baixar_precos(ticker):
    ticker_yahoo = f"{ticker}.SA"

    try:
        df = yf.download(
            ticker_yahoo,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            timeout=20
        )
    except Exception as erro:
        print(f"{ticker}: erro no download - {erro}")
        return pd.DataFrame()

    if df.empty:
        print(f"{ticker}: sem dados.")
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    return df


def calcular_rsi(close, periodo=14):
    delta = close.diff()

    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.rolling(periodo).mean()
    media_perda = perda.rolling(periodo).mean()

    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calcular_macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    sinal = macd.ewm(span=9, adjust=False).mean()
    histograma = macd - sinal

    return macd, sinal, histograma


def calcular_tecnicos(df):
    df = df.copy()

    if "Close" not in df.columns or "Volume" not in df.columns:
        return pd.DataFrame()

    close = df["Close"]
    volume = df["Volume"]

    df["mm20"] = close.rolling(20).mean()
    df["mm50"] = close.rolling(50).mean()
    df["mm200"] = close.rolling(200).mean()

    df["rsi14"] = calcular_rsi(close)

    macd, sinal, hist = calcular_macd(close)
    df["macd"] = macd
    df["macd_sinal"] = sinal
    df["macd_hist"] = hist

    df["retorno_20d"] = close.pct_change(20)
    df["dist_mm200"] = (close / df["mm200"]) - 1

    df["volume_medio_20d"] = volume.rolling(20).mean()
    df["volume_forca"] = volume / df["volume_medio_20d"]

    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    return df


def calcular_score_tecnico(row):
    score = 0

    preco = row.get("Close", np.nan)
    mm20 = row.get("mm20", np.nan)
    mm50 = row.get("mm50", np.nan)
    mm200 = row.get("mm200", np.nan)
    rsi = row.get("rsi14", np.nan)
    macd = row.get("macd", np.nan)
    macd_sinal = row.get("macd_sinal", np.nan)
    retorno_20d = row.get("retorno_20d", np.nan)
    dist_mm200 = row.get("dist_mm200", np.nan)
    volume_forca = row.get("volume_forca", np.nan)

    if pd.notna(preco) and pd.notna(mm200) and preco > mm200:
        score += 20

    if pd.notna(preco) and pd.notna(mm50) and preco > mm50:
        score += 15

    if pd.notna(mm20) and pd.notna(mm50) and mm20 > mm50:
        score += 15

    if pd.notna(rsi) and 45 <= rsi <= 65:
        score += 15
    elif pd.notna(rsi) and 35 <= rsi < 45:
        score += 8

    if pd.notna(macd) and pd.notna(macd_sinal) and macd > macd_sinal:
        score += 15

    if pd.notna(retorno_20d) and retorno_20d > 0:
        score += 10

    if pd.notna(dist_mm200) and -0.05 <= dist_mm200 <= 0.20:
        score += 5

    if pd.notna(volume_forca) and volume_forca >= 1:
        score += 5

    return score


def classificar_sinal(score):
    if score >= 80:
        return "COMPRA FORTE"
    if score >= 65:
        return "COMPRA"
    if score >= 50:
        return "AGUARDAR"
    if score >= 35:
        return "FRACO"
    return "EVITAR"


def analisar_top20():
    top20 = carregar_top20()

    if top20.empty:
        print("Nenhuma ação para análise técnica.")
        return pd.DataFrame()

    resultados = []

    for _, empresa in top20.iterrows():
        ticker = empresa["ticker"]

        print(f"Analisando técnico: {ticker}")

        precos = baixar_precos(ticker)

        if precos.empty or len(precos) < 200:
            print(f"{ticker}: dados insuficientes.")
            continue

        precos = calcular_tecnicos(precos)

        if precos.empty:
            print(f"{ticker}: falha nos indicadores.")
            continue

        ultima = precos.iloc[-1]
        score_tecnico = calcular_score_tecnico(ultima)

        resultados.append({
            "ticker": ticker,
            "empresa": empresa.get("empresa", ""),
            "score_fundamental": empresa.get("score_balanceado", np.nan),
            "rating": empresa.get("rating", ""),
            "moat_score": empresa.get("moat_score", np.nan),
            "preco": ultima.get("Close", np.nan),
            "mm20": ultima.get("mm20", np.nan),
            "mm50": ultima.get("mm50", np.nan),
            "mm200": ultima.get("mm200", np.nan),
            "rsi14": ultima.get("rsi14", np.nan),
            "macd": ultima.get("macd", np.nan),
            "macd_sinal": ultima.get("macd_sinal", np.nan),
            "retorno_20d": ultima.get("retorno_20d", np.nan),
            "dist_mm200": ultima.get("dist_mm200", np.nan),
            "volume_forca": ultima.get("volume_forca", np.nan),
            "score_tecnico": score_tecnico,
            "sinal_tecnico": classificar_sinal(score_tecnico),
        })

    resultado = pd.DataFrame(resultados)

    if resultado.empty:
        print("Nenhum resultado técnico gerado.")
        return resultado

    resultado["score_final"] = (
        resultado["score_fundamental"].fillna(50) * 0.70 +
        resultado["score_tecnico"].fillna(50) * 0.30
    )

    resultado = resultado.sort_values(
        ["score_final", "score_tecnico"],
        ascending=False
    ).reset_index(drop=True)

    Path("output").mkdir(exist_ok=True)

    resultado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArquivo técnico salvo:")
    print(OUTPUT_FILE)

    return resultado


if __name__ == "__main__":
    analisar_top20()
