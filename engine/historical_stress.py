# ============================================================
# stress_test.py
# B3 FUNDAMENTALISTA ENGINE
# Stress Test Institucional da Carteira
# ============================================================

from pathlib import Path
import pandas as pd


INPUT_FILE = Path("output/carteira_diversificada.csv")
OUTPUT_FILE = Path("output/stress_test.csv")
SUMMARY_FILE = Path("output/stress_test_summary.csv")


STRESS_SETOR = {
    "Construção Civil": {"crise_2008_pct": -65, "covid_2020_pct": -45, "juros_altos_pct": -40},
    "Consumo Cíclico": {"crise_2008_pct": -55, "covid_2020_pct": -40, "juros_altos_pct": -35},
    "Financeiro": {"crise_2008_pct": -55, "covid_2020_pct": -35, "juros_altos_pct": -30},
    "Petróleo, Gás e Biocombustíveis": {"crise_2008_pct": -60, "covid_2020_pct": -50, "juros_altos_pct": -25},
    "Utilidade Pública": {"crise_2008_pct": -30, "covid_2020_pct": -25, "juros_altos_pct": -20},
    "Saúde": {"crise_2008_pct": -25, "covid_2020_pct": -20, "juros_altos_pct": -15},
    "Comunicações": {"crise_2008_pct": -35, "covid_2020_pct": -25, "juros_altos_pct": -20},
    "Bens Industriais": {"crise_2008_pct": -50, "covid_2020_pct": -35, "juros_altos_pct": -30},
    "Materiais Básicos": {"crise_2008_pct": -55, "covid_2020_pct": -35, "juros_altos_pct": -25},
    "Tecnologia da Informação": {"crise_2008_pct": -50, "covid_2020_pct": -45, "juros_altos_pct": -35},
    "Consumo Não Cíclico": {"crise_2008_pct": -30, "covid_2020_pct": -25, "juros_altos_pct": -20},
}

DEFAULT_STRESS = {
    "crise_2008_pct": -45,
    "covid_2020_pct": -35,
    "juros_altos_pct": -30,
}


def carregar_carteira():
    if not INPUT_FILE.exists():
        print(f"Arquivo não encontrado: {INPUT_FILE}")
        return pd.DataFrame()

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def obter_stress_setor(setor, cenario):
    setor = str(setor or "").strip()

    if setor in STRESS_SETOR:
        return STRESS_SETOR[setor][cenario]

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


def classificar_perfil_stress(perda_pct):
    perda = abs(float(perda_pct))

    if perda >= 50:
        return "CARTEIRA AGRESSIVA EM STRESS"
    if perda >= 40:
        return "CARTEIRA MODERADAMENTE AGRESSIVA"
    if perda >= 30:
        return "CARTEIRA BALANCEADA COM RISCO CÍCLICO"

    return "CARTEIRA MAIS DEFENSIVA"


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


def calcular_hhi(df):
    pesos = df["peso_sugerido_pct"] / 100
    return float((pesos ** 2).sum())


def calcular_numero_efetivo_ativos(hhi):
    if hhi <= 0:
        return 0

    return 1 / hhi


def executar_stress_test():
    df = carregar_carteira()

    if df.empty:
        print("Carteira vazia. Stress test não executado.")
        return df

    if "peso_sugerido_pct" not in df.columns:
        raise ValueError("Coluna peso_sugerido_pct não encontrada.")

    if "setor" not in df.columns:
        raise ValueError("Coluna setor não encontrada.")

    df = normalizar_peso(df)

    cenarios = [
        "crise_2008_pct",
        "covid_2020_pct",
        "juros_altos_pct",
    ]

    for cenario in cenarios:
        df[cenario] = df["setor"].apply(
            lambda setor: obter_stress_setor(setor, cenario)
        )

        df[f"impacto_{cenario}"] = (
            df["peso_sugerido_pct"] / 100
        ) * df[cenario]

        df[f"perda_estimada_{cenario}"] = df[f"impacto_{cenario}"]

    df["pior_stress_ativo_pct"] = df[
        [f"impacto_{c}" for c in cenarios]
    ].min(axis=1)

    df["risco_stress_ativo"] = df["pior_stress_ativo_pct"].apply(classificar_risco)

    df["contribuicao_risco_pct"] = abs(df["pior_stress_ativo_pct"])

    total_contribuicao = df["contribuicao_risco_pct"].sum()

    if total_contribuicao > 0:
        df["participacao_no_risco_total_pct"] = (
            df["contribuicao_risco_pct"] / total_contribuicao * 100
        )
    else:
        df["participacao_no_risco_total_pct"] = 0

    hhi = calcular_hhi(df)
    numero_efetivo = calcular_numero_efetivo_ativos(hhi)

    resumo = []

    for cenario in cenarios:
        coluna_impacto = f"impacto_{cenario}"
        impacto_total = float(df[coluna_impacto].sum())

        idx_maior_risco = df[coluna_impacto].idxmin()

        setor_risco = (
            df.groupby("setor")[coluna_impacto]
            .sum()
            .sort_values()
        )

        maior_setor_risco = setor_risco.index[0]
        impacto_maior_setor = float(setor_risco.iloc[0])

        resumo.append({
            "cenario": cenario.replace("_pct", ""),
            "queda_estimada_carteira_pct": impacto_total,
            "risco_stress": classificar_risco(impacto_total),
            "perfil_stress": classificar_perfil_stress(impacto_total),
            "maior_contribuidor_risco": df.loc[idx_maior_risco, "ticker"]
            if "ticker" in df.columns else "N/A",
            "maior_setor_risco": maior_setor_risco,
            "impacto_maior_setor_pct": impacto_maior_setor,
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

    pior_cenario = resumo_df.sort_values("queda_estimada_carteira_pct").iloc[0]

    resumo_geral = pd.DataFrame([{
        "pior_cenario_da_carteira": pior_cenario["cenario"],
        "queda_pior_cenario_pct": pior_cenario["queda_estimada_carteira_pct"],
        "risco_pior_cenario": pior_cenario["risco_stress"],
        "perfil_pior_cenario": pior_cenario["perfil_stress"],
        "maior_setor_risco_pior_cenario": pior_cenario["maior_setor_risco"],
        "maior_contribuidor_pior_cenario": pior_cenario["maior_contribuidor_risco"],
        "hhi_carteira": hhi,
        "numero_efetivo_ativos": numero_efetivo,
    }])

    Path("output").mkdir(exist_ok=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    resumo_df.to_csv(
        SUMMARY_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    resumo_geral.to_csv(
        Path("output/stress_test_overview.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 70)
    print("STRESS TEST INSTITUCIONAL V3")
    print("=" * 70)

    print()
    print("RESUMO POR CENÁRIO:")
    colunas_resumo = [
        "cenario",
        "queda_estimada_carteira_pct",
        "risco_stress",
        "perfil_stress",
        "maior_contribuidor_risco",
        "maior_setor_risco",
        "impacto_maior_setor_pct",
    ]

    print(
        resumo_df[colunas_resumo]
        .to_string(index=False)
    )

    print()
    print("PIOR CENÁRIO DA CARTEIRA:")
    print(
        resumo_geral
        .to_string(index=False)
    )

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
    cols = [c for c in cols if c in df.columns]

    print(
        df.sort_values("participacao_no_risco_total_pct", ascending=False)
        .head(10)[cols]
        .to_string(index=False)
    )

    print()
    print("Arquivos salvos:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)
    print("output/stress_test_overview.csv")

    return df


if __name__ == "__main__":
    executar_stress_test()
