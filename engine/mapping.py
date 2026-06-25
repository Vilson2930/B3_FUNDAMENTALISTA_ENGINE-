# ============================================================
# mapping.py
# B3 FUNDAMENTALISTA ENGINE
# Mapeamento permanente Ticker -> CD_CVM
# ============================================================

from pathlib import Path
import pandas as pd

MAP_DIR = Path("data/mapping")
MAP_DIR.mkdir(parents=True, exist_ok=True)

MAP_FILE = MAP_DIR / "ticker_cvm.csv"


def carregar_mapping():

    if MAP_FILE.exists():

        df = pd.read_csv(
            MAP_FILE,
            dtype={
                "ticker": str,
                "CD_CVM": str
            }
        )

        print(f"Mapping carregado: {len(df)} empresas")

        return df

    print("Nenhum mapping encontrado.")

    return pd.DataFrame(
        columns=[
            "ticker",
            "empresa",
            "CD_CVM",
            "DENOM_CIA",
            "match_score"
        ]
    )


def salvar_mapping(df):

    df = (
        df.drop_duplicates(
            subset=["ticker"],
            keep="first"
        )
        .sort_values("ticker")
        .reset_index(drop=True)
    )

    df.to_csv(
        MAP_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"Mapping salvo: {len(df)} empresas")


def atualizar_mapping(mapping_antigo, novos_matches):

    if mapping_antigo.empty:

        mapping = novos_matches.copy()

    else:

        mapping = pd.concat(
            [
                mapping_antigo,
                novos_matches
            ],
            ignore_index=True
        )

    mapping = (
        mapping
        .sort_values(
            "match_score",
            ascending=False
        )
        .drop_duplicates(
            subset=["ticker"],
            keep="first"
        )
        .reset_index(drop=True)
    )

    salvar_mapping(mapping)

    return mapping


def aplicar_mapping(df_b3, fundamentos, mapping):

    if mapping.empty:

        return pd.DataFrame()

    base = df_b3.merge(
        mapping[
            [
                "ticker",
                "CD_CVM"
            ]
        ],
        on="ticker",
        how="inner"
    )

    base = base.merge(
        fundamentos,
        on="CD_CVM",
        how="inner"
    )

    return base
