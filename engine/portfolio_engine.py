# ============================================================
# portfolio_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Carteira Institucional Final — V3 Explicável com Top 15
#
# Filosofia:
# - O Fundamentalista escolhe as melhores empresas.
# - O Técnico calcula o momento de entrada.
# - O Portfolio combina fundamento + técnico e transforma em carteira.
# - Score Final = 70% Fundamentalista + 30% Técnico.
# - A decisão final deve ser conservadora, explicável e auditável.
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


INPUT_TECNICO = Path("output/top20_tecnico.csv")
OUTPUT_FILE = Path("output/carteira_institucional.csv")
METRICS_FILE = Path("output/portfolio_metrics.csv")


PESO_FUNDAMENTAL = 0.70
PESO_TECNICO = 0.30

PESO_MAXIMO_ATIVO = 0.10
PESO_MINIMO_ATIVO = 0.02

MIN_SCORE_CARTEIRA = 50
MAX_ATIVOS_CARTEIRA = 15


# ============================================================
# LEITURA
# ============================================================

def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(caminho, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(caminho)

    df.columns = [str(c).strip() for c in df.columns]
    return df


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_base(base):
    base = base.copy()

    if "ticker" in base.columns:
        base["ticker"] = base["ticker"].astype(str).str.strip().str.upper()

    defaults = {
        "score_fundamental": 50,
        "score_tecnico": 50,
        "moat_score": 50,
        "score_tendencia": 50,
        "score_entrada": 50,
        "score_momentum": 50,
        "score_volume": 50,
        "score_risco": 50,
    }

    for coluna, valor in defaults.items():
        if coluna not in base.columns:
            base[coluna] = valor
        base[coluna] = pd.to_numeric(base[coluna], errors="coerce").fillna(valor)

    texto_defaults = {
        "empresa": "",
        "setor": "SEM SETOR",
        "rating": "N/A",
        "sinal_tecnico": "NEUTRO",
        "diagnostico_tecnico": "Diagnóstico técnico não disponível.",
        "conviccao_tecnica": "N/A",
        "risco_tecnico": "N/A",
        "tendencia_resumo": "N/A",
        "mm200_status": "N/A",
        "rsi_status": "N/A",
        "momentum_status": "N/A",
        "volume_status": "N/A",
        "volatilidade_status": "N/A",
    }

    for coluna, valor in texto_defaults.items():
        if coluna not in base.columns:
            base[coluna] = valor
        base[coluna] = base[coluna].fillna(valor)

    return base


# ============================================================
# CLASSIFICAÇÕES INSTITUCIONAIS
# ============================================================

def rating_institucional(score):
    if score >= 90:
        return "AAA"
    if score >= 85:
        return "AA+"
    if score >= 80:
        return "AA"
    if score >= 75:
        return "A+"
    if score >= 70:
        return "A"
    if score >= 65:
        return "BBB+"
    if score >= 60:
        return "BBB"
    if score >= 55:
        return "BB"
    return "B"


def classificar_conviccao(score):
    if score >= 80:
        return "MUITO ALTA"
    if score >= 70:
        return "ALTA"
    if score >= 60:
        return "MÉDIA"
    if score >= 50:
        return "BAIXA"
    return "MUITO BAIXA"


def classificar_prioridade(score):
    if score >= 80:
        return "PRIORIDADE 1"
    if score >= 70:
        return "PRIORIDADE 2"
    if score >= 60:
        return "PRIORIDADE 3"
    return "OBSERVAÇÃO"


def classificar_risco_carteira(row):
    score = row.get("score_final_carteira", 0)
    tecnico = row.get("score_tecnico", 50)
    sinal = str(row.get("sinal_tecnico", "")).upper()
    rating = str(row.get("rating_carteira", "")).upper()

    pontos_risco = 0

    if tecnico < 45:
        pontos_risco += 2
    elif tecnico < 60:
        pontos_risco += 1

    if "EVITAR" in sinal:
        pontos_risco += 2
    elif "FRACO" in sinal:
        pontos_risco += 1

    if rating in ["B", "BB"]:
        pontos_risco += 1

    if score < 60:
        pontos_risco += 1

    if pontos_risco >= 4:
        return "ELEVADO"
    if pontos_risco >= 2:
        return "MODERADO/ALTO"
    if pontos_risco == 1:
        return "MODERADO"
    return "CONTROLADO"


# ============================================================
# DECISÃO FINAL
# ============================================================

def classificar_decisao(row):
    score = row.get("score_final_carteira", 0)
    tecnico = row.get("score_tecnico", 50)
    sinal = str(row.get("sinal_tecnico", "")).upper()

    # Trava institucional: técnico muito fraco não vira compra,
    # mesmo que o fundamento seja bom.
    if "EVITAR" in sinal or tecnico < 35:
        return "NÃO PRIORIZAR AGORA"

    if "FRACO" in sinal or tecnico < 50:
        if score >= 70:
            return "AGUARDAR MELHOR ENTRADA"
        return "NÃO PRIORIZAR AGORA"

    if score >= 80 and tecnico >= 75:
        return "COMPRAR AGORA"

    if score >= 70 and tecnico >= 60:
        return "COMPRAR PARCIAL"

    if score >= 60:
        return "AGUARDAR MELHOR ENTRADA"

    return "NÃO PRIORIZAR AGORA"


# ============================================================
# SCORE FINAL
# ============================================================

def calcular_score_final(base):
    base = base.copy()

    base["score_final_carteira"] = (
        base["score_fundamental"] * PESO_FUNDAMENTAL +
        base["score_tecnico"] * PESO_TECNICO
    )

    base["score_final_carteira"] = base["score_final_carteira"].round(2)

    return base


# ============================================================
# PESOS
# ============================================================

def calcular_allocation_score(df):
    df = df.copy()

    score = df["score_final_carteira"].clip(lower=0)

    bonus_compra = np.where(
        df["decisao"].astype(str).str.upper().str.contains("COMPRAR"),
        1.10,
        1.00,
    )

    penal_aguardar = np.where(
        df["decisao"].astype(str).str.upper().str.contains("AGUARDAR"),
        0.90,
        1.00,
    )

    penal_nao_priorizar = np.where(
        df["decisao"].astype(str).str.upper().str.contains("NÃO|NAO|EVITAR"),
        0.65,
        1.00,
    )

    bonus_conviccao = np.where(
        df["conviccao"].astype(str).str.upper().str.contains("ALTA"),
        1.08,
        1.00,
    )

    penal_risco = np.where(
        df["risco_carteira"].astype(str).str.upper().str.contains("ELEVADO"),
        0.65,
        np.where(
            df["risco_carteira"].astype(str).str.upper().str.contains("MODERADO/ALTO"),
            0.80,
            1.00,
        ),
    )

    df["allocation_score"] = (
        score * bonus_compra * penal_aguardar * penal_nao_priorizar * bonus_conviccao * penal_risco
    ) ** 2

    return df


def normalizar_pesos_com_limite(df):
    df = df.copy()

    if df.empty:
        return df

    total_score = df["allocation_score"].sum()

    if total_score <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df["allocation_score"] / total_score

    # Redistribuição iterativa respeitando limite máximo por ativo.
    for _ in range(100):
        acima = df["peso_sugerido"] > PESO_MAXIMO_ATIVO

        if not acima.any():
            break

        excesso = (df.loc[acima, "peso_sugerido"] - PESO_MAXIMO_ATIVO).sum()
        df.loc[acima, "peso_sugerido"] = PESO_MAXIMO_ATIVO

        elegiveis = ~acima
        total_elegivel = df.loc[elegiveis, "peso_sugerido"].sum()

        if total_elegivel <= 0:
            break

        df.loc[elegiveis, "peso_sugerido"] += (
            df.loc[elegiveis, "peso_sugerido"] / total_elegivel
        ) * excesso

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    # Segunda trava para evitar que a normalização estoure o teto.
    for _ in range(100):
        acima = df["peso_sugerido"] > PESO_MAXIMO_ATIVO
        if not acima.any():
            break

        excesso = (df.loc[acima, "peso_sugerido"] - PESO_MAXIMO_ATIVO).sum()
        df.loc[acima, "peso_sugerido"] = PESO_MAXIMO_ATIVO

        elegiveis = ~acima
        total_elegivel = df.loc[elegiveis, "peso_sugerido"].sum()

        if total_elegivel <= 0:
            break

        capacidade = PESO_MAXIMO_ATIVO - df.loc[elegiveis, "peso_sugerido"]
        capacidade = capacidade.clip(lower=0)
        capacidade_total = capacidade.sum()

        if capacidade_total <= 0:
            break

        incremento = capacidade / capacidade_total * excesso
        df.loc[elegiveis, "peso_sugerido"] += incremento

    df["peso_sugerido_pct"] = (df["peso_sugerido"] * 100).round(2)
    df["validacao_peso_ativo"] = np.where(
        df["peso_sugerido"] <= PESO_MAXIMO_ATIVO + 1e-9,
        "OK",
        "ACIMA DO LIMITE",
    )

    return df


# ============================================================
# EXPLICAÇÃO DA DECISÃO
# ============================================================

def gerar_motivo(row):
    motivos = []

    score_fund = row.get("score_fundamental", 0)
    score_tec = row.get("score_tecnico", 0)
    moat = row.get("moat_score", 0)
    sinal = str(row.get("sinal_tecnico", "")).upper()
    risco = str(row.get("risco_carteira", "")).upper()

    if score_fund >= 75:
        motivos.append("fundamentos fortes")
    elif score_fund >= 65:
        motivos.append("fundamentos bons")
    elif score_fund >= 55:
        motivos.append("fundamentos moderados")
    else:
        motivos.append("fundamentos frágeis")

    if score_tec >= 80:
        motivos.append("momento técnico muito favorável")
    elif score_tec >= 65:
        motivos.append("momento técnico favorável")
    elif score_tec >= 50:
        motivos.append("momento técnico neutro")
    else:
        motivos.append("momento técnico fraco")

    if moat >= 75:
        motivos.append("moat relevante")

    if "FRACO" in sinal or "EVITAR" in sinal:
        motivos.append("entrada exige cautela")

    if "ELEVADO" in risco:
        motivos.append("risco técnico elevado")
    elif "MODERADO/ALTO" in risco:
        motivos.append("risco técnico moderado/alto")

    return "; ".join(motivos)


def gerar_parecer_portfolio(row):
    ticker = row.get("ticker", "")
    decisao = row.get("decisao", "")
    conviccao = row.get("conviccao", "")
    peso = row.get("peso_sugerido_pct", 0)
    diagnostico = row.get("diagnostico_tecnico", "")

    return (
        f"{ticker}: decisão {decisao}; convicção {conviccao}; "
        f"peso sugerido {peso:.2f}%. {diagnostico}"
    )


# ============================================================
# MÉTRICAS DA CARTEIRA
# ============================================================

def calcular_metricas_portfolio(df):
    if df.empty:
        return pd.DataFrame()

    metricas = {
        "qtd_ativos": len(df),
        "score_medio_carteira": df["score_final_carteira"].mean(),
        "score_fundamental_medio": df["score_fundamental"].mean(),
        "score_tecnico_medio": df["score_tecnico"].mean(),
        "peso_top5_pct": df.sort_values("peso_sugerido", ascending=False).head(5)["peso_sugerido"].sum() * 100,
        "qtd_comprar": df["decisao"].astype(str).str.contains("COMPRAR", case=False, na=False).sum(),
        "qtd_aguardar": df["decisao"].astype(str).str.contains("AGUARDAR", case=False, na=False).sum(),
        "qtd_nao_priorizar": df["decisao"].astype(str).str.contains("NÃO|NAO", case=False, na=False).sum(),
        "qtd_risco_elevado": df["risco_carteira"].astype(str).str.contains("ELEVADO", case=False, na=False).sum(),
        "peso_maximo_ativo_pct": PESO_MAXIMO_ATIVO * 100,
        "soma_pesos_pct": df["peso_sugerido"].sum() * 100,
    }

    return pd.DataFrame([metricas])


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def montar_carteira():
    base = carregar_csv(INPUT_TECNICO)

    if base.empty:
        print("Arquivo top20_tecnico.csv vazio ou não encontrado.")
        return pd.DataFrame()

    print("=" * 70)
    print("AUDITORIA — TOP20 TÉCNICO CARREGADO")
    print("=" * 70)
    print("Linhas:", len(base))
    print("Colunas:", list(base.columns))

    base = normalizar_base(base)

    print()
    print("Amostra antes do cálculo:")
    colunas_debug = [
        "ticker",
        "score_fundamental",
        "score_tecnico",
        "sinal_tecnico",
        "conviccao_tecnica",
        "risco_tecnico",
    ]
    colunas_debug = [c for c in colunas_debug if c in base.columns]
    print(base[colunas_debug].head(20))

    base = calcular_score_final(base)

    base["rating_carteira"] = base["score_final_carteira"].apply(rating_institucional)
    base["conviccao"] = base["score_final_carteira"].apply(classificar_conviccao)
    base["prioridade"] = base["score_final_carteira"].apply(classificar_prioridade)
    base["risco_carteira"] = base.apply(classificar_risco_carteira, axis=1)
    base["decisao"] = base.apply(classificar_decisao, axis=1)
    base["motivo_decisao"] = base.apply(gerar_motivo, axis=1)

    base = base[base["score_final_carteira"] >= MIN_SCORE_CARTEIRA].copy()

    # Mantém a carteira institucional enxuta e compatível com o relatório.
    # O Top20 técnico continua sendo analisado, mas a carteira final usa apenas
    # os 15 melhores ativos por score final e score técnico.
    base = base.sort_values(
        ["score_final_carteira", "score_tecnico"],
        ascending=False,
    ).head(MAX_ATIVOS_CARTEIRA).reset_index(drop=True)

    base = calcular_allocation_score(base)
    base = normalizar_pesos_com_limite(base)

    base["parecer_portfolio"] = base.apply(gerar_parecer_portfolio, axis=1)

    base = base.sort_values(
        ["score_final_carteira", "score_tecnico"],
        ascending=False,
    ).reset_index(drop=True)

    base.insert(0, "ranking_carteira", base.index + 1)

    metricas = calcular_metricas_portfolio(base)

    Path("output").mkdir(exist_ok=True)

    base.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    metricas.to_csv(
        METRICS_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 70)
    print("CARTEIRA INSTITUCIONAL V3 — TOP 15 EXPLICÁVEL")
    print("=" * 70)

    colunas = [
        "ranking_carteira",
        "ticker",
        "empresa",
        "setor",
        "score_fundamental",
        "score_tecnico",
        "score_final_carteira",
        "rating_carteira",
        "conviccao",
        "prioridade",
        "risco_carteira",
        "peso_sugerido_pct",
        "validacao_peso_ativo",
        "sinal_tecnico",
        "decisao",
        "motivo_decisao",
    ]

    colunas = [c for c in colunas if c in base.columns]

    print(base[colunas])

    print("\nMÉTRICAS DO PORTFÓLIO")
    print(metricas)

    print("\nCarteira institucional salva em:")
    print(OUTPUT_FILE)

    print("\nMétricas do portfólio salvas em:")
    print(METRICS_FILE)

    return base


if __name__ == "__main__":
    montar_carteira()
