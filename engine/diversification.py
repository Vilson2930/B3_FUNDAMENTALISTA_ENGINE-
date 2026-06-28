# ============================================================
# diversification.py
# B3 FUNDAMENTALISTA ENGINE
# Diversificação Institucional da Carteira Final — V3 Corrigida
# ============================================================

from pathlib import Path
import numpy as np
import pandas as pd

INPUT_FILE = Path("output/carteira_institucional.csv")
OUTPUT_FILE = Path("output/carteira_diversificada.csv")
METRICS_FILE = Path("output/diversification_metrics.csv")

MAX_EMPRESAS = 15
MAX_EMPRESAS_POR_SETOR = 2
MAX_PESO_ATIVO = 0.10
MAX_PESO_SETOR = 0.20
MIN_SCORE_ENTRADA = 55
EPS = 1e-9


def carregar_carteira():
    if not INPUT_FILE.exists():
        print("Arquivo carteira_institucional.csv não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

    if "setor" not in df.columns:
        df["setor"] = "SEM SETOR"

    df["setor"] = df["setor"].fillna("SEM SETOR").astype(str).str.strip()
    return df


def escolher_score_col(df):
    if "score_final_carteira" in df.columns:
        return "score_final_carteira"
    if "score_final" in df.columns:
        return "score_final"
    raise Exception("Nenhuma coluna de score encontrada.")


def normalizar_colunas(df):
    df = df.copy()
    score_col = escolher_score_col(df)

    df[score_col] = pd.to_numeric(df[score_col], errors="coerce").fillna(0)
    df["score_tecnico"] = pd.to_numeric(df.get("score_tecnico", 50), errors="coerce").fillna(50)
    df["score_fundamental"] = pd.to_numeric(df.get("score_fundamental", 50), errors="coerce").fillna(50)

    for col in ["decisao", "rating_carteira", "conviccao"]:
        if col not in df.columns:
            df[col] = "N/A"
        df[col] = df[col].fillna("N/A")

    return df


def filtrar_minimo_qualidade(df):
    df = df.copy()
    score_col = escolher_score_col(df)
    df["filtro_qualidade"] = np.where(df[score_col] >= MIN_SCORE_ENTRADA, "APROVADO", "REPROVADO_SCORE_BAIXO")
    return df[df["filtro_qualidade"] == "APROVADO"].copy()


def limitar_empresas_por_setor(df):
    df = df.copy()
    score_col = escolher_score_col(df)
    df = df.sort_values([score_col, "score_tecnico", "score_fundamental"], ascending=False)

    selecionadas = []
    contador_setor = {}

    for _, row in df.iterrows():
        setor = row["setor"]
        contador_setor[setor] = contador_setor.get(setor, 0)

        if contador_setor[setor] >= MAX_EMPRESAS_POR_SETOR:
            continue

        selecionadas.append(row)
        contador_setor[setor] += 1

        if len(selecionadas) >= MAX_EMPRESAS:
            break

    return pd.DataFrame(selecionadas).reset_index(drop=True)


def calcular_allocation_score(df):
    df = df.copy()
    score_col = escolher_score_col(df)

    score_base = df[score_col].clip(lower=0)
    decisao = df["decisao"].astype(str).str.upper()
    conviccao = df["conviccao"].astype(str).str.upper()

    bonus_tecnico = np.where(df["score_tecnico"] >= 75, 1.08, 1.00)
    penal_tecnico = np.where(df["score_tecnico"] < 45, 0.88, 1.00)
    bonus_conviccao = np.where(conviccao.str.contains("ALTA"), 1.08, 1.00)
    penal_baixa = np.where(conviccao.str.contains("BAIXA"), 0.85, 1.00)
    penal_nao_priorizar = np.where(decisao.str.contains("NÃO|NAO|EVITAR"), 0.75, 1.00)

    df["allocation_score_div"] = (
        score_base * bonus_tecnico * penal_tecnico * bonus_conviccao * penal_baixa * penal_nao_priorizar
    ) ** 2

    df["allocation_score_div"] = df["allocation_score_div"].replace([np.inf, -np.inf], np.nan).fillna(0)
    return df


def alocar_com_limites(df):
    """
    Distribui 100% respeitando simultaneamente:
    - máximo por ativo
    - máximo por setor

    A correção principal está aqui: não existe normalização final cega,
    porque normalizar depois do limite pode fazer ativos voltarem acima de 10%.
    """
    df = df.copy().reset_index(drop=True)

    if df.empty:
        return df

    if len(df) * MAX_PESO_ATIVO + EPS < 1:
        raise Exception("Carteira inviável: poucos ativos para respeitar o limite máximo por ativo.")

    if df["setor"].nunique() * MAX_PESO_SETOR + EPS < 1:
        raise Exception("Carteira inviável: poucos setores para respeitar o limite máximo por setor.")

    scores = df["allocation_score_div"].astype(float).clip(lower=0)
    if scores.sum() <= 0:
        scores = pd.Series(1.0, index=df.index)

    pesos = pd.Series(0.0, index=df.index)
    restante = 1.0

    for _ in range(500):
        if restante <= 1e-8:
            break

        setor_atual = df.assign(peso_tmp=pesos).groupby("setor")["peso_tmp"].sum()
        capacidade_ativo = (MAX_PESO_ATIVO - pesos).clip(lower=0)
        capacidade_setor = df["setor"].map(lambda s: max(MAX_PESO_SETOR - setor_atual.get(s, 0.0), 0.0))
        capacidade_individual = pd.concat([capacidade_ativo, capacidade_setor], axis=1).min(axis=1)

        elegiveis = capacidade_individual > 1e-8
        if not elegiveis.any():
            break

        scores_elegiveis = scores.where(elegiveis, 0.0)
        if scores_elegiveis.sum() <= 0:
            scores_elegiveis = pd.Series(np.where(elegiveis, 1.0, 0.0), index=df.index)

        proposta = restante * scores_elegiveis / scores_elegiveis.sum()
        proposta_corrigida = proposta.copy()

        # trava por setor antes da trava por ativo
        for setor in df.loc[elegiveis, "setor"].unique():
            idx_setor = (df["setor"] == setor) & elegiveis
            capacidade_do_setor = max(MAX_PESO_SETOR - setor_atual.get(setor, 0.0), 0.0)
            soma_proposta_setor = proposta_corrigida.loc[idx_setor].sum()

            if soma_proposta_setor > capacidade_do_setor + EPS and soma_proposta_setor > 0:
                proposta_corrigida.loc[idx_setor] *= capacidade_do_setor / soma_proposta_setor

        # trava por ativo
        proposta_corrigida = pd.concat([proposta_corrigida, capacidade_ativo], axis=1).min(axis=1).clip(lower=0)

        adicionado = proposta_corrigida.sum()
        if adicionado <= 1e-10:
            break

        pesos += proposta_corrigida
        restante -= adicionado

    df["peso_sugerido"] = pesos
    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100
    return df


def validar_limites(df):
    df = df.copy()

    total = df["peso_sugerido"].sum()
    max_ativo_real = df["peso_sugerido"].max()
    max_setor_real = df.groupby("setor")["peso_sugerido"].sum().max()

    df["validacao_peso_ativo"] = np.where(df["peso_sugerido"] <= MAX_PESO_ATIVO + 1e-6, "OK", "FALHA")

    setor_pesos = df.groupby("setor")["peso_sugerido"].sum()
    df["validacao_peso_setor"] = df["setor"].map(
        lambda s: "OK" if setor_pesos.get(s, 0.0) <= MAX_PESO_SETOR + 1e-6 else "FALHA"
    )

    if max_ativo_real > MAX_PESO_ATIVO + 1e-6:
        raise Exception(f"Falha: ativo acima de 10%. Máximo real: {max_ativo_real * 100:.4f}%")

    if max_setor_real > MAX_PESO_SETOR + 1e-6:
        raise Exception(f"Falha: setor acima de 20%. Máximo real: {max_setor_real * 100:.4f}%")

    if abs(total - 1.0) > 1e-4:
        raise Exception(f"Falha: soma dos pesos diferente de 100%. Total real: {total * 100:.4f}%")

    return df


def calcular_exposicao_setorial(df):
    df = df.copy()

    exposicao = (
        df.groupby("setor")["peso_sugerido_pct"]
        .sum()
        .reset_index()
        .rename(columns={"peso_sugerido_pct": "peso_setor_pct"})
    )

    df = df.merge(exposicao, on="setor", how="left")

    df["alerta_setorial"] = df["peso_setor_pct"].apply(
        lambda x: "ACIMA DO LIMITE" if x > MAX_PESO_SETOR * 100 + 1e-6 else "OK"
    )

    df["peso_ativo_status"] = df["peso_sugerido_pct"].apply(
        lambda x: "ACIMA DO LIMITE" if x > MAX_PESO_ATIVO * 100 + 1e-6 else "OK"
    )

    return df


def calcular_metricas_diversificacao(df):
    if df.empty:
        return pd.DataFrame()

    pesos = df["peso_sugerido"].astype(float)
    hhi = float((pesos ** 2).sum())
    numero_efetivo_ativos = 1 / hhi if hhi > 0 else 0

    top5 = df.sort_values("peso_sugerido", ascending=False).head(5)["peso_sugerido"].sum()
    setor_pesos = df.groupby("setor")["peso_sugerido"].sum().sort_values(ascending=False)

    maior_setor = setor_pesos.index[0] if not setor_pesos.empty else "N/A"
    peso_maior_setor = setor_pesos.iloc[0] if not setor_pesos.empty else 0

    score_diversificacao = 100
    if top5 > 0.45:
        score_diversificacao -= 15
    if peso_maior_setor > MAX_PESO_SETOR:
        score_diversificacao -= 20
    if numero_efetivo_ativos < 8:
        score_diversificacao -= 15
    if hhi > 0.12:
        score_diversificacao -= 10

    score_diversificacao = max(0, min(100, score_diversificacao))

    if score_diversificacao >= 85:
        status = "EXCELENTE"
    elif score_diversificacao >= 70:
        status = "BOA"
    elif score_diversificacao >= 55:
        status = "MODERADA"
    else:
        status = "FRACA"

    return pd.DataFrame([{
        "qtd_ativos": len(df),
        "qtd_setores": df["setor"].nunique(),
        "peso_top5_pct": top5 * 100,
        "maior_setor": maior_setor,
        "peso_maior_setor_pct": peso_maior_setor * 100,
        "maior_peso_ativo_pct": pesos.max() * 100,
        "hhi": hhi,
        "numero_efetivo_ativos": numero_efetivo_ativos,
        "score_diversificacao": score_diversificacao,
        "status_diversificacao": status,
        "limite_peso_ativo_pct": MAX_PESO_ATIVO * 100,
        "limite_peso_setor_pct": MAX_PESO_SETOR * 100,
        "soma_pesos_pct": pesos.sum() * 100,
    }])


def classificar_risco_diversificacao(row):
    score = row.get("score_diversificacao", 0)

    if score >= 85:
        return "RISCO BAIXO"
    if score >= 70:
        return "RISCO CONTROLADO"
    if score >= 55:
        return "RISCO MODERADO"
    return "RISCO ELEVADO"


def aplicar_metricas_no_df(df, metricas):
    df = df.copy()

    if metricas.empty:
        return df

    for coluna in metricas.columns:
        df[coluna] = metricas.iloc[0][coluna]

    df["risco_diversificacao"] = df.apply(classificar_risco_diversificacao, axis=1)
    return df


def analisar_diversificacao():
    df = carregar_carteira()

    if df.empty:
        print("Nenhuma carteira para diversificar.")
        return df

    df = normalizar_colunas(df)
    df = filtrar_minimo_qualidade(df)

    if df.empty:
        print("Nenhuma empresa passou no filtro mínimo de qualidade.")
        return df

    resultado = limitar_empresas_por_setor(df)
    resultado = calcular_allocation_score(resultado)
    resultado = alocar_com_limites(resultado)
    resultado = validar_limites(resultado)
    resultado = calcular_exposicao_setorial(resultado)

    metricas = calcular_metricas_diversificacao(resultado)
    resultado = aplicar_metricas_no_df(resultado, metricas)

    resultado = resultado.sort_values("peso_sugerido_pct", ascending=False).reset_index(drop=True)
    resultado["ranking_diversificado"] = resultado.index + 1

    Path("output").mkdir(exist_ok=True)

    resultado.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    metricas.to_csv(METRICS_FILE, index=False, encoding="utf-8-sig")

    print("=" * 70)
    print("DIVERSIFICAÇÃO INSTITUCIONAL V3 — LIMITES VALIDADOS")
    print("=" * 70)

    colunas = [
        "ranking_diversificado",
        "ticker",
        "empresa",
        "setor",
        "rating_carteira",
        "conviccao",
        "score_final_carteira",
        "score_tecnico",
        "peso_sugerido_pct",
        "peso_setor_pct",
        "alerta_setorial",
        "peso_ativo_status",
        "validacao_peso_ativo",
        "validacao_peso_setor",
        "risco_diversificacao",
    ]

    colunas = [c for c in colunas if c in resultado.columns]
    print(resultado[colunas])

    print("\nMÉTRICAS DE DIVERSIFICAÇÃO")
    print(metricas)

    print("\nArquivo de diversificação salvo:")
    print(OUTPUT_FILE)

    print("\nArquivo de métricas salvo:")
    print(METRICS_FILE)

    return resultado


if __name__ == "__main__":
    analisar_diversificacao()
