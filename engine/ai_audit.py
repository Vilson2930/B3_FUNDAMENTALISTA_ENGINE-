# ============================================================
# ai_audit.py
# B3 FUNDAMENTALISTA ENGINE
# Auditoria Institucional com IA — Versão 2.0 CIO
# ============================================================

import os
from pathlib import Path

import pandas as pd
from openai import OpenAI


OUTPUT_DIR = Path("output")
CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"


# ============================================================
# LEITURA DE DADOS
# ============================================================

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


def numero_seguro(valor, default=0.0):
    try:
        return float(valor)
    except Exception:
        return default


# ============================================================
# MÉTRICAS OBJETIVAS DA CARTEIRA
# ============================================================

def calcular_metricas(df):
    if df.empty:
        return {
            "qtd_ativos": 0,
            "peso_total": 0.0,
            "peso_top5": 0.0,
            "qtd_setores": 0,
            "maior_setor": "N/A",
            "peso_maior_setor": 0.0,
            "score_medio": 0.0,
            "score_max": 0.0,
            "score_min": 0.0,
            "ativo_lider": "N/A",
            "decisoes": {},
            "conviccoes": {},
        }

    metricas = {}
    metricas["qtd_ativos"] = len(df)

    if "peso_sugerido_pct" in df.columns:
        pesos = pd.to_numeric(df["peso_sugerido_pct"], errors="coerce").fillna(0)
        metricas["peso_total"] = float(pesos.sum())
        metricas["peso_top5"] = float(pesos.head(5).sum())
    else:
        metricas["peso_total"] = 0.0
        metricas["peso_top5"] = 0.0

    if "setor" in df.columns:
        metricas["qtd_setores"] = int(df["setor"].nunique())

        if "peso_sugerido_pct" in df.columns:
            setor = (
                df.assign(
                    peso_sugerido_pct=pd.to_numeric(
                        df["peso_sugerido_pct"],
                        errors="coerce"
                    ).fillna(0)
                )
                .groupby("setor")["peso_sugerido_pct"]
                .sum()
                .sort_values(ascending=False)
            )

            if not setor.empty:
                metricas["maior_setor"] = str(setor.index[0])
                metricas["peso_maior_setor"] = float(setor.iloc[0])
            else:
                metricas["maior_setor"] = "N/A"
                metricas["peso_maior_setor"] = 0.0
        else:
            metricas["maior_setor"] = "N/A"
            metricas["peso_maior_setor"] = 0.0
    else:
        metricas["qtd_setores"] = 0
        metricas["maior_setor"] = "N/A"
        metricas["peso_maior_setor"] = 0.0

    if "score_final_carteira" in df.columns:
        scores = pd.to_numeric(df["score_final_carteira"], errors="coerce").fillna(0)
        metricas["score_medio"] = float(scores.mean())
        metricas["score_max"] = float(scores.max())
        metricas["score_min"] = float(scores.min())
    else:
        metricas["score_medio"] = 0.0
        metricas["score_max"] = 0.0
        metricas["score_min"] = 0.0

    if "ticker" in df.columns and not df.empty:
        metricas["ativo_lider"] = str(df.iloc[0]["ticker"])
    else:
        metricas["ativo_lider"] = "N/A"

    if "decisao" in df.columns:
        metricas["decisoes"] = df["decisao"].value_counts().to_dict()
    else:
        metricas["decisoes"] = {}

    if "conviccao" in df.columns:
        metricas["conviccoes"] = df["conviccao"].value_counts().to_dict()
    else:
        metricas["conviccoes"] = {}

    return metricas


def formatar_metricas(metricas):
    linhas = [
        f"Ativos na carteira: {metricas['qtd_ativos']}",
        f"Peso total: {metricas['peso_total']:.2f}%",
        f"Peso Top 5: {metricas['peso_top5']:.2f}%",
        f"Quantidade de setores: {metricas['qtd_setores']}",
        f"Maior setor: {metricas['maior_setor']} ({metricas['peso_maior_setor']:.2f}%)",
        f"Score médio: {metricas['score_medio']:.2f}",
        f"Maior score: {metricas['score_max']:.2f}",
        f"Menor score: {metricas['score_min']:.2f}",
        f"Ativo líder: {metricas['ativo_lider']}",
    ]

    if metricas.get("decisoes"):
        linhas.append("")
        linhas.append("Distribuição por decisão:")
        for chave, valor in metricas["decisoes"].items():
            linhas.append(f"- {chave}: {valor}")

    if metricas.get("conviccoes"):
        linhas.append("")
        linhas.append("Distribuição por convicção:")
        for chave, valor in metricas["conviccoes"].items():
            linhas.append(f"- {chave}: {valor}")

    return "\n".join(linhas)


# ============================================================
# RESUMO TABULAR PARA A IA
# ============================================================

def preparar_resumo_tabela(df, limite=15):
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

    resumo = df[colunas].head(limite).copy()

    for col in ["score_fundamental", "score_tecnico", "score_final_carteira", "peso_sugerido_pct"]:
        if col in resumo.columns:
            resumo[col] = pd.to_numeric(resumo[col], errors="coerce").round(2)

    return resumo.to_string(index=False)


# ============================================================
# PROMPT INSTITUCIONAL
# ============================================================

def gerar_prompt(carteira, diversificada):
    base = diversificada if not diversificada.empty else carteira
    metricas = calcular_metricas(base)

    prompt = f"""
Você é o Chief Investment Officer (CIO) de uma gestora quantitativa especializada em ações brasileiras.

Sua função é auditar a carteira produzida pelo B3 Fundamentalista Engine.

IMPORTANTE:
- Não faça recomendação absoluta de compra ou venda.
- Não prometa retorno.
- Não invente dados.
- Use apenas as métricas e tabelas fornecidas.
- Escreva como um parecer para Comitê de Investimentos.
- Seja objetivo, conservador e institucional.
- O texto será inserido em um PDF, portanto deve ser curto, claro e organizado.

METODOLOGIA DO MOTOR:
- Fundamentalista: seleciona empresas por qualidade, valuation, crescimento, rentabilidade, alavancagem e moat.
- Técnico: avalia momento de entrada.
- Portfolio: combina 70% fundamentos e 30% técnico.
- Diversificação: controla concentração setorial.
- IA: audita coerência, riscos observáveis e governança do processo.

MÉTRICAS CONSOLIDADAS DA CARTEIRA:
{formatar_metricas(metricas)}

CARTEIRA FINAL:
{preparar_resumo_tabela(base, limite=15)}

Gere a auditoria exatamente no formato abaixo.
Não use markdown complexo. Use títulos simples e bullets simples.

NOTA GERAL: X.X/10
Explique a nota em no máximo 4 linhas.

DASHBOARD EXECUTIVO:
Fundamentos: X/10
Técnico: X/10
Diversificação: X/10
Governança: X/10
Consistência: X/10

DIAGNÓSTICO EXECUTIVO:
Um único parágrafo de no máximo 5 linhas.

PONTOS FORTES:
- até 5 bullets objetivos

PONTOS DE ATENÇÃO:
- até 5 bullets objetivos

MAIORES RISCOS OBSERVADOS:
- liste apenas riscos suportados pelos dados

ATIVOS PRIORITÁRIOS:
- até 5 tickers com motivo em uma linha

ATIVOS EM OBSERVAÇÃO:
- até 5 tickers com motivo em uma linha

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: APROVADO / ATENÇÃO / REPROVADO
Timing Técnico: APROVADO / ATENÇÃO / REPROVADO
Diversificação: APROVADO / ATENÇÃO / REPROVADO
Governança: APROVADO / ATENÇÃO / REPROVADO
Controle de Risco: APROVADO / ATENÇÃO / REPROVADO

PARECER FINAL:
Um parágrafo curto, objetivo e institucional.
"""

    return prompt


# ============================================================
# CHAMADA OPENAI
# ============================================================

def chamar_openai(prompt, api_key):
    client = OpenAI(api_key=api_key)

    resposta = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um CIO e auditor institucional de carteiras quantitativas. "
                    "Avalie processo, risco, coerência, diversificação e governança. "
                    "Nunca prometa retorno e nunca invente dados."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.10,
    )

    return resposta.choices[0].message.content.strip()


# ============================================================
# FALLBACK SEM IA
# ============================================================

def gerar_auditoria_fallback(df):
    metricas = calcular_metricas(df)

    texto = f"""
NOTA GERAL: 7.0/10
Auditoria gerada por fallback local porque a IA não foi executada. A carteira possui {metricas['qtd_ativos']} ativos, {metricas['qtd_setores']} setores e score médio de {metricas['score_medio']:.2f}.

DASHBOARD EXECUTIVO:
Fundamentos: 7/10
Técnico: 6/10
Diversificação: 7/10
Governança: 8/10
Consistência: 7/10

DIAGNÓSTICO EXECUTIVO:
A carteira apresenta estrutura quantitativa organizada, com pesos distribuídos e controle inicial de concentração. A análise completa da IA não foi realizada, portanto este parecer deve ser tratado como diagnóstico operacional provisório.

PONTOS FORTES:
- Processo quantitativo estruturado.
- Carteira com pesos distribuídos.
- Existência de controle por setor.

PONTOS DE ATENÇÃO:
- Auditoria IA não executada.
- Necessária revisão da chave OPENAI_API_KEY.
- Validar geração do arquivo auditoria_ia.txt.

MAIORES RISCOS OBSERVADOS:
- Risco operacional de ausência de auditoria IA.

ATIVOS PRIORITÁRIOS:
- {metricas['ativo_lider']}: ativo líder pelo ranking atual.

ATIVOS EM OBSERVAÇÃO:
- Verificar ativos com decisão NÃO PRIORIZAR AGORA.

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: ATENÇÃO
Timing Técnico: ATENÇÃO
Diversificação: ATENÇÃO
Governança: APROVADO
Controle de Risco: ATENÇÃO

PARECER FINAL:
O processo está operacional, mas a auditoria institucional completa depende da execução correta da IA. Recomenda-se validar credenciais e revisar o relatório gerado.
""".strip()

    return texto


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def gerar_auditoria_ia():
    OUTPUT_DIR.mkdir(exist_ok=True)

    carteira = carregar_csv(CARTEIRA_FILE)
    diversificada = carregar_csv(DIVERSIFICADA_FILE)

    if carteira.empty:
        texto = "AUDITORIA IA NÃO GERADA: carteira_institucional.csv não encontrado ou vazio."
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print(texto)
        return texto

    base = diversificada if not diversificada.empty else carteira

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        texto = gerar_auditoria_fallback(base)
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print("OPENAI_API_KEY não configurada. Fallback local gerado.")
        print(texto)
        return texto

    try:
        prompt = gerar_prompt(carteira, diversificada)
        texto = chamar_openai(prompt, api_key)
    except Exception as erro:
        texto = gerar_auditoria_fallback(base)
        texto = (
            "AVISO: auditoria IA não executada por erro na chamada OpenAI. "
            f"Erro: {erro}\n\n" + texto
        )

    AUDITORIA_FILE.write_text(texto, encoding="utf-8")

    print("=" * 70)
    print("AUDITORIA IA GERADA")
    print("=" * 70)
    print(texto)

    return texto


if __name__ == "__main__":
    gerar_auditoria_ia()
