# ============================================================
# technical_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Análise Técnica Institucional — Download em Lote
# ============================================================

from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/top20_premium.csv")
OUTPUT_FILE = Path("output/top20_tecnico.csv")


def carregar_top20():
    if not INPUT_FILE.exists():
        print("Arquivo output/top20_premium.csv não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE)

    if "ticker" not in df.columns:
        print("Coluna ticker não encontrada em top20_premium.csv.")
        return pd.DataFrame()

    return df.head(20).copy()


def preparar_tickers(top20):
    tickers = []

    for ticker in top20["ticker"].dropna().unique():
        ticker = str(ticker).strip().upper()

        if not ticker.endswith(".SA"):
            ticker = f"{ticker}.SA"

        tickers.append(ticker)

    return tickers


def baixar_precos_lote(tickers):
    if not tickers:
        return pd.DataFrame()

    try:
        return yf.download(
            tickers=tickers,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by="ticker",
            timeout=30
        )

    except Exception as erro:
        print(f"Erro ao baixar dados em lote: {erro}")
        return pd.DataFrame()


def extrair_dados_ticker(dados, ticker_yahoo):
    if dados.empty:
        return pd.DataFrame()

    try:
        if isinstance(dados.columns, pd.MultiIndex):
            if ticker_yahoo not in dados.columns.get_level_values(0):
                return pd.DataFrame()

            df = dados[ticker_yahoo].copy()
        else:
            df = dados.copy()

        df = df.dropna(how="all")

        if df.empty:
            return pd.DataFrame()

        return df.reset_index()

    except Exception:
        return pd.DataFrame()


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
    macd_sinal = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_sinal

    return macd, macd_sinal, macd_hist


def calcular_atr(df, periodo=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    fechamento_anterior = close.shift(1)

    tr1 = high - low
    tr2 = (high - fechamento_anterior).abs()
    tr3 = (low - fechamento_anterior).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    return true_range.rolling(periodo).mean()


def calcular_indicadores(df):
    df = df.copy()

    obrigatorias = ["Close", "High", "Low", "Volume"]

    for coluna in obrigatorias:
        if coluna not in df.columns:
            return pd.DataFrame()

    close = df["Close"]
    volume = df["Volume"]

    df["mm20"] = close.rolling(20).mean()
    df["mm50"] = close.rolling(50).mean()
    df["mm200"] = close.rolling(200).mean()

    df["rsi14"] = calcular_rsi(close)

    macd, macd_sinal, macd_hist = calcular_macd(close)

    df["macd"] = macd
    df["macd_sinal"] = macd_sinal
    df["macd_hist"] = macd_hist

    df["atr14"] = calcular_atr(df)

    df["retorno_20d"] = close.pct_change(20)
    df["retorno_60d"] = close.pct_change(60)

    df["dist_mm20"] = (close / df["mm20"]) - 1
    df["dist_mm50"] = (close / df["mm50"]) - 1
    df["dist_mm200"] = (close / df["mm200"]) - 1

    df["volume_medio_20d"] = volume.rolling(20).mean()
    df["volume_forca"] = volume / df["volume_medio_20d"]

    df["atr_pct"] = df["atr14"] / close

    df["tendencia_alta"] = (
        (close > df["mm200"]) &
        (df["mm50"] > df["mm200"])
    )

    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    return df


def score_tendencia(row):
    score = 0

    preco = row.get("Close", np.nan)
    mm20 = row.get("mm20", np.nan)
    mm50 = row.get("mm50", np.nan)
    mm200 = row.get("mm200", np.nan)

    if pd.notna(preco) and pd.notna(mm200) and preco > mm200:
        score += 35

    if pd.notna(mm50) and pd.notna(mm200) and mm50 > mm200:
        score += 30

    if pd.notna(mm20) and pd.notna(mm50) and mm20 > mm50:
        score += 20

    if pd.notna(preco) and pd.notna(mm20) and preco > mm20:
        score += 15

    return min(score, 100)


def score_entrada(row):
    score = 0

    rsi = row.get("rsi14", np.nan)
    dist_mm200 = row.get("dist_mm200", np.nan)
    dist_mm20 = row.get("dist_mm20", np.nan)

    if pd.notna(rsi):
        if 45 <= rsi <= 60:
            score += 40
        elif 40 <= rsi < 45:
            score += 30
        elif 60 < rsi <= 70:
            score += 25
        elif 35 <= rsi < 40:
            score += 15
        elif 70 < rsi <= 75:
            score += 10

    if pd.notna(dist_mm200):
        if -0.05 <= dist_mm200 <= 0.15:
            score += 35
        elif 0.15 < dist_mm200 <= 0.30:
            score += 20
        elif -0.15 <= dist_mm200 < -0.05:
            score += 15

    if pd.notna(dist_mm20):
        if -0.03 <= dist_mm20 <= 0.05:
            score += 25
        elif 0.05 < dist_mm20 <= 0.10:
            score += 10

    return min(score, 100)


def score_momentum(row):
    score = 0

    macd = row.get("macd", np.nan)
    macd_sinal = row.get("macd_sinal", np.nan)
    macd_hist = row.get("macd_hist", np.nan)
    retorno_20d = row.get("retorno_20d", np.nan)
    retorno_60d = row.get("retorno_60d", np.nan)

    if pd.notna(macd) and pd.notna(macd_sinal) and macd > macd_sinal:
        score += 30

    if pd.notna(macd_hist) and macd_hist > 0:
        score += 20

    if pd.notna(retorno_20d):
        if retorno_20d > 0:
            score += 25
        if retorno_20d > 0.05:
            score += 10

    if pd.notna(retorno_60d) and retorno_60d > 0:
        score += 15

    return min(score, 100)


def score_volume(row):
    volume_forca = row.get("volume_forca", np.nan)

    if pd.isna(volume_forca):
        return 50

    if volume_forca >= 1.5:
        return 100

    if volume_forca >= 1.2:
        return 80

    if volume_forca >= 1.0:
        return 65

    if volume_forca >= 0.8:
        return 50

    return 30


def score_risco(row):
    atr_pct = row.get("atr_pct", np.nan)

    if pd.isna(atr_pct):
        return 50

    if atr_pct <= 0.025:
        return 100

    if atr_pct <= 0.04:
        return 80

    if atr_pct <= 0.06:
        return 60

    if atr_pct <= 0.08:
        return 40

    return 20


def calcular_score_tecnico(row):
    tendencia = score_tendencia(row)
    entrada = score_entrada(row)
    momentum = score_momentum(row)
    volume = score_volume(row)
    risco = score_risco(row)

    score = (
        tendencia * 0.30 +
        entrada * 0.25 +
        momentum * 0.25 +
        volume * 0.10 +
        risco * 0.10
    )

    return round(min(score, 100), 2)


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

    tickers_yahoo = preparar_tickers(top20)

    print("Baixando dados técnicos em lote...")
    print(", ".join(tickers_yahoo))

    dados = baixar_precos_lote(tickers_yahoo)

    if dados.empty:
        print("Nenhum dado técnico foi baixado.")
        return pd.DataFrame()

    resultados = []

    for _, empresa in top20.iterrows():
        ticker_original = str(empresa["ticker"]).strip().upper()
        ticker_yahoo = (
            ticker_original
            if ticker_original.endswith(".SA")
            else f"{ticker_original}.SA"
        )

        print(f"Calculando técnico: {ticker_original}")

        df_ticker = extrair_dados_ticker(dados, ticker_yahoo)

        if df_ticker.empty or len(df_ticker) < 200:
            print(f"{ticker_original}: dados insuficientes.")
            continue

        df_ticker = calcular_indicadores(df_ticker)

        if df_ticker.empty:
            print(f"{ticker_original}: falha nos indicadores.")
            continue

        ultima = df_ticker.iloc[-1]

        score_tecnico = calcular_score_tecnico(ultima)

        resultados.append({
            "ticker": ticker_original,
            "empresa": empresa.get("empresa", ""),
            "setor": empresa.get("setor", ""),
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
            "macd_hist": ultima.get("macd_hist", np.nan),
            "atr14": ultima.get("atr14", np.nan),
            "atr_pct": ultima.get("atr_pct", np.nan),
            "retorno_20d": ultima.get("retorno_20d", np.nan),
            "retorno_60d": ultima.get("retorno_60d", np.nan),
            "dist_mm20": ultima.get("dist_mm20", np.nan),
            "dist_mm50": ultima.get("dist_mm50", np.nan),
            "dist_mm200": ultima.get("dist_mm200", np.nan),
            "volume_forca": ultima.get("volume_forca", np.nan),
            "tendencia_alta": ultima.get("tendencia_alta", False),

            "score_tendencia": score_tendencia(ultima),
            "score_entrada": score_entrada(ultima),
            "score_momentum": score_momentum(ultima),
            "score_volume": score_volume(ultima),
            "score_risco": score_risco(ultima),

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

    print("Arquivo técnico salvo:")
    print(OUTPUT_FILE)

    return resultado
