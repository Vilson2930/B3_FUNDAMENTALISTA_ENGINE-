# ============================================================
# b3_data.py
# B3 FUNDAMENTALISTA ENGINE
# Coleta B3 via BRAPI + Setor oficial via setores_b3.csv
# ============================================================

from pathlib import Path
import requests
import pandas as pd


URL_BRAPI = "https://brapi.dev/api/quote/list"

ROOT_DIR = Path(__file__).resolve().parent.parent
SETOR_FILE = ROOT_DIR / "setores_b3.csv"
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_AUDITORIA_SETOR = OUTPUT_DIR / "auditoria_setores.csv"


def carregar_setores_b3():
    if not SETOR_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo oficial de setores não encontrado: {SETOR_FILE}"
        )

    setores = pd.read_csv(SETOR_FILE, encoding="utf-8-sig")
    setores.columns = [str(c).strip() for c in setores.columns]

    colunas_obrigatorias = ["ticker", "setor_b3", "subsetor_b3", "segmento_b3"]

    for coluna in colunas_obrigatorias:
        if coluna not in setores.columns:
            raise ValueError(
                f"setores_b3.csv precisa conter a coluna obrigatória: {coluna}"
            )

    setores["ticker"] = setores["ticker"].astype(str).str.upper().str.strip()

    setores["setor_b3"] = setores["setor_b3"].astype(str).str.strip()
    setores["subsetor_b3"] = setores["subsetor_b3"].astype(str).str.strip()
    setores["segmento_b3"] = setores["segmento_b3"].astype(str).str.strip()

    setores = setores.drop_duplicates(subset=["ticker"], keep="first")

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

    df = df[df["ticker"].str.len() <= 6].copy()

    setores_b3 = carregar_setores_b3()

    df = df.merge(
        setores_b3[["ticker", "setor_b3", "subsetor_b3", "segmento_b3"]],
        on="ticker",
        how="left"
    )

    df["setor"] = df["setor_b3"].where(
        df["setor_b3"].notna() & (df["setor_b3"].astype(str).str.strip() != ""),
        df["setor_original_brapi"]
    )

    df["setor_fonte"] = df["setor_b3"].apply(
        lambda x: "B3_OFICIAL" if pd.notna(x) and str(x).strip() != "" else "BRAPI_FALLBACK"
    )

    df["setor"] = df["setor"].fillna("Não Classificado")
    df["subsetor_b3"] = df["subsetor_b3"].fillna("")
    df["segmento_b3"] = df["segmento_b3"].fillna("")

    OUTPUT_DIR.mkdir(exist_ok=True)

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
    print("ARQUIVO DE SETORES USADO:")
    print(SETOR_FILE)
    print()
    print("AUDITORIA DE SETORES SALVA EM:")
    print(OUTPUT_AUDITORIA_SETOR)

    print()
    print("VALIDAÇÃO DE SETORES PRIORITÁRIOS:")
    tickers_teste = ["JHSF3", "CYRE3", "LAVV3", "PETR4", "SEER3", "ISAE4", "VULC3"]
    cols = ["ticker", "setor_original_brapi", "setor", "setor_fonte"]

    print(
        df[df["ticker"].isin(tickers_teste)][cols]
        .sort_values("ticker")
        .to_string(index=False)
    )

    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = carregar_empresas_b3()

    print()
    print(df.head())
