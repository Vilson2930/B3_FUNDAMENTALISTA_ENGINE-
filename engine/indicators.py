# ============================================================
# indicators.py
# B3 FUNDAMENTALISTA ENGINE
# Núcleo Quantitativo
# ============================================================

import pandas as pd
import numpy as np
import re
from difflib import SequenceMatcher


def limpar_nome_empresa(nome):
    nome = str(nome).upper()

    remover = [
        "S.A.", "S/A", "SA", ".", "-", ",",
        "PARTICIPACOES", "PARTICIPAÇÕES",
        "HOLDING", "CIA", "COMPANHIA"
    ]

    for item in remover:
        nome = nome.replace(item, " ")

    nome = re.sub(r"\s+", " ", nome)
    return nome.strip()


def extrair_fundamentos(dados_cvm):
    df_dre = dados_cvm["dre"]
    df_bpa = dados_cvm["bpa"]
    df_bpp = dados_cvm["bpp"]

    receita = df_dre[
        (df_dre["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_dre["CD_CONTA"] == "3.01")
    ][["CD_CVM", "DENOM_CIA", "VL_CONTA"]].rename(
        columns={"VL_CONTA": "receita"}
    )

    lucro = df_dre[
        (df_dre["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_dre["CD_CONTA"] == "3.11")
    ][["CD_CVM", "VL_CONTA"]].rename(
        columns={"VL_CONTA": "lucro_liquido"}
    )

    ativo = df_bpa[
        (df_bpa["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpa["CD_CONTA"] == "1")
    ][["CD_CVM", "VL_CONTA"]].rename(
        columns={"VL_CONTA": "ativo_total"}
    )

    patrimonio = df_bpp[
        (df_bpp["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpp["CD_CONTA"] == "2.03")
    ][["CD_CVM", "VL_CONTA"]].rename(
        columns={"VL_CONTA": "patrimonio_liquido"}
    )

    fundamentos = receita.merge(lucro, on="CD_CVM", how="inner")
    fundamentos = fundamentos.merge(ativo, on="CD_CVM", how="inner")
    fundamentos = fundamentos.merge(patrimonio, on="CD_CVM", how="inner")

    fundamentos = fundamentos.drop_duplicates(subset=["CD_CVM"])

    return fundamentos


def calcular_indicadores(df):
    df = df.copy()

    df["roe"] = df["lucro_liquido"] / df["patrimonio_liquido"]
    df["roa"] = df["lucro_liquido"] / df["ativo_total"]
    df["margem_liquida"] = df["lucro_liquido"] / df["receita"]

    df = df.replace([np.inf, -np.inf], np.nan)

    return df


def cruzar_b3_cvm(df_b3, df_fundamentos):
    df_b3 = df_b3.copy()
    df_fundamentos = df_fundamentos.copy()

    df_b3["nome_limpo"] = df_b3["empresa"].apply(limpar_nome_empresa)
    df_fundamentos["nome_limpo"] = df_fundamentos["DENOM_CIA"].apply(limpar_nome_empresa)

    matches = []

    for _, b3 in df_b3.iterrows():
        melhor_score = 0
        melhor = None

        for _, cvm in df_fundamentos.iterrows():
            score = SequenceMatcher(
                None,
                b3["nome_limpo"],
                cvm["nome_limpo"]
            ).ratio()

            if score > melhor_score:
                melhor_score = score
                melhor = cvm

        if melhor_score >= 0.75 and melhor is not None:
            registro = b3.to_dict()
            registro.update(melhor.to_dict())
            registro["match_score"] = melhor_score
            matches.append(registro)

    return pd.DataFrame(matches)


def aplicar_filtro(df):
    df = df.copy()

    df = df[
        (df["market_cap"] > 500_000_000) &
        (df["volume"] > 100000) &
        (df["receita"] > 0) &
        (df["lucro_liquido"] > 0) &
        (df["patrimonio_liquido"] > 0) &
        (df["ativo_total"] > 0) &
        (df["roe"] > 0) &
        (df["roe"] <= 1.00) &
        (df["roa"] > 0) &
        (df["roa"] <= 0.50) &
        (df["margem_liquida"] > 0) &
        (df["margem_liquida"] <= 1.00)
    ].copy()

    return df


def deduplicar_por_empresa(df):
    df = df.copy()

    df = df.sort_values("volume", ascending=False)

    df = df.drop_duplicates(
        subset=["DENOM_CIA"],
        keep="first"
    )

    return df.reset_index(drop=True)


def construir_base_fundamentalista(df_b3, dados_cvm):
    fundamentos = extrair_fundamentos(dados_cvm)

    fundamentos = calcular_indicadores(fundamentos)

    base = cruzar_b3_cvm(df_b3, fundamentos)

    base = aplicar_filtro(base)

    base = deduplicar_por_empresa(base)

    print(f"Empresas finais: {len(base)}")

    return base
