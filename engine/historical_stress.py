# ============================================================
# historical_stress.py
# B3 FUNDAMENTALISTA ENGINE
# Historical Stress Engine — V1 Institucional
# ============================================================

from pathlib import Path
import contextlib
import io

import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/carteira_diversificada.csv")
OUTPUT_FILE = Path("output/historical_stress.csv")
COVERAGE_FILE = Path("output/historical_stress_coverage.csv")


CENARIOS_HISTORICOS = {
    "crise_2008": ("2008-05-01", "2008-12-31"),
    "covid_2020": ("2020-02-01", "2020-04-30"),
    "juros_altos_2021_2022": ("2021-01-01", "2022-12-31"),
}


def ticker_yahoo(ticker):
    ticker = str(ticker).upper().strip()
    return ticker if ticker.endswith(".SA") else f"{ticker}.SA"


def carregar_carteira():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    if "ticker" not in df.columns:
        raise ValueError("Coluna ticker não encontrada em carteira_diversificada.csv")

    return df


def baixar_historico(ticker, inicio, fim):
    try:
        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            dados = yf.download(
                ticker_yahoo(ticker),
                start=inicio,
                end=fim,
                progress=False,
                auto_adjust=True,
                threads=False,
            )

        if dados is None or dados.empty:
            return pd.Series(dtype=float)

        if isinstance(dados.columns, pd.MultiIndex):
            if "Close" in dados.columns.get_level_values(0):
                close = dados["Close"]
            elif "Close" in dados.columns.get_level_values(-1):
                close = dados.xs("Close", axis=1, level=-1)
            else:
                return pd.Series(dtype=float)

            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]

        elif "Close" in dados.columns:
            close = dados["Close"]

            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
        else:
            return pd.Series(dtype=float)

        close = pd.to_numeric(close, errors="coerce").dropna()

        return close

    except Exception:
        return pd.Series(dtype=float)


def calcular_drawdown(precos):
    if precos is None or precos.empty or len(precos) < 20:
        return None

    topo = precos.cummax()
    drawdown = (precos / topo) - 1
    pior = drawdown.min() * 100

    if pd.isna(pior):
        return None

    return float(pior)


def classificar_fonte(precos):
    if precos is None or precos.empty:
        return "SEM_HISTORICO"

    if len(precos) < 20:
        return "HISTORICO_INSUFICIENTE"

    return "HISTORICO_REAL"


def calcular_ativo(ticker):
    resultado = {"ticker": str(ticker).upper().strip()}

    for nome, (inicio, fim) in CENARIOS_HISTORICOS.items():
        precos = baixar_historico(ticker, inicio, fim)
        fonte = classificar_fonte(precos)
        drawdown = calcular_drawdown(precos)

        resultado[f"{nome}_drawdown_pct"] = drawdown
        resultado[f"{nome}_fonte"] = fonte
        resultado[f"{nome}_qtd_pregoes"] = int(len(precos)) if precos is not None else 0

    return resultado


def classificar_confiabilidade(cobertura_pct):
    if cobertura_pct >= 80:
        return "ALTA"
    if cobertura_pct >= 50:
        return "MODERADA"
    if cobertura_pct > 0:
        return "BAIXA"
    return "SEM BASE HISTÓRICA"


def gerar_cobertura(df_resultado):
    linhas = []

    total = len(df_resultado)

    for nome in CENARIOS_HISTORICOS:
        fonte_col = f"{nome}_fonte"
        dd_col = f"{nome}_drawdown_pct"

        com_historico = int((df_resultado[fonte_col] == "HISTORICO_REAL").sum())
        sem_historico = total - com_historico
        cobertura = (com_historico / total * 100) if total else 0

        perdas = pd.to_numeric(df_resultado[dd_col], errors="coerce").dropna()

        linhas.append({
            "cenario": nome,
            "ativos_total": total,
            "ativos_com_historico": com_historico,
            "ativos_sem_historico": sem_historico,
            "cobertura_historica_pct": cobertura,
            "drawdown_medio_ativos_pct": float(perdas.mean()) if not perdas.empty else None,
            "drawdown_mediano_ativos_pct": float(perdas.median()) if not perdas.empty else None,
            "pior_drawdown_ativo_pct": float(perdas.min()) if not perdas.empty else None,
            "confiabilidade_cenario": classificar_confiabilidade(cobertura),
        })

    return pd.DataFrame(linhas)


def gerar_historical_stress():
    carteira = carregar_carteira()

    tickers = (
        carteira["ticker"]
        .dropna()
        .astype(str)
        .str.upper()
        .str.strip()
        .drop_duplicates()
        .tolist()
    )

    print("=" * 70)
    print("HISTORICAL STRESS ENGINE V1 INSTITUCIONAL")
    print("=" * 70)

    resultados = []

    for ticker in tickers:
        print(f"Calculando stress histórico: {ticker}")
        resultados.append(calcular_ativo(ticker))

    df_resultado = pd.DataFrame(resultados)
    cobertura = gerar_cobertura(df_resultado)

    Path("output").mkdir(exist_ok=True)

    df_resultado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    cobertura.to_csv(
        COVERAGE_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("COBERTURA HISTÓRICA:")
    print(cobertura.to_string(index=False))

    print()
    print("Arquivos salvos:")
    print(OUTPUT_FILE)
    print(COVERAGE_FILE)

    return df_resultado


if __name__ == "__main__":
    gerar_historical_stress()
