# ============================================================
# correlation_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Correlation Engine Institucional
# V3 — Matriz + Pares + Clusters de Correlação
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


INPUT_FILE = Path("output/carteira_institucional.csv")

OUTPUT_MATRIX = Path("output/correlation_matrix.csv")
OUTPUT_SUMMARY = Path("output/correlation_summary.csv")
OUTPUT_PAIRS = Path("output/correlation_pairs.csv")
OUTPUT_CLUSTERS = Path("output/correlation_clusters.csv")

PERIODO = "3y"
LIMITE_CLUSTER = 0.50


def carregar_carteira():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    if "ticker" not in df.columns:
        raise ValueError("Coluna ticker não encontrada na carteira.")

    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df = df.dropna(subset=["ticker"])
    df = df.drop_duplicates(subset=["ticker"])

    return df


def yahoo(ticker):
    ticker = str(ticker).upper().strip()
    return ticker if ticker.endswith(".SA") else f"{ticker}.SA"


def ticker_limpo(ticker_yahoo):
    return str(ticker_yahoo).replace(".SA", "").upper().strip()


def limpar_colunas_precos(dados, tickers_yahoo):
    if dados is None or dados.empty:
        return pd.DataFrame()

    if isinstance(dados.columns, pd.MultiIndex):
        if "Close" in dados.columns.get_level_values(0):
            precos = dados["Close"]
        elif "Close" in dados.columns.get_level_values(-1):
            precos = dados.xs("Close", axis=1, level=-1)
        else:
            return pd.DataFrame()
    else:
        if "Close" in dados.columns:
            precos = dados[["Close"]].copy()
            if len(tickers_yahoo) == 1:
                precos.columns = [tickers_yahoo[0]]
        else:
            precos = dados.copy()

    if isinstance(precos, pd.Series):
        precos = precos.to_frame()

    precos = precos.apply(pd.to_numeric, errors="coerce")
    precos = precos.dropna(axis=1, how="all")

    return precos


def baixar_precos(tickers_yahoo):
    dados = yf.download(
        tickers_yahoo,
        period=PERIODO,
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    return limpar_colunas_precos(dados, tickers_yahoo)


def resumo_correlacao(corr):
    ativos = corr.columns.tolist()
    pares = []

    for i in range(len(ativos)):
        for j in range(i + 1, len(ativos)):
            valor = corr.iloc[i, j]

            if pd.isna(valor):
                continue

            pares.append({
                "ativo_1": ativos[i],
                "ativo_2": ativos[j],
                "correlacao": float(valor),
                "correlacao_abs": abs(float(valor)),
            })

    pares = pd.DataFrame(pares)

    if pares.empty:
        return pares, None, None, 0

    maior = pares.sort_values("correlacao_abs", ascending=False).iloc[0]
    menor = pares.sort_values("correlacao_abs", ascending=True).iloc[0]
    media = float(pares["correlacao_abs"].mean())

    return pares, maior, menor, media


def classificar(media):
    media = float(media or 0)

    if media >= 0.80:
        return "MUITO ALTA"
    if media >= 0.60:
        return "ALTA"
    if media >= 0.40:
        return "MODERADA"
    if media >= 0.20:
        return "BAIXA"

    return "MUITO BAIXA"


def score_diversificacao_correlacao(media):
    media = float(media or 0)
    score = 100 - (media * 100)
    return max(0, min(100, score))


def montar_clusters(pares, carteira):
    carteira = carteira.copy()

    carteira["ticker_base"] = carteira["ticker"].astype(str).str.upper().str.strip()

    if "peso_sugerido_pct" not in carteira.columns:
        carteira["peso_sugerido_pct"] = 0

    carteira["peso_sugerido_pct"] = pd.to_numeric(
        carteira["peso_sugerido_pct"],
        errors="coerce"
    ).fillna(0)

    mapa_setor = {}
    if "setor" in carteira.columns:
        mapa_setor = dict(zip(carteira["ticker_base"], carteira["setor"]))

    mapa_peso = dict(zip(carteira["ticker_base"], carteira["peso_sugerido_pct"]))

    ativos = sorted(carteira["ticker_base"].unique().tolist())

    grafo = {ativo: set() for ativo in ativos}

    for _, row in pares.iterrows():
        a = ticker_limpo(row["ativo_1"])
        b = ticker_limpo(row["ativo_2"])
        corr_abs = float(row["correlacao_abs"])

        if corr_abs >= LIMITE_CLUSTER:
            if a in grafo and b in grafo:
                grafo[a].add(b)
                grafo[b].add(a)

    visitados = set()
    clusters = []
    cluster_id = 1

    for ativo in ativos:
        if ativo in visitados:
            continue

        pilha = [ativo]
        grupo = []

        while pilha:
            atual = pilha.pop()

            if atual in visitados:
                continue

            visitados.add(atual)
            grupo.append(atual)

            for vizinho in grafo.get(atual, []):
                if vizinho not in visitados:
                    pilha.append(vizinho)

        peso_cluster = sum(mapa_peso.get(t, 0) for t in grupo)

        setores = sorted(
            set(
                str(mapa_setor.get(t, "N/A"))
                for t in grupo
            )
        )

        clusters.append({
            "cluster_id": cluster_id,
            "qtd_ativos_cluster": len(grupo),
            "ativos_cluster": ", ".join(sorted(grupo)),
            "peso_cluster_pct": peso_cluster,
            "setores_cluster": " | ".join(setores),
            "tipo_cluster": classificar_cluster(len(grupo), peso_cluster),
        })

        cluster_id += 1

    return pd.DataFrame(clusters).sort_values(
        ["qtd_ativos_cluster", "peso_cluster_pct"],
        ascending=False
    )


def classificar_cluster(qtd, peso):
    if qtd >= 4 or peso >= 30:
        return "RISCO DE CLUSTER ALTO"
    if qtd >= 3 or peso >= 20:
        return "RISCO DE CLUSTER MODERADO"
    if qtd == 2 or peso >= 10:
        return "CLUSTER CONTROLADO"

    return "ATIVO ISOLADO"


def executar_correlation_engine():
    print("=" * 70)
    print("CORRELATION ENGINE V3 — MATRIZ + CLUSTERS")
    print("=" * 70)
    print(f"Carteira utilizada: {INPUT_FILE}")
    print("=" * 70)

    carteira = carregar_carteira()

    tickers_yahoo = [yahoo(t) for t in carteira["ticker"]]

    print()
    print("Baixando preços...")
    print(", ".join(tickers_yahoo))

    precos = baixar_precos(tickers_yahoo)

    if precos.empty or len(precos.columns) < 2:
        raise ValueError(
            "Dados insuficientes para calcular correlação. "
            "Menos de 2 ativos com preços válidos."
        )

    retornos = precos.pct_change().dropna(how="all")
    retornos = retornos.dropna(axis=1, how="all")

    corr = retornos.corr()

    pares, maior, menor, media = resumo_correlacao(corr)

    if maior is None:
        raise ValueError("Não foi possível gerar pares de correlação válidos.")

    clusters = montar_clusters(pares, carteira)

    resumo = pd.DataFrame([{
        "arquivo_entrada": str(INPUT_FILE),
        "periodo": PERIODO,
        "limite_cluster": LIMITE_CLUSTER,
        "ativos_na_carteira": len(carteira),
        "ativos_com_precos_validos": len(corr.columns),
        "pares_analisados": len(pares),
        "correlacao_media_abs": media,
        "classificacao_correlacao": classificar(media),
        "score_diversificacao_correlacao": score_diversificacao_correlacao(media),
        "qtd_clusters": len(clusters),
        "maior_cluster_qtd_ativos": int(clusters["qtd_ativos_cluster"].max()),
        "maior_cluster_peso_pct": float(clusters["peso_cluster_pct"].max()),
        "maior_correlacao": f"{maior['ativo_1']} x {maior['ativo_2']}",
        "valor_maior_correlacao": maior["correlacao"],
        "menor_correlacao": f"{menor['ativo_1']} x {menor['ativo_2']}",
        "valor_menor_correlacao": menor["correlacao"],
    }])

    Path("output").mkdir(exist_ok=True)

    corr.to_csv(OUTPUT_MATRIX, encoding="utf-8-sig")
    resumo.to_csv(OUTPUT_SUMMARY, index=False, encoding="utf-8-sig")
    pares.to_csv(OUTPUT_PAIRS, index=False, encoding="utf-8-sig")
    clusters.to_csv(OUTPUT_CLUSTERS, index=False, encoding="utf-8-sig")

    print()
    print("=" * 70)
    print("RESUMO DE CORRELAÇÃO")
    print("=" * 70)
    print(resumo.to_string(index=False))

    print()
    print("TOP 10 MAIORES CORRELAÇÕES:")
    print(
        pares.sort_values("correlacao_abs", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print()
    print("CLUSTERS DE CORRELAÇÃO:")
    print(clusters.to_string(index=False))

    print()
    print("Arquivos gerados:")
    print(OUTPUT_MATRIX)
    print(OUTPUT_SUMMARY)
    print(OUTPUT_PAIRS)
    print(OUTPUT_CLUSTERS)

    return corr


if __name__ == "__main__":
    executar_correlation_engine()
