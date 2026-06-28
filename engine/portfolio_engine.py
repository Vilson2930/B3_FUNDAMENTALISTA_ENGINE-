# ============================================================
# portfolio_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Carteira Institucional Final — V4 com Setor Oficial B3
#
# Filosofia:
# O Fundamentalista escolhe as melhores empresas.
# O Técnico calcula o momento de entrada.
# O Portfolio combina fundamentos + técnico, monta a carteira
# e garante consistência setorial usando data/setores_b3.csv.
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


INPUT_TECNICO = Path("output/top20_tecnico.csv")
OUTPUT_FILE = Path("output/carteira_institucional.csv")
PORTFOLIO_METRICS_FILE = Path("output/portfolio_metrics.csv")
SETOR_FILE = Path("data/setores_b3.csv")
AUDITORIA_SETOR_PORTFOLIO = Path("output/auditoria_setores_portfolio.csv")


PESO_FUNDAMENTAL = 0.70
PESO_TECNICO = 0.30

MAX_ATIVOS_CARTEIRA = 15
PESO_MAXIMO_ATIVO = 0.10
PESO_MINIMO_ATIVO = 0.02


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
# SETORES OFICIAIS B3
# ============================================================


def carregar_setores_b3():
    if not SETOR_FILE.exists():
        print("ATENÇÃO: data/setores_b3.csv não encontrado. Mantendo setor recebido.")
        return pd.DataFrame()

    setores = pd.read_csv(SETOR_FILE, encoding="utf-8-sig")
    setores.columns = [str(c).strip() for c in setores.columns]

    if "ticker" not in setores.columns or "setor_b3" not in setores.columns:
        print("ATENÇÃO: data/setores_b3.csv precisa ter as colunas ticker e setor_b3.")
        return pd.DataFrame()

    setores["ticker"] = setores["ticker"].astype(str).str.upper().str.strip()

    colunas = [
        c for c in ["ticker", "setor_b3", "subsetor_b3", "segmento_b3"]
        if c in setores.columns
    ]

    setores = setores[colunas].drop_duplicates("ticker")
    return setores


def aplicar_setor_oficial_b3(df):
    """
    Regra institucional:
    - Setor oficial vem de data/setores_b3.csv.
    - BRAPI/Yahoo/API ficam apenas como fallback.
    - O portfolio nunca deve depender cegamente do setor recebido no top20_tecnico.csv.
    """
    df = df.copy()

    if "ticker" not in df.columns:
        return df

    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

    if "setor" not in df.columns:
        df["setor"] = "SEM SETOR"

    df["setor_original_entrada"] = df["setor"].fillna("SEM SETOR")

    setores_b3 = carregar_setores_b3()

    if setores_b3.empty:
        df["setor_fonte"] = "ENTRADA_FALLBACK"
        df["subsetor_b3"] = df.get("subsetor_b3", "")
        df["segmento_b3"] = df.get("segmento_b3", "")
        return df

    df = df.merge(setores_b3, on="ticker", how="left")

    tem_setor_b3 = (
        df["setor_b3"].notna()
        & (df["setor_b3"].astype(str).str.strip() != "")
    )

    df["setor"] = np.where(
        tem_setor_b3,
        df["setor_b3"].astype(str).str.strip(),
        df["setor_original_entrada"].fillna("SEM SETOR").astype(str).str.strip(),
    )

    df["setor_fonte"] = np.where(
        tem_setor_b3,
        "B3_OFICIAL",
        "ENTRADA_FALLBACK",
    )

    df["setor_divergente"] = np.where(
        tem_setor_b3
        & (df["setor_original_entrada"].astype(str).str.strip() != df["setor"].astype(str).str.strip()),
        "SIM",
        "NÃO",
    )

    df = df.drop(columns=["setor_b3"], errors="ignore")

    Path("output").mkdir(exist_ok=True)
    colunas_auditoria = [
        c for c in [
            "ticker",
            "empresa",
            "setor_original_entrada",
            "setor",
            "setor_fonte",
            "setor_divergente",
            "subsetor_b3",
            "segmento_b3",
        ]
        if c in df.columns
    ]

    df[colunas_auditoria].to_csv(
        AUDITORIA_SETOR_PORTFOLIO,
        index=False,
        encoding="utf-8-sig",
    )

    print("Auditoria setorial do portfolio salva em:")
    print(AUDITORIA_SETOR_PORTFOLIO)

    return df


# ============================================================
# CLASSIFICAÇÕES
# ============================================================


def classificar_decisao(row):
    score_final = float(row.get("score_final_carteira", 0) or 0)
    score_tecnico = float(row.get("score_tecnico", 0) or 0)
    sinal = str(row.get("sinal_tecnico", "")).upper()
    risco = str(row.get("risco_tecnico", "")).upper()

    # Regra conservadora: técnico ruim bloqueia compra, mesmo com fundamento forte.
    if sinal in ["EVITAR", "FRACO"] or score_tecnico < 50 or "ELEVADO" in risco:
        return "NÃO PRIORIZAR AGORA"

    if score_final >= 80 and score_tecnico >= 75:
        return "COMPRAR AGORA"

    if score_final >= 70 and score_tecnico >= 60:
        return "COMPRAR PARCIAL"

    if score_final >= 60:
        return "AGUARDAR MELHOR ENTRADA"

    return "NÃO PRIORIZAR AGORA"


def classificar_conviccao(score):
    score = float(score or 0)

    if score >= 80:
        return "MUITO ALTA"
    if score >= 70:
        return "ALTA"
    if score >= 60:
        return "MÉDIA"
    if score >= 50:
        return "BAIXA"
    return "MUITO BAIXA"


def classificar_prioridade(row):
    decisao = str(row.get("decisao", "")).upper()
    score = float(row.get("score_final_carteira", 0) or 0)

    if "COMPRAR AGORA" in decisao:
        return "PRIORIDADE 1"
    if "COMPRAR PARCIAL" in decisao:
        return "PRIORIDADE 2"
    if "AGUARDAR" in decisao and score >= 60:
        return "PRIORIDADE 3"
    return "OBSERVAÇÃO"


def rating_institucional(score):
    score = float(score or 0)

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


def classificar_risco_carteira(row):
    risco_tecnico = str(row.get("risco_tecnico", "")).upper()
    sinal = str(row.get("sinal_tecnico", "")).upper()
    conv_tec = str(row.get("conviccao_tecnica", "")).upper()
    score_tecnico = float(row.get("score_tecnico", 0) or 0)

    if "ELEVADO" in risco_tecnico or sinal == "EVITAR" or score_tecnico < 35:
        return "RISCO ELEVADO"

    if "MODERADO/ALTO" in risco_tecnico or sinal == "FRACO" or "MUITO BAIXA" in conv_tec:
        return "RISCO MODERADO/ALTO"

    if "MODERADO" in risco_tecnico or score_tecnico < 55:
        return "RISCO MODERADO"

    return "RISCO CONTROLADO"


# ============================================================
# SCORE E PESOS
# ============================================================


def calcular_score_final(base):
    base = base.copy()

    base["score_final_carteira"] = (
        base["score_fundamental"] * PESO_FUNDAMENTAL
        + base["score_tecnico"] * PESO_TECNICO
    )

    return base


def calcular_allocation_score(row):
    score = float(row.get("score_final_carteira", 0) or 0)
    score_tecnico = float(row.get("score_tecnico", 0) or 0)
    decisao = str(row.get("decisao", "")).upper()
    risco = str(row.get("risco_carteira", "")).upper()
    conv_tec = str(row.get("conviccao_tecnica", "")).upper()

    fator = 1.0

    if "COMPRAR" in decisao:
        fator *= 1.10
    if "AGUARDAR" in decisao:
        fator *= 0.90
    if "NÃO" in decisao or "NAO" in decisao or "OBSERVAÇÃO" in decisao:
        fator *= 0.60

    if "MUITO ALTA" in conv_tec:
        fator *= 1.08
    elif "ALTA" in conv_tec:
        fator *= 1.04
    elif "BAIXA" in conv_tec:
        fator *= 0.85
    elif "MUITO BAIXA" in conv_tec:
        fator *= 0.70

    if "ELEVADO" in risco:
        fator *= 0.60
    elif "MODERADO/ALTO" in risco:
        fator *= 0.75
    elif "MODERADO" in risco:
        fator *= 0.90

    # Garante que técnico muito fraco reduza peso.
    if score_tecnico < 40:
        fator *= 0.70
    elif score_tecnico < 50:
        fator *= 0.85

    return max(score, 0) ** 2 * fator


def redistribuir_limite_ativo(df):
    df = df.copy()

    for _ in range(50):
        acima = df["peso_sugerido"] > PESO_MAXIMO_ATIVO

        if not acima.any():
            break

        excesso = (df.loc[acima, "peso_sugerido"] - PESO_MAXIMO_ATIVO).sum()
        df.loc[acima, "peso_sugerido"] = PESO_MAXIMO_ATIVO

        elegiveis = ~acima
        soma_elegiveis = df.loc[elegiveis, "peso_sugerido"].sum()

        if soma_elegiveis <= 0 or excesso <= 0:
            break

        df.loc[elegiveis, "peso_sugerido"] += (
            df.loc[elegiveis, "peso_sugerido"] / soma_elegiveis
        ) * excesso

    return df


def calcular_peso_inteligente(df):
    df = df.copy()

    df["allocation_score"] = df.apply(calcular_allocation_score, axis=1)

    total = df["allocation_score"].sum()

    if total <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df["allocation_score"] / total

    df = redistribuir_limite_ativo(df)

    # Peso mínimo só para ativos que não estão em risco elevado.
    aprovado_minimo = (
        df["score_final_carteira"] >= 55
    ) & (~df["risco_carteira"].astype(str).str.upper().str.contains("ELEVADO"))

    df.loc[aprovado_minimo, "peso_sugerido"] = df.loc[
        aprovado_minimo,
        "peso_sugerido",
    ].clip(lower=PESO_MINIMO_ATIVO)

    total = df["peso_sugerido"].sum()
    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df = redistribuir_limite_ativo(df)

    total = df["peso_sugerido"].sum()
    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    # Pequena tolerância para arredondamento.
    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100
    df["validacao_peso_ativo"] = np.where(
        df["peso_sugerido"] <= PESO_MAXIMO_ATIVO + 1e-8,
        "OK",
        "ACIMA DO LIMITE",
    )

    return df


# ============================================================
# EXPLICAÇÃO
# ============================================================


def gerar_motivo(row):
    motivos = []

    sf = float(row.get("score_fundamental", 0) or 0)
    st = float(row.get("score_tecnico", 0) or 0)
    moat = float(row.get("moat_score", 0) or 0)
    sinal = str(row.get("sinal_tecnico", "")).upper()
    risco = str(row.get("risco_tecnico", "")).upper()

    if sf >= 75:
        motivos.append("fundamentos fortes")
    elif sf >= 65:
        motivos.append("fundamentos bons")
    else:
        motivos.append("fundamentos moderados")

    if st >= 80:
        motivos.append("momento técnico muito favorável")
    elif st >= 65:
        motivos.append("momento técnico favorável")
    elif st >= 50:
        motivos.append("momento técnico neutro")
    else:
        motivos.append("momento técnico fraco")

    if moat >= 75:
        motivos.append("moat relevante")

    if sinal in ["EVITAR", "FRACO"]:
        motivos.append("entrada exige cautela")

    if "ELEVADO" in risco:
        motivos.append("risco técnico elevado")
    elif "MODERADO/ALTO" in risco:
        motivos.append("risco técnico moderado/alto")

    if row.get("setor_fonte", "") == "B3_OFICIAL":
        motivos.append("setor validado por base B3")

    return "; ".join(motivos)


def gerar_parecer_portfolio(row):
    return (
        f"{row.get('ticker', 'N/A')}: {row.get('motivo_decisao', '')}. "
        f"Decisão: {row.get('decisao', 'N/A')}. "
        f"Peso sugerido: {float(row.get('peso_sugerido_pct', 0) or 0):.2f}%."
    )


# ============================================================
# MÉTRICAS
# ============================================================


def gerar_metricas_portfolio(df):
    if df.empty:
        return pd.DataFrame()

    decisoes = df["decisao"].fillna("").astype(str).str.upper()
    riscos = df["risco_carteira"].fillna("").astype(str).str.upper()

    metricas = {
        "qtd_ativos": len(df),
        "score_medio_carteira": float(df["score_final_carteira"].mean()),
        "score_tecnico_medio": float(df["score_tecnico"].mean()),
        "score_fundamental_medio": float(df["score_fundamental"].mean()),
        "peso_total_pct": float(df["peso_sugerido_pct"].sum()),
        "peso_top5_pct": float(df.sort_values("peso_sugerido_pct", ascending=False).head(5)["peso_sugerido_pct"].sum()),
        "peso_maximo_real_pct": float(df["peso_sugerido_pct"].max()),
        "peso_maximo_ativo_pct": PESO_MAXIMO_ATIVO * 100,
        "soma_pesos_pct": float(df["peso_sugerido_pct"].sum()),
        "comprar": int(decisoes.str.contains("COMPRAR").sum()),
        "aguardar": int(decisoes.str.contains("AGUARDAR").sum()),
        "nao_priorizar": int(decisoes.str.contains("NÃO|NAO|EVITAR").sum()),
        "risco_controlado": int(riscos.str.contains("CONTROLADO").sum()),
        "risco_moderado": int(riscos.str.contains("MODERADO").sum()),
        "risco_elevado": int(riscos.str.contains("ELEVADO").sum()),
        "setores_b3_validados": int((df.get("setor_fonte", "") == "B3_OFICIAL").sum()) if "setor_fonte" in df.columns else 0,
        "setores_fallback": int((df.get("setor_fonte", "") != "B3_OFICIAL").sum()) if "setor_fonte" in df.columns else len(df),
    }

    return pd.DataFrame([metricas])


# ============================================================
# MOTOR PRINCIPAL
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

    if "ticker" in base.columns:
        base["ticker"] = base["ticker"].astype(str).str.strip().str.upper()

    # Garante consistência setorial no portfolio.
    base = aplicar_setor_oficial_b3(base)

    colunas_padrao = {
        "score_fundamental": 50,
        "score_tecnico": 50,
        "moat_score": 50,
        "sinal_tecnico": "NEUTRO",
        "conviccao_tecnica": "N/A",
        "risco_tecnico": "N/A",
        "diagnostico_tecnico": "N/A",
    }

    for coluna, valor in colunas_padrao.items():
        if coluna not in base.columns:
            print(f"ATENÇÃO: coluna {coluna} não encontrada. Usando {valor}.")
            base[coluna] = valor

    for coluna in ["score_fundamental", "score_tecnico", "moat_score"]:
        base[coluna] = pd.to_numeric(base[coluna], errors="coerce").fillna(50)

    print()
    print("Amostra antes do cálculo:")
    colunas_debug = [
        "ticker",
        "setor",
        "setor_fonte",
        "score_fundamental",
        "score_tecnico",
        "conviccao_tecnica",
        "risco_tecnico",
    ]
    colunas_debug = [c for c in colunas_debug if c in base.columns]
    print(base[colunas_debug].head(20))

    base = calcular_score_final(base)

    base = base.sort_values(
        ["score_final_carteira", "score_tecnico"],
        ascending=False,
    ).reset_index(drop=True)

    base = base.head(MAX_ATIVOS_CARTEIRA).reset_index(drop=True)

    base["decisao"] = base.apply(classificar_decisao, axis=1)
    base["conviccao"] = base["score_final_carteira"].apply(classificar_conviccao)
    base["prioridade"] = base.apply(classificar_prioridade, axis=1)
    base["rating_carteira"] = base["score_final_carteira"].apply(rating_institucional)
    base["risco_carteira"] = base.apply(classificar_risco_carteira, axis=1)
    base["motivo_decisao"] = base.apply(gerar_motivo, axis=1)

    base = calcular_peso_inteligente(base)

    # Ordena pelo peso para leitura executiva, mas preserva ranking por score.
    base = base.sort_values(
        ["peso_sugerido_pct", "score_final_carteira"],
        ascending=False,
    ).reset_index(drop=True)

    base.insert(0, "ranking_carteira", base.index + 1)

    base["parecer_portfolio"] = base.apply(gerar_parecer_portfolio, axis=1)

    metricas = gerar_metricas_portfolio(base)

    Path("output").mkdir(exist_ok=True)

    base.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    metricas.to_csv(
        PORTFOLIO_METRICS_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 70)
    print("CARTEIRA INSTITUCIONAL V4 — SETOR B3 VALIDADO")
    print("=" * 70)

    colunas = [
        "ranking_carteira",
        "ticker",
        "empresa",
        "setor",
        "setor_fonte",
        "score_fundamental",
        "score_tecnico",
        "score_final_carteira",
        "rating_carteira",
        "conviccao",
        "prioridade",
        "peso_sugerido_pct",
        "validacao_peso_ativo",
        "conviccao_tecnica",
        "risco_tecnico",
        "risco_carteira",
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
    print(PORTFOLIO_METRICS_FILE)

    return base


if __name__ == "__main__":
    montar_carteira()
