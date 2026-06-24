# ============================================================
# indicators.py
# B3 FUNDAMENTALISTA ENGINE
# Núcleo Quantitativo + EBIT + Endividamento
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
    ][["CD_CVM", "DENOM_CIA", "VL_CONTA"]].rename(columns={"VL_CONTA": "receita"})

    lucro = df_dre[
        (df_dre["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_dre["CD_CONTA"] == "3.11")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "lucro_liquido"})

    ebit = df_dre[
        (df_dre["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_dre["CD_CONTA"] == "3.05")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "ebit"})

    ativo = df_bpa[
        (df_bpa["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpa["CD_CONTA"] == "1")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "ativo_total"})

    patrimonio = df_bpp[
        (df_bpp["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpp["CD_CONTA"] == "2.03")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "patrimonio_liquido"})

    passivo_circ = df_bpp[
        (df_bpp["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpp["CD_CONTA"] == "2.01")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "passivo_circulante"})

    passivo_nao_circ = df_bpp[
        (df_bpp["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpp["CD_CONTA"] == "2.02")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "passivo_nao_circulante"})

    caixa = df_bpa[
        (df_bpa["ORDEM_EXERC"] == "ÚLTIMO") &
        (df_bpa["CD_CONTA"] == "1.01.01")
    ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": "caixa"})

    fundamentos = receita.merge(lucro, on="CD_CVM", how="inner")
    fundamentos = fundamentos.merge(ebit, on="CD_CVM", how="left")
    fundamentos = fundamentos.merge(ativo, on="CD_CVM", how="inner")
    fundamentos = fundamentos.merge(patrimonio, on="CD_CVM", how="inner")
    fundamentos = fundamentos.merge(passivo_circ, on="CD_CVM", how="left")
    fundamentos = fundamentos.merge(passivo_nao_circ, on="CD_CVM", how="left")
    fundamentos = fundamentos.merge(caixa, on="CD_CVM", how="left")

    fundamentos = fundamentos.groupby("CD_CVM", as_index=False).agg({
        "DENOM_CIA": "first",
        "receita": "max",
        "lucro_liquido": "max",
        "ebit": "max",
        "ativo_total": "max",
        "patrimonio_liquido": "max",
        "passivo_circulante": "max",
        "passivo_nao_circulante": "max",
        "caixa": "max",
    })

    fundamentos["passivo_total"] = (
        fundamentos["passivo_circulante"].fillna(0) +
        fundamentos["passivo_nao_circulante"].fillna(0)
    )

    fundamentos["caixa"] = fundamentos["caixa"].fillna(0)

    return fundamentos


def calcular_crescimento(dados_cvm):
    df_dre = dados_cvm["dre"]

    dre_base = df_dre[
        df_dre["ORDEM_EXERC"].isin(["ÚLTIMO", "PENÚLTIMO"])
    ].copy()

    def extrair(ordem, conta, nome):
        return dre_base[
            (dre_base["ORDEM_EXERC"] == ordem) &
            (dre_base["CD_CONTA"] == conta)
        ][["CD_CVM", "VL_CONTA"]].rename(columns={"VL_CONTA": nome})

    crescimento = extrair("ÚLTIMO", "3.01", "receita_atual")
    crescimento = crescimento.merge(extrair("PENÚLTIMO", "3.01", "receita_anterior"), on="CD_CVM", how="left")
    crescimento = crescimento.merge(extrair("ÚLTIMO", "3.11", "lucro_atual"), on="CD_CVM", how="left")
    crescimento = crescimento.merge(extrair("PENÚLTIMO", "3.11", "lucro_anterior"), on="CD_CVM", how="left")

    crescimento = crescimento.groupby("CD_CVM", as_index=False).max(numeric_only=True)

    crescimento["crescimento_receita"] = (
        (crescimento["receita_atual"] - crescimento["receita_anterior"]) /
        crescimento["receita_anterior"].abs()
    )

    crescimento["crescimento_lucro"] = (
        (crescimento["lucro_atual"] - crescimento["lucro_anterior"]) /
        crescimento["lucro_anterior"].abs()
    )

    crescimento = crescimento.replace([np.inf, -np.inf], np.nan)

    crescimento["crescimento_receita"] = crescimento["crescimento_receita"].fillna(0).clip(-1, 2)
    crescimento["crescimento_lucro"] = crescimento["crescimento_lucro"].fillna(0).clip(-1, 2)

    return crescimento[["CD_CVM", "crescimento_receita", "crescimento_lucro"]]


def calcular_indicadores(df):
    df = df.copy()

    df["roe"] = df["lucro_liquido"] / df["patrimonio_liquido"]
    df["roa"] = df["lucro_liquido"] / df["ativo_total"]
    df["margem_liquida"] = df["lucro_liquido"] / df["receita"]

    df["divida_liquida"] = df["passivo_total"] - df["caixa"]
    df["divida_patrimonio"] = df["divida_liquida"] / df["patrimonio_liquido"]

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
            score = SequenceMatcher(None, b3["nome_limpo"], cvm["nome_limpo"]).ratio()

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
        (df["ebit"] > 0) &
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

    crescimento = calcular_crescimento(dados_cvm)

    fundamentos = fundamentos.merge(
        crescimento,
        on="CD_CVM",
        how="left"
    )

    fundamentos["crescimento_receita"] = fundamentos["crescimento_receita"].fillna(0)
    fundamentos["crescimento_lucro"] = fundamentos["crescimento_lucro"].fillna(0)

    base = cruzar_b3_cvm(df_b3, fundamentos)
    base = aplicar_filtro(base)
    base = deduplicar_por_empresa(base)

    print(f"Empresas finais: {len(base)}")

    return base
