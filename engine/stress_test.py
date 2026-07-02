# ============================================================
# stress_test.py
# B3 FUNDAMENTALISTA ENGINE
# Stress Test Institucional da Carteira
#
# V4 — Usa histórico real quando existir
#      Usa stress setorial como fallback quando não houver histórico
# ============================================================

from pathlib import Path
import pandas as pd


INPUT_FILE = Path("output/carteira_diversificada.csv")
HISTORICAL_FILE = Path("output/historical_stress.csv")
COVERAGE_FILE = Path("output/historical_stress_coverage.csv")

OUTPUT_FILE = Path("output/stress_test.csv")
SUMMARY_FILE = Path("output/stress_test_summary.csv")
OVERVIEW_FILE = Path("output/stress_test_overview.csv")


STRESS_SETOR = {
    "Construção Civil": {"crise_2008": -65, "covid_2020": -45, "juros_altos_2021_2022": -40},
    "Consumo Cíclico": {"crise_2008": -55, "covid_2020": -40, "juros_altos_2021_2022": -35},
    "Financeiro": {"crise_2008": -55, "covid_2020": -35, "juros_altos_2021_2022": -30},
    "Petróleo, Gás e Biocombustíveis": {"crise_2008": -60, "covid_2020": -50, "juros_altos_2021_2022": -25},
    "Utilidade Pública": {"crise_2008": -30, "covid_2020": -25, "juros_altos_2021_2022": -20},
    "Saúde": {"crise_2008": -25, "covid_2020": -20, "juros_altos_2021_2022": -15},
    "Comunicações": {"crise_2008": -35, "covid_2020": -25, "juros_altos_2021_2022": -20},
    "Bens Industriais": {"crise_2008": -50, "covid_2020": -35, "juros_altos_2021_2022": -30},
    "Materiais Básicos": {"crise_2008": -55, "covid_2020": -35, "juros_altos_2021_2022": -25},
    "Tecnologia da Informação": {"crise_2008": -50, "covid_2020": -45, "juros_altos_2021_2022": -35},
    "Consumo Não Cíclico": {"crise_2008": -30, "covid_2020": -25, "juros_altos_2021_2022": -20},
}

DEFAULT_STRESS = {
    "crise_2008": -45,
    "covid_2020": -35,
    "juros_altos_2021_2022": -30,
}


CENARIOS = [
    "crise_2008",
    "covid_2020",
    "juros_altos_2021_2022",
]


def carregar_csv(caminho):
    if not caminho.exists():
        return pd.DataFrame()

    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def normalizar_peso(df):
    df = df.copy()

    df["peso_sugerido_pct"] = pd.to_numeric(
        df["peso_sugerido_pct"],
        errors="coerce"
    ).fillna(0)

    soma = df["peso_sugerido_pct"].sum()

    if soma <= 0:
        df["peso_sugerido_pct"] = 100 / len(df)
    elif abs(soma - 100) > 0.01:
        df["peso_sugerido_pct"] = df["peso_sugerido_pct"] / soma * 100

    return df


def obter_stress_fallback(setor, cenario):
    setor = str(setor or "").strip()

    if setor in STRESS_SETOR:
        return STRESS_SETOR[setor].get(cenario, DEFAULT_STRESS[cenario])

    return DEFAULT_STRESS[cenario]


def classificar_risco(perda_pct):
    perda = abs(float(perda_pct))

    if perda >= 50:
        return "RISCO EXTREMO"
    if perda >= 40:
        return "RISCO ALTO"
    if perda >= 30:
        return "RISCO MODERADO"
    if perda >= 20:
        return "RISCO CONTROLADO"

    return "RISCO BAIXO"


def classificar_perfil(perda_pct):
    perda = abs(float(perda_pct))

    if perda >= 50:
        return "CARTEIRA AGRESSIVA EM STRESS"
    if perda >= 40:
        return "CARTEIRA MODERADAMENTE AGRESSIVA"
    if perda >= 30:
        return "CARTEIRA BALANCEADA COM RISCO CÍCLICO"

    return "CARTEIRA MAIS DEFENSIVA"


def calcular_hhi(df):
    pesos = df["peso_sugerido_pct"] / 100
    return float((pesos ** 2).sum())


def calcular_numero_efetivo_ativos(hhi):
    if hhi <= 0:
        return 0
    return 1 / hhi


def preparar_base():
    carteira = carregar_csv(INPUT_FILE)

    if carteira.empty:
        raise FileNotFoundError("carteira_diversificada.csv não encontrado ou vazio.")

    if "ticker" not in carteira.columns:
        raise ValueError("Coluna ticker não encontrada na carteira.")

    if "setor" not in carteira.columns:
        raise ValueError("Coluna setor não encontrada na carteira.")

    if "peso_sugerido_pct" not in carteira.columns:
        raise ValueError("Coluna peso_sugerido_pct não encontrada na carteira.")

    carteira["ticker"] = carteira["ticker"].astype(str).str.upper().str.strip()
    carteira = normalizar_peso(carteira)

    historico = carregar_csv(HISTORICAL_FILE)

    if not historico.empty:
        historico["ticker"] = historico["ticker"].astype(str).str.upper().str.strip()

        carteira = carteira.merge(
            historico,
            on="ticker",
            how="left"
        )
    else:
        print("ATENÇÃO: historical_stress.csv não encontrado. Usando apenas fallback setorial.")

    return carteira


def aplicar_stress(df):
    df = df.copy()

    for cenario in CENARIOS:
        dd_col = f"{cenario}_drawdown_pct"
        fonte_col = f"{cenario}_fonte"

        stress_col = f"{cenario}_stress_pct"
        fonte_final_col = f"{cenario}_stress_fonte"
        impacto_col = f"impacto_{cenario}_pct"

        def escolher_stress(row):
            valor_historico = row.get(dd_col, None)
            fonte_historica = row.get(fonte_col, "")

            if pd.notna(valor_historico) and str(fonte_historica) == "HISTORICO_REAL":
                return float(valor_historico), "HISTORICO_REAL"

            return obter_stress_fallback(row.get("setor", ""), cenario), "FALLBACK_SETORIAL"

        resultados = df.apply(escolher_stress, axis=1)

        df[stress_col] = resultados.apply(lambda x: x[0])
        df[fonte_final_col] = resultados.apply(lambda x: x[1])

        df[impacto_col] = (
            df["peso_sugerido_pct"] / 100
        ) * df[stress_col]

    impacto_cols = [f"impacto_{c}_pct" for c in CENARIOS]

    df["pior_stress_ativo_pct"] = df[impacto_cols].min(axis=1)
    df["risco_stress_ativo"] = df["pior_stress_ativo_pct"].apply(classificar_risco)
    df["contribuicao_risco_pct"] = abs(df["pior_stress_ativo_pct"])

    total_risco = df["contribuicao_risco_pct"].sum()

    if total_risco > 0:
        df["participacao_no_risco_total_pct"] = (
            df["contribuicao_risco_pct"] / total_risco * 100
        )
    else:
        df["participacao_no_risco_total_pct"] = 0

    return df


def montar_resumo(df):
    hhi = calcular_hhi(df)
    numero_efetivo = calcular_numero_efetivo_ativos(hhi)

    resumo = []

    for cenario in CENARIOS:
        impacto_col = f"impacto_{cenario}_pct"
        fonte_col = f"{cenario}_stress_fonte"

        impacto_total = float(df[impacto_col].sum())

        idx_maior_risco = df[impacto_col].idxmin()

        setor_risco = (
            df.groupby("setor")[impacto_col]
            .sum()
            .sort_values()
        )

        maior_setor_risco = setor_risco.index[0]
        impacto_maior_setor = float(setor_risco.iloc[0])

        peso_historico = float(
            df.loc[df[fonte_col] == "HISTORICO_REAL", "peso_sugerido_pct"].sum()
        )

        peso_fallback = float(
            df.loc[df[fonte_col] == "FALLBACK_SETORIAL", "peso_sugerido_pct"].sum()
        )

        resumo.append({
            "cenario": cenario,
            "queda_estimada_carteira_pct": impacto_total,
            "risco_stress": classificar_risco(impacto_total),
            "perfil_stress": classificar_perfil(impacto_total),
            "maior_contribuidor_risco": df.loc[idx_maior_risco, "ticker"],
            "maior_setor_risco": maior_setor_risco,
            "impacto_maior_setor_pct": impacto_maior_setor,
            "peso_com_historico_real_pct": peso_historico,
            "peso_com_fallback_setorial_pct": peso_fallback,
            "confiabilidade_stress": classificar_confiabilidade_peso(peso_historico),
            "hhi_carteira": hhi,
            "numero_efetivo_ativos": numero_efetivo,
            "peso_top5_pct": float(
                df.sort_values("peso_sugerido_pct", ascending=False)
                .head(5)["peso_sugerido_pct"]
                .sum()
            ),
            "maior_peso_ativo_pct": float(df["peso_sugerido_pct"].max()),
        })

    resumo_df = pd.DataFrame(resumo)

    pior = resumo_df.sort_values("queda_estimada_carteira_pct").iloc[0]

    overview = pd.DataFrame([{
        "pior_cenario_da_carteira": pior["cenario"],
        "queda_pior_cenario_pct": pior["queda_estimada_carteira_pct"],
        "risco_pior_cenario": pior["risco_stress"],
        "perfil_pior_cenario": pior["perfil_stress"],
        "maior_setor_risco_pior_cenario": pior["maior_setor_risco"],
        "maior_contribuidor_pior_cenario": pior["maior_contribuidor_risco"],
        "peso_historico_real_pior_cenario_pct": pior["peso_com_historico_real_pct"],
        "peso_fallback_pior_cenario_pct": pior["peso_com_fallback_setorial_pct"],
        "confiabilidade_pior_cenario": pior["confiabilidade_stress"],
        "hhi_carteira": pior["hhi_carteira"],
        "numero_efetivo_ativos": pior["numero_efetivo_ativos"],
    }])

    return resumo_df, overview


def classificar_confiabilidade_peso(peso_historico):
    if peso_historico >= 80:
        return "ALTA"
    if peso_historico >= 50:
        return "MODERADA"
    if peso_historico > 0:
        return "BAIXA"
    return "SEM BASE HISTÓRICA"


def executar_stress_test():
    print("=" * 70)
    print("STRESS TEST INSTITUCIONAL V4 — HISTÓRICO + FALLBACK")
    print("=" * 70)

    df = preparar_base()
    df = aplicar_stress(df)

    resumo_df, overview = montar_resumo(df)

    Path("output").mkdir(exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    resumo_df.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")
    overview.to_csv(OVERVIEW_FILE, index=False, encoding="utf-8-sig")

    print()
    print("RESUMO POR CENÁRIO:")
    print(
        resumo_df[
            [
                "cenario",
                "queda_estimada_carteira_pct",
                "risco_stress",
                "perfil_stress",
                "peso_com_historico_real_pct",
                "peso_com_fallback_setorial_pct",
                "confiabilidade_stress",
                "maior_contribuidor_risco",
                "maior_setor_risco",
            ]
        ].to_string(index=False)
    )

    print()
    print("PIOR CENÁRIO:")
    print(overview.to_string(index=False))

    print()
    print("MAIORES CONTRIBUIDORES DE RISCO:")
    cols = [
        "ticker",
        "setor",
        "peso_sugerido_pct",
        "pior_stress_ativo_pct",
        "risco_stress_ativo",
        "participacao_no_risco_total_pct",
    ]

    print(
        df.sort_values("participacao_no_risco_total_pct", ascending=False)
        .head(10)[cols]
        .to_string(index=False)
    )

    print()
    print("Arquivos salvos:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)
    print(OVERVIEW_FILE)

    return df


if __name__ == "__main__":
    executar_stress_test()
