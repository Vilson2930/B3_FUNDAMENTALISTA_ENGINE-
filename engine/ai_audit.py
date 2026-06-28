# ============================================================
# ai_audit.py
# B3 FUNDAMENTALISTA ENGINE
# AI Institutional Audit — Research Committee Report V3
# ============================================================

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from openai import OpenAI


OUTPUT_DIR = Path("output")
CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"

# Limites de referência usados apenas para auditoria qualitativa.
# Não alteram a carteira, só dão contexto para a IA interpretar os números.
LIMITE_SETOR_REFERENCIA = 25.0
LIMITE_TOP5_REFERENCIA = 45.0
LIMITE_ATIVO_REFERENCIA = 10.0


def carregar_csv(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(caminho, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(caminho)

    df.columns = [str(c).strip() for c in df.columns]
    return df


def fmt_pct(valor):
    try:
        return f"{float(valor):.2f}%"
    except Exception:
        return "N/A"


def fmt_num(valor):
    try:
        return f"{float(valor):.2f}"
    except Exception:
        return "N/A"


def serie_numerica(df, coluna):
    if coluna not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(df[coluna], errors="coerce")


def calcular_metricas(df):
    if df.empty:
        return {
            "qtd_ativos": 0,
            "peso_total": 0,
            "peso_top5": 0,
            "maior_setor": "N/A",
            "peso_maior_setor": 0,
            "qtd_setores": 0,
            "score_medio": 0,
            "score_max": 0,
            "score_min": 0,
            "maior_ativo": "N/A",
            "maior_peso_ativo": 0,
            "decisoes": {},
            "conviccoes": {},
            "ratings": {},
            "status_setor": "N/A",
            "status_top5": "N/A",
            "status_ativo": "N/A",
        }

    peso = serie_numerica(df, "peso_sugerido_pct")
    score = serie_numerica(df, "score_final_carteira")

    qtd_ativos = len(df)
    peso_total = peso.sum() if not peso.empty else 0
    peso_top5 = peso.head(5).sum() if not peso.empty else 0

    maior_ativo = "N/A"
    maior_peso_ativo = 0

    if "ticker" in df.columns and not peso.empty and peso.notna().any():
        idx_maior = peso.idxmax()
        maior_ativo = str(df.loc[idx_maior, "ticker"])
        maior_peso_ativo = float(peso.loc[idx_maior])

    maior_setor = "N/A"
    peso_maior_setor = 0
    qtd_setores = 0

    if "setor" in df.columns and "peso_sugerido_pct" in df.columns:
        setores = (
            df.assign(peso_tmp=peso)
            .groupby("setor")["peso_tmp"]
            .sum()
            .sort_values(ascending=False)
        )

        qtd_setores = df["setor"].nunique()

        if not setores.empty:
            maior_setor = str(setores.index[0])
            peso_maior_setor = float(setores.iloc[0])

    decisoes = {}
    if "decisao" in df.columns:
        decisoes = df["decisao"].fillna("N/A").value_counts().to_dict()

    conviccoes = {}
    if "conviccao" in df.columns:
        conviccoes = df["conviccao"].fillna("N/A").value_counts().to_dict()

    ratings = {}
    if "rating_carteira" in df.columns:
        ratings = df["rating_carteira"].fillna("N/A").value_counts().to_dict()

    status_setor = (
        "ACEITÁVEL"
        if peso_maior_setor <= LIMITE_SETOR_REFERENCIA
        else "ACIMA DO LIMITE"
    )

    status_top5 = (
        "ACEITÁVEL"
        if peso_top5 <= LIMITE_TOP5_REFERENCIA
        else "CONCENTRADO"
    )

    status_ativo = (
        "ACEITÁVEL"
        if maior_peso_ativo <= LIMITE_ATIVO_REFERENCIA
        else "ACIMA DO LIMITE"
    )

    return {
        "qtd_ativos": qtd_ativos,
        "peso_total": peso_total,
        "peso_top5": peso_top5,
        "maior_setor": maior_setor,
        "peso_maior_setor": peso_maior_setor,
        "qtd_setores": qtd_setores,
        "score_medio": score.mean() if not score.empty else 0,
        "score_max": score.max() if not score.empty else 0,
        "score_min": score.min() if not score.empty else 0,
        "maior_ativo": maior_ativo,
        "maior_peso_ativo": maior_peso_ativo,
        "decisoes": decisoes,
        "conviccoes": conviccoes,
        "ratings": ratings,
        "status_setor": status_setor,
        "status_top5": status_top5,
        "status_ativo": status_ativo,
    }


def preparar_resumo_tabela(df, limite=15):
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

    if not colunas:
        return df.head(limite).to_string(index=False)

    resumo = df[colunas].head(limite).copy()

    for col in ["score_fundamental", "score_tecnico", "score_final_carteira", "peso_sugerido_pct"]:
        if col in resumo.columns:
            resumo[col] = pd.to_numeric(resumo[col], errors="coerce").round(2)

    return resumo.to_string(index=False)


def formatar_dicionario(nome, dados):
    linhas = [nome]

    if not dados:
        linhas.append("- N/A")
        return "\n".join(linhas)

    for chave, valor in dados.items():
        linhas.append(f"- {chave}: {valor}")

    return "\n".join(linhas)


def resumo_metricas(metricas):
    linhas = []

    linhas.append(f"Ativos na carteira: {metricas['qtd_ativos']}")
    linhas.append(f"Peso total: {fmt_pct(metricas['peso_total'])}")
    linhas.append(f"Score médio: {fmt_num(metricas['score_medio'])}")
    linhas.append(f"Maior score: {fmt_num(metricas['score_max'])}")
    linhas.append(f"Menor score: {fmt_num(metricas['score_min'])}")
    linhas.append("")

    linhas.append("Concentração por ativo:")
    linhas.append(f"- Maior ativo: {metricas['maior_ativo']} ({fmt_pct(metricas['maior_peso_ativo'])})")
    linhas.append(f"- Limite de referência por ativo: {fmt_pct(LIMITE_ATIVO_REFERENCIA)}")
    linhas.append(f"- Status: {metricas['status_ativo']}")
    linhas.append("")

    linhas.append("Concentração Top 5:")
    linhas.append(f"- Peso Top 5: {fmt_pct(metricas['peso_top5'])}")
    linhas.append(f"- Limite de referência Top 5: {fmt_pct(LIMITE_TOP5_REFERENCIA)}")
    linhas.append(f"- Status: {metricas['status_top5']}")
    linhas.append("")

    linhas.append("Concentração setorial:")
    linhas.append(f"- Quantidade de setores: {metricas['qtd_setores']}")
    linhas.append(f"- Maior setor: {metricas['maior_setor']} ({fmt_pct(metricas['peso_maior_setor'])})")
    linhas.append(f"- Limite de referência por setor: {fmt_pct(LIMITE_SETOR_REFERENCIA)}")
    linhas.append(f"- Status: {metricas['status_setor']}")
    linhas.append("")

    linhas.append(formatar_dicionario("Distribuição por decisão:", metricas["decisoes"]))
    linhas.append("")
    linhas.append(formatar_dicionario("Distribuição por convicção:", metricas["conviccoes"]))
    linhas.append("")
    linhas.append(formatar_dicionario("Distribuição por rating:", metricas["ratings"]))

    return "\n".join(linhas)


def gerar_prompt(carteira, diversificada):
    base = diversificada if not diversificada.empty else carteira
    metricas = calcular_metricas(base)

    prompt = f"""
Você é o Chief Investment Officer (CIO) de uma gestora quantitativa especializada em ações brasileiras.

Sua função é auditar a carteira produzida pelo B3 Fundamentalista Engine como se estivesse preparando um parecer para um Comitê de Investimentos.

IMPORTANTE:
- Não faça recomendação absoluta de compra ou venda.
- Não prometa retorno.
- Não invente informações.
- Não estime rentabilidade futura.
- Use apenas os dados enviados.
- Seja objetivo, técnico e conservador.
- O texto será inserido em um PDF institucional, portanto deve ser enxuto e bem estruturado.

FILOSOFIA DO MOTOR:
- Fundamentalista: seleciona empresas com base em qualidade, valuation, crescimento, rentabilidade, alavancagem e moat.
- Técnico: avalia o momento de entrada.
- Portfolio: combina 70% fundamentos e 30% análise técnica.
- Diversificação: controla concentração setorial e reduz dependência de poucos setores.
- IA: atua como auditoria independente do processo, sem alterar a carteira.

LIMITES DE REFERÊNCIA DA AUDITORIA:
- Peso máximo de referência por ativo: {fmt_pct(LIMITE_ATIVO_REFERENCIA)}
- Peso máximo de referência por setor: {fmt_pct(LIMITE_SETOR_REFERENCIA)}
- Peso máximo de referência do Top 5: {fmt_pct(LIMITE_TOP5_REFERENCIA)}

MÉTRICAS CONSOLIDADAS:
{resumo_metricas(metricas)}

CARTEIRA AUDITADA:
{preparar_resumo_tabela(base)}

GERE O RELATÓRIO EXATAMENTE NESTA ESTRUTURA:

NOTA GERAL: X.X/10
Explique a nota em até quatro linhas. A nota não pode parecer arbitrária: relacione fundamentos, técnico, diversificação e concentração.

COMPOSIÇÃO DA NOTA:
Fundamentos: X/10 — justificativa curta
Técnico: X/10 — justificativa curta
Diversificação: X/10 — justificativa curta
Governança: X/10 — justificativa curta
Consistência: X/10 — justificativa curta

DIAGNÓSTICO EXECUTIVO:
Um único parágrafo de até cinco linhas, interpretando a carteira sem repetir mecanicamente os números.

PONTOS FORTES:
- Até cinco bullets objetivos.

PONTOS DE ATENÇÃO:
- Até cinco bullets objetivos.

RISCOS PRIORIZADOS:
- ALTO: risco principal, se houver. Explique em uma linha.
- MÉDIO: risco relevante, se houver. Explique em uma linha.
- BAIXO: risco monitorável, se houver. Explique em uma linha.

INTERPRETAÇÃO DA CONCENTRAÇÃO:
Explique se o maior setor, o maior ativo e o Top 5 estão dentro ou fora dos limites de referência informados. Não apenas repita os números; interprete o significado.

ATIVOS PRIORITÁRIOS:
- Liste até cinco ativos com motivo em uma linha cada.

ATIVOS EM OBSERVAÇÃO:
- Liste até cinco ativos com motivo em uma linha cada.

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: APROVADO/ATENÇÃO — justificativa curta
Timing Técnico: APROVADO/ATENÇÃO — justificativa curta
Diversificação: APROVADO/ATENÇÃO — justificativa curta
Governança: APROVADO/ATENÇÃO — justificativa curta
Controle de Risco: APROVADO/ATENÇÃO — justificativa curta

PARECER FINAL:
Um parágrafo curto, objetivo e institucional. Deve explicar a principal mensagem da auditoria e a ação de monitoramento mais importante, sem recomendar compra ou venda.
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
                "content": (
                    "Você é o CIO de uma gestora quantitativa. "
                    "Sua função é auditar carteiras com linguagem técnica, conservadora e objetiva. "
                    "Nunca prometa retorno e nunca invente dados."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.12,
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
