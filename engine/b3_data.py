# ============================================================
# b3_data.py
# B3 FUNDAMENTALISTA ENGINE
# Coleta de ativos da B3 via BRAPI
# ============================================================

import requests
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

URL_BRAPI = "https://brapi.dev/api/quote/list"

# ============================================================
# DOWNLOAD LISTA B3
# ============================================================

def carregar_empresas_b3():

    print("=" * 70)
    print("COLETANDO EMPRESAS DA B3")
    print("=" * 70)

    response = requests.get(
        URL_BRAPI,
        timeout=120
    )

    response.raise_for_status()

    dados = response.json()

    ativos = dados.get("stocks", [])

    registros = []

    for ativo in ativos:

        registros.append({

            "ticker": ativo.get("stock"),

            "empresa": ativo.get("name"),

            "setor": ativo.get("sector"),

            "market_cap": ativo.get("market_cap"),

            "volume": ativo.get("volume"),

            "tipo": ativo.get("type")

        })

    df = pd.DataFrame(registros)

    # --------------------------------------------------------
    # LIMPEZA
    # --------------------------------------------------------

    df = df.dropna(subset=["ticker"])

    df["market_cap"] = pd.to_numeric(
        df["market_cap"],
        errors="coerce"
    )

    df["volume"] = pd.to_numeric(
        df["volume"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # SOMENTE AÇÕES
    # --------------------------------------------------------

    df = df[
        df["ticker"].str.len() <= 6
    ]

    print(f"Ativos encontrados: {len(df)}")

    return df.reset_index(drop=True)

# ============================================================
# TESTE LOCAL
# ============================================================

if __name__ == "__main__":

    df = carregar_empresas_b3()

    print()
    print(df.head())
