# ============================================================
# b3_data.py
# B3 FUNDAMENTALISTA ENGINE
# Coleta B3 via BRAPI + Setor oficial via data/setores_b3.csv
# ============================================================

from pathlib import Path
import requests
import pandas as pd


URL_BRAPI = "https://brapi.dev/api/quote/list"

SETOR_FILE = Path("data/setores_b3.csv")
OUTPUT_AUDITORIA_SETOR = Path("output/auditoria_setores.csv")


def carregar_setores_b3():
    if not SETOR_FILE.exists():
        print("Arquivo data/setores_b3.csv não encontrado. Usando setor da BRAPI como fallback.")
        return pd.DataFrame()

    setores = pd.read_csv(SETOR_FILE, encoding="utf-8-sig")
    setores.columns = [str(c).strip() for c in setores.columns]

    if "ticker" not in setores.columns:
        print("data/setores_b3.csv sem coluna ticker. Ignorando.")
        return pd.DataFrame()

    setores["ticker"] = setores["ticker"].astype(str).str.upper().str.strip()

    return setores


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

    # Somente tickers comuns da B3
    df = df[df["ticker"].str.len() <= 6].copy()

    setores_b3 = carregar_setores_b3()

    if not setores_b3.empty:
        colunas_setor = [
            c for c in [
                "ticker",
                "setor_b3",
                "subsetor_b3",
                "segmento_b3"
            ]
            if c in setores_b3.columns
        ]

        df = df.merge(
            setores_b3[colunas_setor],
            on="ticker",
            how="left"
        )

        df["setor"] = df["setor_b3"].fillna(df["setor_original_brapi"])
        df["setor_fonte"] = df["setor_b3"].apply(
            lambda x: "B3_OFICIAL" if pd.notna(x) and str(x).strip() else "BRAPI_FALLBACK"
        )

    else:
        df["setor"] = df["setor_original_brapi"]
        df["subsetor_b3"] = ""
        df["segmento_b3"] = ""
        df["setor_fonte"] = "BRAPI_FALLBACK"

    df["setor"] = df["setor"].fillna("Não Classificado")

    Path("output").mkdir(exist_ok=True)

    auditoria = df[[
        "ticker",
        "empresa",
        "setor_original_brapi",
        "setor",
        "setor_fonte",
        "subsetor_b3",
        "segmento_b3",
    ]].copy()

    auditoria.to_csv(
        OUTPUT_AUDITORIA_SETOR,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Ativos encontrados: {len(df)}")
    print()
    print("AUDITORIA DE SETORES SALVA EM:")
    print(OUTPUT_AUDITORIA_SETOR)

    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = carregar_empresas_b3()

    print()
    print(df.head())
