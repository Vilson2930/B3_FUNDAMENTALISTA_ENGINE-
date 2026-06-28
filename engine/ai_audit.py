# ============================================================
# ai_audit.py
# B3 FUNDAMENTALISTA ENGINE
# Auditoria Institucional com IA — V4 Executive Research
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

    try:
        return pd.read_csv(caminho, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(caminho)


def _num(valor, padrao=0.0):
    try:
        return float(valor)
    except Exception:
        return padrao


def _colunas_existentes(df, colunas):
    return [c for c in colunas if c in df.columns]


def calcular_metricas(df):
    if df.empty:
        return {
            "ativos": 0,
            "peso_total": 0,
            "peso_top5": 0,
            "setores": 0,
            "maior_setor": "N/A",
            "peso_maior_setor": 0,
            "score_medio": 0,
            "score_max": 0,
            "score_min": 0,
            "comprar": 0,
            "aguardar": 0,
            "nao_priorizar": 0,
            "conviccao_alta": 0,
            "conviccao_media": 0,
            "conviccao_baixa": 0,
        }

    metricas = {}
    metricas["ativos"] = len(df)

    if "peso_sugerido_pct" in df.columns:
        metricas["peso_total"] = _num(df["peso_sugerido_pct"].sum())
        metricas["peso_top5"] = _num(df.head(5)["peso_sugerido_pct"].sum())
    else:
        metricas["peso_total"] = 0
        metricas["peso_top5"] = 0

    if "setor" in df.columns:
        metricas["setores"] = int(df["setor"].nunique())
    else:
        metricas["setores"] = 0

    if "setor" in df.columns and "peso_sugerido_pct" in df.columns:
        setor = (
            df.groupby("setor")["peso_sugerido_pct"]
            .sum()
            .sort_values(ascending=False)
            .head(1)
        )
        if not setor.empty:
            metricas["maior_setor"] = str(setor.index[0])
            metricas["peso_maior_setor"] = _num(setor.iloc[0])
        else:
            metricas["maior_setor"] = "N/A"
            metricas["peso_maior_setor"] = 0
    else:
        metricas["maior_setor"] = "N/A"
        metricas["peso_maior_setor"] = 0

    if "score_final_carteira" in df.columns:
        metricas["score_medio"] = _num(df["score_final_carteira"].mean())
        metricas["score_max"] = _num(df["score_final_carteira"].max())
        metricas["score_min"] = _num(df["score_final_carteira"].min())
    else:
        metricas["score_medio"] = 0
        metricas["score_max"] = 0
        metricas["score_min"] = 0

    if "decisao" in df.columns:
        decisoes = df["decisao"].fillna("").astype(str).str.upper()
        metricas["comprar"] = int(decisoes.str.contains("COMPRAR").sum())
        metricas["aguardar"] = int(decisoes.str.contains("AGUARDAR").sum())
        metricas["nao_priorizar"] = int(decisoes.str.contains("NÃO PRIORIZAR|NAO PRIORIZAR|EVITAR").sum())
    else:
        metricas["comprar"] = 0
        metricas["aguardar"] = 0
        metricas["nao_priorizar"] = 0

    if "conviccao" in df.columns:
        conv = df["conviccao"].fillna("").astype(str).str.upper()
        metricas["conviccao_alta"] = int(conv.str.contains("ALTA").sum())
        metricas["conviccao_media"] = int(conv.str.contains("MÉDIA|MEDIA").sum())
        metricas["conviccao_baixa"] = int(conv.str.contains("BAIXA").sum())
    else:
        metricas["conviccao_alta"] = 0
        metricas["conviccao_media"] = 0
        metricas["conviccao_baixa"] = 0

    return metricas


def resumo_metricas_texto(metricas):
    return f"""
Ativos: {metricas['ativos']}
Peso total: {metricas['peso_total']:.2f}%
Peso Top 5: {metricas['peso_top5']:.2f}%
Setores: {metricas['setores']}
Maior setor: {metricas['maior_setor']} ({metricas['peso_maior_setor']:.2f}%)
Score médio: {metricas['score_medio']:.2f}
Maior score: {metricas['score_max']:.2f}
Menor score: {metricas['score_min']:.2f}
Decisões de comprar: {metricas['comprar']}
Decisões de aguardar: {metricas['aguardar']}
Decisões de não priorizar/evitar: {metricas['nao_priorizar']}
Convicção alta: {metricas['conviccao_alta']}
Convicção média: {metricas['conviccao_media']}
Convicção baixa: {metricas['conviccao_baixa']}
""".strip()


def preparar_tabela(df, limite=15):
    if df.empty:
        return "Carteira vazia."

    colunas = _colunas_existentes(
        df,
        [
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
        ],
    )

    return df[colunas].head(limite).to_string(index=False)


def gerar_prompt(carteira, diversificada):
    base = diversificada if not diversificada.empty else carteira
    metricas = calcular_metricas(base)

    return f"""
Você é o Chief Investment Officer (CIO) de uma gestora quantitativa especializada em ações brasileiras.

Sua função é auditar a carteira produzida pelo B3 Fundamentalista Engine para um Comitê de Investimentos.

REGRAS OBRIGATÓRIAS:
- Não faça recomendação absoluta de compra ou venda.
- Não prometa retorno.
- Não invente dados.
- Use apenas os dados fornecidos.
- Seja conservador, técnico e objetivo.
- A saída será inserida em um PDF institucional.
- Não escreva parágrafos longos.
- Use blocos curtos e bullets.
- Interprete os números; não apenas repita os dados.
- Se não houver dado suficiente para avaliar algo, diga "dados insuficientes".

METODOLOGIA DO MOTOR:
- Fundamentalista seleciona empresas por qualidade, valuation, rentabilidade, crescimento, alavancagem e moat.
- Técnico avalia o momento de entrada.
- Portfolio combina predominantemente fundamentos com uma camada técnica.
- Diversificação controla concentração setorial.
- IA faz auditoria independente do processo.

MÉTRICAS CONSOLIDADAS:
{resumo_metricas_texto(metricas)}

CARTEIRA ANALISADA:
{preparar_tabela(base)}

FORMATO DA RESPOSTA:
Responda exatamente nesta estrutura, mantendo os títulos abaixo.

NOTA GERAL: X.X/10
Explique em no máximo 3 linhas por que a nota foi atribuída.

COMPOSIÇÃO DA NOTA:
Fundamentos: X/10 — justificativa curta.
Técnico: X/10 — justificativa curta.
Diversificação: X/10 — justificativa curta.
Governança: X/10 — justificativa curta.
Consistência: X/10 — justificativa curta.

DIAGNÓSTICO EXECUTIVO:
Escreva no máximo 5 linhas. Interprete a carteira de forma objetiva.

PONTOS FORTES:
- máximo 5 bullets curtos.

PONTOS DE ATENÇÃO:
- máximo 5 bullets curtos.

RISCOS PRIORIZADOS:
ALTO | Nome do risco | Explicação curta.
MÉDIO | Nome do risco | Explicação curta.
BAIXO | Nome do risco | Explicação curta.

INTERPRETAÇÃO DA CONCENTRAÇÃO:
Explique em até 4 linhas se a concentração em setor, top 5 e maior ativo parece aceitável, moderada ou relevante com base nos dados fornecidos.

ATIVOS PRIORITÁRIOS:
- TICKER | Motivo em uma linha.
- TICKER | Motivo em uma linha.
- TICKER | Motivo em uma linha.

ATIVOS EM OBSERVAÇÃO:
- TICKER | Motivo em uma linha.
- TICKER | Motivo em uma linha.
- TICKER | Motivo em uma linha.

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: APROVADO/ATENÇÃO | justificativa curta.
Timing Técnico: APROVADO/ATENÇÃO | justificativa curta.
Diversificação: APROVADO/ATENÇÃO | justificativa curta.
Governança: APROVADO/ATENÇÃO | justificativa curta.
Controle de Risco: APROVADO/ATENÇÃO | justificativa curta.

PARECER FINAL:
Um único parágrafo, com no máximo 6 linhas. Não seja genérico. Foque em decisão de monitoramento, disciplina e coerência do processo.
"""


def gerar_auditoria_fallback(carteira, diversificada, motivo):
    base = diversificada if not diversificada.empty else carteira
    metricas = calcular_metricas(base)

    texto = f"""
NOTA GERAL: 7.0/10
Auditoria automática por IA não foi concluída. Motivo técnico: {motivo}

COMPOSIÇÃO DA NOTA:
Fundamentos: dados insuficientes — IA indisponível.
Técnico: dados insuficientes — IA indisponível.
Diversificação: dados disponíveis — {metricas['setores']} setores, maior setor {metricas['maior_setor']} com {metricas['peso_maior_setor']:.2f}%.
Governança: 7/10 — pipeline executou até a etapa de auditoria fallback.
Consistência: dados insuficientes — IA indisponível.

DIAGNÓSTICO EXECUTIVO:
A carteira foi gerada pelo pipeline, mas a auditoria IA não pôde ser completada. O relatório deve ser interpretado com base nos dados quantitativos disponíveis e revisado manualmente.

PONTOS FORTES:
- Pipeline gerou carteira final.
- Carteira contém {metricas['ativos']} ativos.
- Diversificação apresenta {metricas['setores']} setores.

PONTOS DE ATENÇÃO:
- Auditoria IA indisponível nesta execução.
- Revisão manual recomendada.
- Monitorar logs do GitHub Actions.

RISCOS PRIORIZADOS:
ALTO | Auditoria IA indisponível | O parecer qualitativo não foi gerado pelo modelo.
MÉDIO | Interpretação limitada | O PDF dependerá apenas dos dados quantitativos.
BAIXO | Continuidade operacional | O restante do pipeline pode continuar funcionando.

INTERPRETAÇÃO DA CONCENTRAÇÃO:
Maior setor: {metricas['maior_setor']} com {metricas['peso_maior_setor']:.2f}%. Peso Top 5: {metricas['peso_top5']:.2f}%. Sem auditoria IA, a leitura deve ser conservadora.

ATIVOS PRIORITÁRIOS:
- Dados insuficientes | Auditoria IA não concluída.

ATIVOS EM OBSERVAÇÃO:
- Dados insuficientes | Auditoria IA não concluída.

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: ATENÇÃO | IA indisponível para validação qualitativa.
Timing Técnico: ATENÇÃO | IA indisponível para validação qualitativa.
Diversificação: APROVADO | Métricas quantitativas disponíveis.
Governança: ATENÇÃO | Houve falha na auditoria IA.
Controle de Risco: ATENÇÃO | Revisão manual recomendada.

PARECER FINAL:
A carteira foi construída pelo processo quantitativo, mas a auditoria qualitativa por IA não foi concluída. Recomenda-se revisar os logs, validar os dados gerados e considerar esta execução como parcialmente auditada.
""".strip()

    return texto


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
        texto = gerar_auditoria_fallback(carteira, diversificada, "OPENAI_API_KEY não configurada")
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print(texto)
        return texto

    prompt = gerar_prompt(carteira, diversificada)

    try:
        client = OpenAI(api_key=api_key)

        resposta = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é o CIO de uma gestora quantitativa. "
                        "Você escreve pareceres executivos para comitês de investimento. "
                        "Sua escrita é objetiva, conservadora e baseada apenas nos dados fornecidos."
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

    except Exception as erro:
        texto = gerar_auditoria_fallback(carteira, diversificada, str(erro))

    AUDITORIA_FILE.write_text(texto, encoding="utf-8")

    print("=" * 70)
    print("AUDITORIA IA GERADA")
    print("=" * 70)
    print(texto)

    return texto


if __name__ == "__main__":
    gerar_auditoria_ia()
