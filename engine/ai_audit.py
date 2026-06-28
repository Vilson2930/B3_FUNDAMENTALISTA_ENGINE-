# ============================================================
# ai_audit.py
# B3 FUNDAMENTALISTA ENGINE
# Auditoria Institucional com IA
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


def preparar_resumo(df, limite=20):
    if df.empty:
        return "Arquivo vazio ou não encontrado."

    colunas = [
        "ranking_carteira",
        "ticker",
        "empresa",
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
    resumo_carteira = preparar_resumo(carteira)
    resumo_diversificada = preparar_resumo(diversificada)

    prompt = f"""
Você é um Auditor Institucional de Carteiras Quantitativas.

Analise a carteira gerada pelo B3 Fundamentalista Engine.

FILOSOFIA DO MOTOR:
- O Fundamentalista seleciona as melhores empresas.
- O Técnico avalia o momento de entrada.
- O Portfolio combina 70% fundamento e 30% técnico.
- A Diversificação controla concentração setorial.
- A decisão final deve ser conservadora, institucional e explicável.
- Não invente dados que não estejam na carteira.
- Não prometa retorno.
- Não trate como recomendação absoluta.
- Avalie apenas a qualidade do processo e os riscos observáveis.

CARTEIRA INSTITUCIONAL:
{resumo_carteira}

CARTEIRA DIVERSIFICADA:
{resumo_diversificada}

Gere um relatório profissional com:

1. Nota geral da carteira de 0 a 10.
2. Qualidade fundamentalista.
3. Qualidade técnica das entradas.
4. Diversificação setorial.
5. Coerência dos pesos.
6. Principais pontos fortes.
7. Principais pontos de atenção.
8. Ativos com melhor combinação fundamento + técnico.
9. Ativos que exigem cautela.
10. Parecer executivo final.

Escreva em português do Brasil.
Seja objetivo, profissional e direto.
"""
    return prompt


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
                "content": "Você é um auditor institucional de carteiras quantitativas."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    texto = resposta.choices[0].message.content

    AUDITORIA_FILE.write_text(texto, encoding="utf-8")

    print("=" * 70)
    print("AUDITORIA IA GERADA")
    print("=" * 70)
    print(texto)

    return texto


if __name__ == "__main__":
    gerar_auditoria_ia()
