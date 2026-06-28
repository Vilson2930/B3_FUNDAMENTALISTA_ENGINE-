# ============================================================
# diversification.py
# B3 FUNDAMENTALISTA ENGINE
# Diversificação Institucional da Carteira Final — V2
# ============================================================

from pathlib import Path
import pandas as pd
import numpy as np


INPUT_FILE = Path("output/carteira_institucional.csv")
OUTPUT_FILE = Path("output/carteira_diversificada.csv")
METRICS_FILE = Path("output/diversification_metrics.csv")


MAX_EMPRESAS = 15
MAX_EMPRESAS_POR_SETOR = 2
MAX_PESO_ATIVO = 0.10
MAX_PESO_SETOR = 0.20
MIN_SCORE_ENTRADA = 55


def carregar_carteira():
    if not INPUT_FILE.exists():
        print("Arquivo carteira_institucional.csv não encontrado.")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]

    if "setor" not in df.columns:
        df["setor"] = "SEM SETOR"

    df["setor"] = df["setor"].fillna("SEM SETOR").astype(str).str.strip()

    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

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

    if "score_tecnico" in df.columns:
        df["score_tecnico"] = pd.to_numeric(df["score_tecnico"], errors="coerce").fillna(50)
    else:
        df["score_tecnico"] = 50

    if "score_fundamental" in df.columns:
        df["score_fundamental"] = pd.to_numeric(df["score_fundamental"], errors="coerce").fillna(50)
    else:
        df["score_fundamental"] = 50

    if "decisao" not in df.columns:
        df["decisao"] = "N/A"

    if "rating_carteira" not in df.columns:
        df["rating_carteira"] = "N/A"

    if "conviccao" not in df.columns:
        df["conviccao"] = "N/A"

    return df


def filtrar_minimo_qualidade(df):
    df = df.copy()

    score_col = escolher_score_col(df)

    df["filtro_qualidade"] = np.where(
        df[score_col] >= MIN_SCORE_ENTRADA,
        "APROVADO",
        "REPROVADO_SCORE_BAIXO"
    )

    return df[df["filtro_qualidade"] == "APROVADO"].copy()


def limitar_empresas_por_setor(df):
    df = df.copy()

    score_col = escolher_score_col(df)

    df = df.sort_values(
        [score_col, "score_tecnico", "score_fundamental"],
        ascending=False
    )

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

    bonus_tecnico = np.where(df["score_tecnico"] >= 75, 1.08, 1.00)
    penal_tecnico = np.where(df["score_tecnico"] < 45, 0.88, 1.00)

    bonus_conviccao = np.where(df["conviccao"].astype(str).str.upper().str.contains("ALTA"), 1.08, 1.00)
    penal_baixa = np.where(df["conviccao"].astype(str).str.upper().str.contains("BAIXA"), 0.85, 1.00)

    penal_nao_priorizar = np.where(
        df["decisao"].astype(str).str.upper().str.contains("NÃO|NAO|EVITAR"),
        0.75,
        1.00
    )

    df["allocation_score_div"] = (
        score_base
        * bonus_tecnico
        * penal_tecnico
        * bonus_conviccao
        * penal_baixa
        * penal_nao_priorizar
    ) ** 2

    return df


def normalizar_pesos(df):
    df = df.copy()

    total = df["allocation_score_div"].sum()

    if total <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df["allocation_score_div"] / total

    return df


def redistribuir_excesso_ativo(df):
    df = df.copy()

    for _ in range(20):
        excesso = df["peso_sugerido"] > MAX_PESO_ATIVO

        if not excesso.any():
            break

        sobra = (df.loc[excesso, "peso_sugerido"] - MAX_PESO_ATIVO).sum()

        df.loc[excesso, "peso_sugerido"] = MAX_PESO_ATIVO

        elegiveis = ~excesso

        total_elegivel = df.loc[elegiveis, "peso_sugerido"].sum()

        if total_elegivel <= 0:
            break

        df.loc[elegiveis, "peso_sugerido"] += (
            df.loc[elegiveis, "peso_sugerido"] / total_elegivel
        ) * sobra

    return df


def redistribuir_excesso_setor(df):
    df = df.copy()

    for _ in range(30):
        setor_pesos = df.groupby("setor")["peso_sugerido"].sum()
        setores_acima = setor_pesos[setor_pesos > MAX_PESO_SETOR]

        if setores_acima.empty:
            break

        for setor, peso_setor in setores_acima.items():
            excesso = peso_setor - MAX_PESO_SETOR
            idx_setor = df["setor"] == setor

            df.loc[idx_setor, "peso_sugerido"] *= MAX_PESO_SETOR / peso_setor

            idx_fora = ~idx_setor
            total_fora = df.loc[idx_fora, "peso_sugerido"].sum()

            if total_fora > 0:
                df.loc[idx_fora, "peso_sugerido"] += (
                    df.loc[idx_fora, "peso_sugerido"] / total_fora
                ) * excesso

        df = redistribuir_excesso_ativo(df)

    return df


def finalizar_pesos(df):
    df = df.copy()

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df = redistribuir_excesso_ativo(df)
    df = redistribuir_excesso_setor(df)

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100

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
        lambda x: "ACIMA DO LIMITE" if x > MAX_PESO_SETOR * 100 else "OK"
    )

    df["peso_ativo_status"] = df["peso_sugerido_pct"].apply(
        lambda x: "ACIMA DO LIMITE" if x > MAX_PESO_ATIVO * 100 else "OK"
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

    metricas = {
        "qtd_ativos": len(df),
        "qtd_setores": df["setor"].nunique(),
        "peso_top5_pct": top5 * 100,
        "maior_setor": maior_setor,
        "peso_maior_setor_pct": peso_maior_setor * 100,
        "hhi": hhi,
        "numero_efetivo_ativos": numero_efetivo_ativos,
        "score_diversificacao": score_diversificacao,
        "status_diversificacao": status,
        "limite_peso_ativo_pct": MAX_PESO_ATIVO * 100,
        "limite_peso_setor_pct": MAX_PESO_SETOR * 100,
    }

    return pd.DataFrame([metricas])


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
    resultado = normalizar_pesos(resultado)
    resultado = finalizar_pesos(resultado)
    resultado = calcular_exposicao_setorial(resultado)

    metricas = calcular_metricas_diversificacao(resultado)
    resultado = aplicar_metricas_no_df(resultado, metricas)

    resultado = resultado.sort_values(
        "peso_sugerido_pct",
        ascending=False
    ).reset_index(drop=True)

    resultado["ranking_diversificado"] = resultado.index + 1

    Path("output").mkdir(exist_ok=True)

    resultado.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    metricas.to_csv(
        METRICS_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 70)
    print("DIVERSIFICAÇÃO INSTITUCIONAL V2")
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
