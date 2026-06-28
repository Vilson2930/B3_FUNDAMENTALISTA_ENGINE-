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


# ============================================================
# CENÁRIOS DE STRESS POR SETOR
# Valores representam queda estimada em %
# ============================================================

STRESS_SETOR = {
    "Construção Civil": {
        "crise_2008_pct": -65,
        "covid_2020_pct": -45,
        "juros_altos_pct": -40,
    },
    "Consumo Cíclico": {
        "crise_2008_pct": -55,
        "covid_2020_pct": -40,
        "juros_altos_pct": -35,
    },
    "Financeiro": {
        "crise_2008_pct": -55,
        "covid_2020_pct": -35,
        "juros_altos_pct": -30,
    },
    "Petróleo, Gás e Biocombustíveis": {
        "crise_2008_pct": -60,
        "covid_2020_pct": -50,
        "juros_altos_pct": -25,
    },
    "Utilidade Pública": {
        "crise_2008_pct": -30,
        "covid_2020_pct": -25,
        "juros_altos_pct": -20,
    },
    "Saúde": {
        "crise_2008_pct": -25,
        "covid_2020_pct": -20,
        "juros_altos_pct": -15,
    },
    "Comunicações": {
        "crise_2008_pct": -35,
        "covid_2020_pct": -25,
        "juros_altos_pct": -20,
    },
    "Bens Industriais": {
        "crise_2008_pct": -50,
        "covid_2020_pct": -35,
        "juros_altos_pct": -30,
    },
    "Materiais Básicos": {
        "crise_2008_pct": -55,
        "covid_2020_pct": -35,
        "juros_altos_pct": -25,
    },
    "Tecnologia da Informação": {
        "crise_2008_pct": -50,
        "covid_2020_pct": -45,
        "juros_altos_pct": -35,
    },
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


def classificar_risco_stress(perda):
    perda_abs = abs(float(perda))

    if perda_abs >= 50:
        return "RISCO EXTREMO"

    if perda_abs >= 40:
        return "RISCO ALTO"

    if perda_abs >= 30:
        return "RISCO MODERADO"

    return "RISCO CONTROLADO"


def executar_stress_test():
    df = carregar_carteira()

    if df.empty:
        print("Carteira vazia. Stress test não executado.")
        return df

    if "peso_sugerido_pct" not in df.columns:
        raise ValueError("Coluna peso_sugerido_pct não encontrada.")

    if "setor" not in df.columns:
        raise ValueError("Coluna setor não encontrada.")

    df = df.copy()

    df["peso_sugerido_pct"] = pd.to_numeric(
        df["peso_sugerido_pct"],
        errors="coerce"
    ).fillna(0)

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

    resumo = []

    for cenario in cenarios:
        impacto_total = df[f"impacto_{cenario}"].sum()

        resumo.append({
            "cenario": cenario.replace("_pct", ""),
            "queda_estimada_carteira_pct": impacto_total,
            "risco_stress": classificar_risco_stress(impacto_total),
            "maior_contribuidor_risco": df.loc[
                df[f"impacto_{cenario}"].idxmin(),
                "ticker"
            ] if "ticker" in df.columns else "N/A",
            "maior_setor_risco": df.loc[
                df[f"impacto_{cenario}"].idxmin(),
                "setor"
            ],
        })

    resumo_df = pd.DataFrame(resumo)

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

    print("=" * 70)
    print("STRESS TEST INSTITUCIONAL")
    print("=" * 70)

    print()
    print("RESUMO DO STRESS TEST:")
    print(resumo_df)

    print()
    print("Arquivos salvos:")
    print(OUTPUT_FILE)
    print(SUMMARY_FILE)

    return df


if __name__ == "__main__":
    executar_stress_test()
