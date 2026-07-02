# ============================================================
# historical_stress.py
# B3 FUNDAMENTALISTA ENGINE
# Historical Stress Engine — V2 Institucional
# Stress real + cobertura histórica + comparação com IBOV
# ============================================================

from pathlib import Path
import contextlib
import io

import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/carteira_diversificada.csv")
OUTPUT_FILE = Path("output/historical_stress.csv")
COVERAGE_FILE = Path("output/historical_stress_coverage.csv")
BENCHMARK_FILE = Path("output/historical_stress_benchmark.csv")

BENCHMARK_TICKER = "^BVSP"


CENARIOS_HISTORICOS = {
    "crise_2008": ("2008-05-01", "2008-12-31"),
    "covid_2020": ("2020-02-01", "2020-04-30"),
    "juros_altos_2021_2022": ("2021-01-01", "2022-12-31"),
}


def ticker_yahoo(ticker):
    ticker = str(ticker).upper().strip()
    return ticker if ticker.endswith(".SA") or ticker.startswith("^") else f"{ticker}.SA"


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

        return pd.to_numeric(close, errors="coerce").dropna()

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


def calcular_retorno_periodo(precos):
    if precos is None or precos.empty or len(precos) < 2:
        return None

    retorno = (precos.iloc[-1] / precos.iloc[0] - 1) * 100

    if pd.isna(retorno):
        return None

    return float(retorno)


def calcular_volatilidade(precos):
    if precos is None or precos.empty or len(precos) < 20:
        return None

    retornos = precos.pct_change().dropna()

    if retornos.empty:
        return None

    return float(retornos.std() * (252 ** 0.5) * 100)


def calcular_beta_correlacao(precos_ativo, precos_benchmark):
    if (
        precos_ativo is None or precos_ativo.empty or
        precos_benchmark is None or precos_benchmark.empty
    ):
        return None, None

    df = pd.concat(
        [
            precos_ativo.rename("ativo"),
            precos_benchmark.rename("benchmark")
        ],
        axis=1
    ).dropna()

    if len(df) < 20:
        return None, None

    retornos = df.pct_change().dropna()

    if retornos.empty or retornos["benchmark"].var() == 0:
        return None, None

    beta = retornos["ativo"].cov(retornos["benchmark"]) / retornos["benchmark"].var()
    correlacao = retornos["ativo"].corr(retornos["benchmark"])

    return float(beta), float(correlacao)


def classificar_fonte(precos):
    if precos is None or precos.empty:
        return "SEM_HISTORICO"

    if len(precos) < 20:
        return "HISTORICO_INSUFICIENTE"

    return "HISTORICO_REAL"


def calcular_ativo(ticker, benchmarks):
    resultado = {"ticker": str(ticker).upper().strip()}

    for nome, (inicio, fim) in CENARIOS_HISTORICOS.items():
        precos = baixar_historico(ticker, inicio, fim)
        benchmark = benchmarks.get(nome, pd.Series(dtype=float))

        fonte = classificar_fonte(precos)
        drawdown = calcular_drawdown(precos)
        retorno = calcular_retorno_periodo(precos)
        volatilidade = calcular_volatilidade(precos)
        beta, correlacao = calcular_beta_correlacao(precos, benchmark)

        resultado[f"{nome}_drawdown_pct"] = drawdown
        resultado[f"{nome}_retorno_periodo_pct"] = retorno
        resultado[f"{nome}_volatilidade_anualizada_pct"] = volatilidade
        resultado[f"{nome}_beta_ibov"] = beta
        resultado[f"{nome}_correlacao_ibov"] = correlacao
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


def gerar_benchmark():
    linhas = []
    benchmarks = {}

    for nome, (inicio, fim) in CENARIOS_HISTORICOS.items():
        precos = baixar_historico(BENCHMARK_TICKER, inicio, fim)

        benchmarks[nome] = precos

        linhas.append({
            "cenario": nome,
            "benchmark": "IBOV",
            "drawdown_benchmark_pct": calcular_drawdown(precos),
            "retorno_benchmark_pct": calcular_retorno_periodo(precos),
            "volatilidade_benchmark_pct": calcular_volatilidade(precos),
            "qtd_pregoes_benchmark": int(len(precos)) if precos is not None else 0,
            "fonte_benchmark": classificar_fonte(precos),
        })

    benchmark_df = pd.DataFrame(linhas)

    return benchmarks, benchmark_df


def gerar_cobertura(df_resultado):
    linhas = []
    total = len(df_resultado)

    for nome in CENARIOS_HISTORICOS:
        fonte_col = f"{nome}_fonte"
        dd_col = f"{nome}_drawdown_pct"
        beta_col = f"{nome}_beta_ibov"
        corr_col = f"{nome}_correlacao_ibov"

        com_historico = int((df_resultado[fonte_col] == "HISTORICO_REAL").sum())
        sem_historico = total - com_historico
        cobertura = (com_historico / total * 100) if total else 0

        perdas = pd.to_numeric(df_resultado[dd_col], errors="coerce").dropna()
        betas = pd.to_numeric(df_resultado[beta_col], errors="coerce").dropna()
        corrs = pd.to_numeric(df_resultado[corr_col], errors="coerce").dropna()

        linhas.append({
            "cenario": nome,
            "ativos_total": total,
            "ativos_com_historico": com_historico,
            "ativos_sem_historico": sem_historico,
            "cobertura_historica_pct": cobertura,
            "drawdown_medio_ativos_pct": float(perdas.mean()) if not perdas.empty else None,
            "drawdown_mediano_ativos_pct": float(perdas.median()) if not perdas.empty else None,
            "pior_drawdown_ativo_pct": float(perdas.min()) if not perdas.empty else None,
            "beta_medio_ibov": float(betas.mean()) if not betas.empty else None,
            "correlacao_media_ibov": float(corrs.mean()) if not corrs.empty else None,
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
    print("HISTORICAL STRESS ENGINE V2 INSTITUCIONAL")
    print("=" * 70)

    print("Baixando benchmark IBOV...")
    benchmarks, benchmark_df = gerar_benchmark()

    resultados = []

    for ticker in tickers:
        print(f"Calculando stress histórico: {ticker}")
        resultados.append(calcular_ativo(ticker, benchmarks))

    df_resultado = pd.DataFrame(resultados)
    cobertura = gerar_cobertura(df_resultado)

    Path("output").mkdir(exist_ok=True)

    df_resultado.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    cobertura.to_csv(COVERAGE_FILE, index=False, encoding="utf-8-sig")
    benchmark_df.to_csv(BENCHMARK_FILE, index=False, encoding="utf-8-sig")

    print()
    print("BENCHMARK IBOV:")
    print(benchmark_df.to_string(index=False))

    print()
    print("COBERTURA HISTÓRICA:")
    print(cobertura.to_string(index=False))

    print()
    print("Arquivos salvos:")
    print(OUTPUT_FILE)
    print(COVERAGE_FILE)
    print(BENCHMARK_FILE)

    return df_resultado


if __name__ == "__main__":
    gerar_historical_stress()
