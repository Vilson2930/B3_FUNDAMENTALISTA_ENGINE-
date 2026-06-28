# ============================================================
# ai_audit.py
# B3 FUNDAMENTALISTA ENGINE
# Auditoria Institucional com IA — Relatório Executivo
# ============================================================

import os
from pathlib import Path

import pandas as pd
from openai import OpenAI


OUTPUT_DIR = Path("output")
CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"


def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    return pd.read_csv(caminho, encoding="utf-8-sig")


def resumo_numerico(df):
    if df.empty:
        return "Sem dados disponíveis."

    linhas = []

    linhas.append(f"Ativos na carteira: {len(df)}")

    if "peso_sugerido_pct" in df.columns:
        linhas.append(f"Peso total: {df['peso_sugerido_pct'].sum():.2f}%")
        linhas.append(f"Peso Top 5: {df.head(5)['peso_sugerido_pct'].sum():.2f}%")

    if "setor" in df.columns and "peso_sugerido_pct" in df.columns:
        setor = (
            df.groupby("setor")["peso_sugerido_pct"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )

        if not setor.empty:
            linhas.append(f"Maior setor: {setor.index[0]} ({setor.iloc[0]:.2f}%)")

        linhas.append(f"Quantidade de setores: {df['setor'].nunique()}")

    if "score_final_carteira" in df.columns:
        linhas.append(f"Score médio: {df['score_final_carteira'].mean():.2f}")
        linhas.append(f"Maior score: {df['score_final_carteira'].max():.2f}")
        linhas.append(f"Menor score: {df['score_final_carteira'].min():.2f}")

    if "decisao" in df.columns:
        linhas.append("Distribuição por decisão:")
        for decisao, qtd in df["decisao"].value_counts().items():
            linhas.append(f"- {decisao}: {qtd}")

    return "\n".join(linhas)


def preparar_resumo(df, limite=15):
    if df.empty:
        return "Arquivo vazio ou não encontrado."

    colunas = [
        "ranking_carteira",
        "ticker",
        "setor",
        "score_fundamental",
        "score_tecnico",
        "score_final_carteira",
        "rating_carteira",
        "conviccao",
        "prioridade",
        "peso_sugerido_pct",
        "sinal_tecnico",
        "decisao",
        "motivo_decisao",
    ]

    colunas = [c for c in colunas if c in df.columns]

    return df[colunas].head(limite).to_string(index=False)


def gerar_prompt(carteira, diversificada):
    base = diversificada if not diversificada.empty else carteira

    return f"""
Você é um auditor institucional de carteiras quantitativas.

Analise a carteira gerada pelo B3 Fundamentalista Engine.

REGRAS:
- Não prometa retorno.
- Não invente dados.
- Não trate como recomendação absoluta.
- Seja objetivo.
- A auditoria será inserida em um PDF institucional, então escreva pouco e com clareza.

FILOSOFIA DO MOTOR:
- Fundamentalista seleciona empresas de qualidade.
- Técnico avalia momento de entrada.
- Portfolio combina 70% fundamentos e 30% técnico.
- Diversificação controla concentração setorial.

MÉTRICAS CONSOLIDADAS:
{resumo_numerico(base)}

CARTEIRA:
{preparar_resumo(base)}

Gere exatamente neste formato:

NOTA GERAL: X.X/10

DIAGNÓSTICO EXECUTIVO:
Texto de até 5 linhas resumindo a carteira.

QUALIDADE FUNDAMENTALISTA:
Classifique como Alta, Média ou Baixa e explique em até 3 linhas.

QUALIDADE TÉCNICA:
Classifique como Forte, Moderada ou Fraca e explique em até 3 linhas.

DIVERSIFICAÇÃO:
Explique concentração setorial e risco de concentração em até 3 linhas.

PESOS DA CARTEIRA:
Explique se os pesos estão coerentes com score, convicção e risco em até 3 linhas.

PONTOS FORTES:
- ponto 1
- ponto 2
- ponto 3

PONTOS DE ATENÇÃO:
- ponto 1
- ponto 2
- ponto 3

ATIVOS DE MAIOR PRIORIDADE:
- ticker: motivo curto
- ticker: motivo curto
- ticker: motivo curto

ATIVOS QUE EXIGEM CAUTELA:
- ticker: motivo curto
- ticker: motivo curto
- ticker: motivo curto

PARECER FINAL:
Texto de até 6 linhas com conclusão institucional.
"""


def gerar_auditoria_ia():
    OUTPUT_DIR.mkdir(exist_ok=True)

    carteira = carregar_csv(CARTEIRA_FILE)
    diversificada = carregar_csv(DIVERSIFICADA_FILE)

    if carteira.empty:
        texto = "AUDITORIA IA NÃO GERADA: carteira_institucional.csv não encontrado ou vazio."
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print(texto)
        return texto

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        texto = "AUDITORIA IA NÃO GERADA: OPENAI_API_KEY não configurada."
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print(texto)
        return texto

    client = OpenAI(api_key=api_key)

    prompt = gerar_prompt(carteira, diversificada)

    resposta = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um auditor institucional de carteiras quantitativas. "
                    "Escreva de forma objetiva, técnica e conservadora."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.15,
    )

    texto = resposta.choices[0].message.content.strip()

    AUDITORIA_FILE.write_text(texto, encoding="utf-8")

    print("=" * 70)
    print("AUDITORIA IA GERADA")
    print("=" * 70)
    print(texto)

    return texto


if __name__ == "__main__":
    gerar_auditoria_ia()
