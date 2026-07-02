# ============================================================
# historical_stress.py
# B3 FUNDAMENTALISTA ENGINE
# Stress histórico real por ativo
# ============================================================

from pathlib import Path
import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/carteira_diversificada.csv")
OUTPUT_FILE = Path("output/historical_stress.csv")


CENARIOS_HISTORICOS = {
    "crise_2008": {
        "inicio": "2008-05-01",
        "fim": "2008-12-31",
    },
    "covid_2020": {
        "inicio": "2020-02-01",
        "fim": "2020-04-30",
    },
    "juros_altos_2021_2022": {
        "inicio": "2021-01-01",
        "fim": "2022-12-31",
    },
}


def carregar_carteira():
    if not INPUT_FILE.exists():
        print(f"Arquivo não encontrado: {INPUT_FILE}")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def ticker_yahoo(ticker):
    ticker = str(ticker).upper().strip()

    if ticker.endswith(".SA"):
        return ticker

    return f"{ticker}.SA"


def calcular_drawdown_periodo(precos):
    if precos.empty:
        return None

    precos = precos.dropna()

    if len(precos) < 20:
        return None

    topo_acumulado = precos.cummax()
    drawdown = (precos / topo_acumulado) - 1

    pior_drawdown = drawdown.min() * 100

    return float(pior_drawdown)


def baixar_precos(ticker, inicio, fim):
    try:
        dados = yf.download(
            ticker_yahoo(ticker),
            start=inicio,
            end=fim,
            progress=False,
            auto_adjust=True,
            threads=False,
        )

        if dados.empty:
            return pd.Series(dtype=float)

        if "Close" in dados.columns:
            return dados["Close"]

        return pd.Series(dtype=float)

    except Exception as erro:
        print(f"Erro ao baixar {ticker}: {erro}")
        return pd.Series(dtype=float)


def calcular_stress_historico_ativo(ticker):
    resultado = {
        "ticker": ticker,
    }

    for nome_cenario, config in CENARIOS_HISTORICOS.items():
        inicio = config["inicio"]
        fim = config["fim"]

        precos = baixar_precos(ticker, inicio, fim)

        drawdown = calcular_drawdown_periodo(precos)

        if drawdown is None:
            resultado[f"{nome_cenario}_drawdown_pct"] = None
            resultado[f"{nome_cenario}_fonte"] = "SEM_HISTORICO"
        else:
            resultado[f"{nome_cenario}_drawdown_pct"] = drawdown
            resultado[f"{nome_cenario}_fonte"] = "HISTORICO_REAL"

    return resultado


def gerar_historical_stress():
    carteira = carregar_carteira()

    if carteira.empty:
        print("Carteira vazia. Historical stress não executado.")
        return pd.DataFrame()

    if "ticker" not in carteira.columns:
        raise ValueError("Coluna ticker não encontrada em carteira_diversificada.csv")

    tickers = (
        carteira["ticker"]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    resultados = []

    print("=" * 70)
    print("HISTORICAL STRESS ENGINE")
    print("=" * 70)

    for ticker in tickers:
        print(f"Calculando stress histórico: {ticker}")
        resultados.append(calcular_stress_historico_ativo(ticker))

    df_resultado = pd.DataFrame(resultados)

    Path("output").mkdir(exist_ok=True)

    df_resultado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 70)
    print("HISTORICAL STRESS FINALIZADO")
    print("=" * 70)
    print(OUTPUT_FILE)

    print()
    print(df_resultado)

    return df_resultado


if __name__ == "__main__":
    gerar_historical_stress()
