# ============================================================
# b3_data.py
# B3 FUNDAMENTALISTA ENGINE
# Coleta de ativos da B3 via BRAPI + Setores corrigidos
# ============================================================

import requests
import pandas as pd


URL_BRAPI = "https://brapi.dev/api/quote/list"


SETOR_MANUAL_B3 = {
    "JHSF3": "Construção Civil",
    "TRIS3": "Construção Civil",
    "PETR4": "Petróleo, Gás e Biocombustíveis",
    "RECV3": "Petróleo, Gás e Biocombustíveis",
    "TAEE4": "Utilidade Pública",
    "ISAE4": "Utilidade Pública",
    "POMO4": "Bens Industriais",
    "VULC3": "Consumo Cíclico",
    "AZZA3": "Consumo Cíclico",
    "TFCO4": "Consumo Cíclico",
    "GMAT3": "Consumo Não Cíclico",
    "SEER3": "Educação",
    "CSED3": "Educação",
    "VTRU3": "Educação",
    "BLAU3": "Saúde",
    "FIQE3": "Comunicações",
    "RANI3": "Materiais Básicos",
    "TGMA3": "Bens Industriais",
    "WIZC3": "Financeiro",
    "CSUD3": "Tecnologia",
}


def corrigir_setor(row):
    ticker = str(row.get("ticker", "")).upper().strip()

    if ticker in SETOR_MANUAL_B3:
        return SETOR_MANUAL_B3[ticker]

    setor = row.get("setor", "")

    if pd.isna(setor) or str(setor).strip() == "":
        return "Não Classificado"

    return str(setor).strip()


def carregar_empresas_b3():

    print("=" * 70)
    print("COLETANDO EMPRESAS DA B3")
    print("=" * 70)

    response = requests.get(URL_BRAPI, timeout=120)
    response.raise_for_status()

    dados = response.json()
    ativos = dados.get("stocks", [])

    registros = []

    for ativo in ativos:
        registros.append({
            "ticker": ativo.get("stock"),
            "empresa": ativo.get("name"),
            "setor_original_brapi": ativo.get("sector"),
            "setor": ativo.get("sector"),
            "market_cap": ativo.get("market_cap"),
            "volume": ativo.get("volume"),
            "tipo": ativo.get("type"),
        })

    df = pd.DataFrame(registros)

    df = df.dropna(subset=["ticker"])

    df["ticker"] = (
        df["ticker"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["market_cap"] = pd.to_numeric(df["market_cap"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    df = df[df["ticker"].str.len() <= 6]

    df["setor"] = df.apply(corrigir_setor, axis=1)

    df["setor_corrigido_manual"] = df["ticker"].apply(
        lambda x: "SIM" if x in SETOR_MANUAL_B3 else "NÃO"
    )

    print(f"Ativos encontrados: {len(df)}")

    print()
    print("AUDITORIA DE SETORES MANUAIS:")
    print(
        df[df["setor_corrigido_manual"] == "SIM"][
            ["ticker", "empresa", "setor_original_brapi", "setor"]
        ].head(50)
    )

    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = carregar_empresas_b3()

    print()
    print(df.head())
