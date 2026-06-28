# ============================================================
# ai_audit.py
# B3 FUNDAMENTALISTA ENGINE
# Auditoria Institucional com IA — V5 Integrated Research
# ============================================================

import os
from pathlib import Path

import pandas as pd
from openai import OpenAI


OUTPUT_DIR = Path("output")
CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
PORTFOLIO_METRICS_FILE = OUTPUT_DIR / "portfolio_metrics.csv"
DIVERSIFICATION_METRICS_FILE = OUTPUT_DIR / "diversification_metrics.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"


# ============================================================
# LEITURA DE ARQUIVOS
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


def primeira_linha_dict(df):
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


# ============================================================
# UTILITÁRIOS
# ============================================================

def _num(valor, padrao=0.0):
    try:
        if pd.isna(valor):
            return padrao
        return float(valor)
    except Exception:
        return padrao


def _txt(valor, padrao="N/A"):
    try:
        if pd.isna(valor):
            return padrao
        texto = str(valor).strip()
        return texto if texto else padrao
    except Exception:
        return padrao


def _fmt(valor, casas=2):
    return f"{_num(valor):.{casas}f}"


def _fmt_pct(valor, casas=2):
    return f"{_num(valor):.{casas}f}%"


def _colunas_existentes(df, colunas):
    return [c for c in colunas if c in df.columns]


# ============================================================
# MÉTRICAS DA CARTEIRA
# ============================================================

def calcular_metricas_carteira(df):
    if df.empty:
        return {
            "ativos": 0,
            "peso_total": 0,
            "peso_top5": 0,
            "maior_ativo": "N/A",
            "peso_maior_ativo": 0,
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
            "risco_tecnico_controlado": 0,
            "risco_tecnico_moderado": 0,
            "risco_tecnico_elevado": 0,
            "conv_tecnica_muito_alta": 0,
            "conv_tecnica_alta": 0,
            "conv_tecnica_moderada": 0,
            "conv_tecnica_baixa": 0,
            "conv_tecnica_muito_baixa": 0,
        }

    metricas = {}
    metricas["ativos"] = len(df)

    if "peso_sugerido_pct" in df.columns:
        pesos = pd.to_numeric(df["peso_sugerido_pct"], errors="coerce").fillna(0)
        metricas["peso_total"] = _num(pesos.sum())
        metricas["peso_top5"] = _num(df.head(5)["peso_sugerido_pct"].sum())
        idx_maior = pesos.idxmax()
        metricas["maior_ativo"] = _txt(df.loc[idx_maior, "ticker"] if "ticker" in df.columns else "N/A")
        metricas["peso_maior_ativo"] = _num(pesos.loc[idx_maior])
    else:
        metricas["peso_total"] = 0
        metricas["peso_top5"] = 0
        metricas["maior_ativo"] = "N/A"
        metricas["peso_maior_ativo"] = 0

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
            metricas["maior_setor"] = _txt(setor.index[0])
            metricas["peso_maior_setor"] = _num(setor.iloc[0])
        else:
            metricas["maior_setor"] = "N/A"
            metricas["peso_maior_setor"] = 0
    else:
        metricas["maior_setor"] = "N/A"
        metricas["peso_maior_setor"] = 0

    if "score_final_carteira" in df.columns:
        scores = pd.to_numeric(df["score_final_carteira"], errors="coerce").fillna(0)
        metricas["score_medio"] = _num(scores.mean())
        metricas["score_max"] = _num(scores.max())
        metricas["score_min"] = _num(scores.min())
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

    if "risco_tecnico" in df.columns:
        risco = df["risco_tecnico"].fillna("").astype(str).str.upper()
        metricas["risco_tecnico_controlado"] = int(risco.str.contains("CONTROLADO").sum())
        metricas["risco_tecnico_moderado"] = int(risco.str.contains("MODERADO").sum())
        metricas["risco_tecnico_elevado"] = int(risco.str.contains("ELEVADO").sum())
    else:
        metricas["risco_tecnico_controlado"] = 0
        metricas["risco_tecnico_moderado"] = 0
        metricas["risco_tecnico_elevado"] = 0

    if "conviccao_tecnica" in df.columns:
        convt = df["conviccao_tecnica"].fillna("").astype(str).str.upper()
        metricas["conv_tecnica_muito_alta"] = int((convt == "MUITO ALTA").sum())
        metricas["conv_tecnica_alta"] = int((convt == "ALTA").sum())
        metricas["conv_tecnica_moderada"] = int(convt.str.contains("MODERADA").sum())
        metricas["conv_tecnica_baixa"] = int((convt == "BAIXA").sum())
        metricas["conv_tecnica_muito_baixa"] = int((convt == "MUITO BAIXA").sum())
    else:
        metricas["conv_tecnica_muito_alta"] = 0
        metricas["conv_tecnica_alta"] = 0
        metricas["conv_tecnica_moderada"] = 0
        metricas["conv_tecnica_baixa"] = 0
        metricas["conv_tecnica_muito_baixa"] = 0

    return metricas


# ============================================================
# MÉTRICAS EXTERNAS DO MOTOR
# ============================================================

def formatar_metricas_portfolio(metrics_dict):
    if not metrics_dict:
        return "portfolio_metrics.csv não encontrado ou vazio."

    linhas = ["MÉTRICAS DO PORTFÓLIO:"]

    campos = {
        "qtd_ativos": "Quantidade de ativos",
        "score_medio_carteira": "Score médio da carteira",
        "score_minimo_carteira": "Menor score da carteira",
        "score_maximo_carteira": "Maior score da carteira",
        "peso_top5_pct": "Peso Top 5",
        "maior_peso_ativo_pct": "Maior peso por ativo",
        "qtd_comprar": "Ativos em compra",
        "qtd_aguardar": "Ativos em aguardar",
        "qtd_nao_priorizar": "Ativos em não priorizar",
        "peso_maximo_ativo_pct": "Limite máximo por ativo",
        "soma_pesos_pct": "Soma dos pesos",
    }

    for chave, nome in campos.items():
        if chave in metrics_dict:
            valor = metrics_dict[chave]
            if "pct" in chave or "peso" in chave:
                linhas.append(f"- {nome}: {_fmt_pct(valor)}")
            elif "score" in chave:
                linhas.append(f"- {nome}: {_fmt(valor, 2)}")
            else:
                linhas.append(f"- {nome}: {_txt(valor)}")

    return "\n".join(linhas)


def formatar_metricas_diversificacao(metrics_dict):
    if not metrics_dict:
        return "diversification_metrics.csv não encontrado ou vazio."

    linhas = ["MÉTRICAS DE DIVERSIFICAÇÃO:"]

    campos = {
        "qtd_ativos": "Quantidade de ativos",
        "qtd_setores": "Quantidade de setores",
        "peso_top5_pct": "Peso Top 5",
        "maior_setor": "Maior setor",
        "peso_maior_setor_pct": "Peso do maior setor",
        "hhi": "HHI",
        "numero_efetivo_ativos": "Número efetivo de ativos",
        "score_diversificacao": "Score de diversificação",
        "status_diversificacao": "Status da diversificação",
        "risco_diversificacao": "Risco de diversificação",
        "limite_peso_ativo_pct": "Limite por ativo",
        "limite_peso_setor_pct": "Limite por setor",
        "soma_pesos_pct": "Soma dos pesos",
    }

    for chave, nome in campos.items():
        if chave in metrics_dict:
            valor = metrics_dict[chave]
            if "pct" in chave or "peso" in chave:
                linhas.append(f"- {nome}: {_fmt_pct(valor)}")
            elif chave in ["hhi"]:
                linhas.append(f"- {nome}: {_fmt(valor, 4)}")
            elif "score" in chave or "numero" in chave:
                linhas.append(f"- {nome}: {_fmt(valor, 2)}")
            else:
                linhas.append(f"- {nome}: {_txt(valor)}")

    return "\n".join(linhas)


def resumo_metricas_texto(metricas):
    return f"""
MÉTRICAS CONSOLIDADAS DA CARTEIRA:
- Ativos: {metricas['ativos']}
- Peso total: {metricas['peso_total']:.2f}%
- Maior ativo: {metricas['maior_ativo']} ({metricas['peso_maior_ativo']:.2f}%)
- Peso Top 5: {metricas['peso_top5']:.2f}%
- Setores: {metricas['setores']}
- Maior setor: {metricas['maior_setor']} ({metricas['peso_maior_setor']:.2f}%)
- Score médio: {metricas['score_medio']:.2f}
- Maior score: {metricas['score_max']:.2f}
- Menor score: {metricas['score_min']:.2f}
- Decisões de comprar: {metricas['comprar']}
- Decisões de aguardar: {metricas['aguardar']}
- Decisões de não priorizar/evitar: {metricas['nao_priorizar']}
- Convicção alta: {metricas['conviccao_alta']}
- Convicção média: {metricas['conviccao_media']}
- Convicção baixa: {metricas['conviccao_baixa']}
- Risco técnico controlado: {metricas['risco_tecnico_controlado']}
- Risco técnico moderado: {metricas['risco_tecnico_moderado']}
- Risco técnico elevado: {metricas['risco_tecnico_elevado']}
- Convicção técnica muito alta: {metricas['conv_tecnica_muito_alta']}
- Convicção técnica alta: {metricas['conv_tecnica_alta']}
- Convicção técnica moderada: {metricas['conv_tecnica_moderada']}
- Convicção técnica baixa: {metricas['conv_tecnica_baixa']}
- Convicção técnica muito baixa: {metricas['conv_tecnica_muito_baixa']}
""".strip()


# ============================================================
# TABELAS PARA O PROMPT
# ============================================================

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
            "conviccao_tecnica",
            "risco_tecnico",
            "prioridade",
            "peso_sugerido_pct",
            "sinal_tecnico",
            "decisao",
            "motivo_decisao",
        ],
    )

    return df[colunas].head(limite).to_string(index=False)


def preparar_diagnostico_tecnico(df, limite=10):
    if df.empty:
        return "Diagnóstico técnico indisponível."

    colunas = _colunas_existentes(
        df,
        [
            "ticker",
            "tendencia_resumo",
            "mm200_status",
            "rsi_status",
            "momentum_status",
            "volume_status",
            "volatilidade_status",
            "conviccao_tecnica",
            "risco_tecnico",
            "diagnostico_tecnico",
        ],
    )

    if not colunas:
        return "Diagnóstico técnico indisponível."

    return df[colunas].head(limite).to_string(index=False)


# ============================================================
# PROMPT
# ============================================================

def gerar_prompt(carteira, diversificada, portfolio_metrics, diversification_metrics):
    base = diversificada if not diversificada.empty else carteira
    metricas = calcular_metricas_carteira(base)

    p_metrics = primeira_linha_dict(portfolio_metrics)
    d_metrics = primeira_linha_dict(diversification_metrics)

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
- Não diga que há ausência de governança corporativa. O escopo aqui é governança quantitativa do processo.
- Avalie governança como disciplina do pipeline, validação de pesos, limites, rastreabilidade e consistência do processo.

METODOLOGIA DO MOTOR:
- Fundamentalista seleciona empresas por qualidade, valuation, rentabilidade, crescimento, alavancagem e moat.
- Técnico avalia o momento de entrada.
- Portfolio combina predominantemente fundamentos com uma camada técnica.
- Diversificação controla concentração por ativo e setor.
- IA faz auditoria independente do processo.

{resumo_metricas_texto(metricas)}

{formatar_metricas_portfolio(p_metrics)}

{formatar_metricas_diversificacao(d_metrics)}

CARTEIRA ANALISADA:
{preparar_tabela(base)}

DIAGNÓSTICO TÉCNICO DOS PRINCIPAIS ATIVOS:
{preparar_diagnostico_tecnico(base)}

FORMATO DA RESPOSTA:
Responda exatamente nesta estrutura, mantendo os títulos abaixo.

NOTA GERAL: X.X/10
Explique em no máximo 3 linhas por que a nota foi atribuída.

COMPOSIÇÃO DA NOTA:
Fundamentos: X/10 — justificativa curta.
Técnico: X/10 — use risco técnico, convicção técnica e decisões de entrada.
Diversificação: X/10 — use HHI, número efetivo de ativos, Top 5, maior setor e limites.
Governança: X/10 — avalie governança quantitativa do pipeline, validação de limites e rastreabilidade.
Consistência: X/10 — avalie coerência entre fundamento, técnico, peso e decisão.

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
Explique em até 4 linhas, usando HHI, número efetivo de ativos, Top 5, maior setor e maior ativo.
Classifique a concentração como baixa, moderada ou elevada.

ATIVOS PRIORITÁRIOS:
- TICKER | Motivo em uma linha, combinando fundamento, técnico, peso e risco.
- TICKER | Motivo em uma linha, combinando fundamento, técnico, peso e risco.
- TICKER | Motivo em uma linha, combinando fundamento, técnico, peso e risco.

ATIVOS EM OBSERVAÇÃO:
- TICKER | Motivo em uma linha, combinando fundamento, técnico, peso e risco.
- TICKER | Motivo em uma linha, combinando fundamento, técnico, peso e risco.
- TICKER | Motivo em uma linha, combinando fundamento, técnico, peso e risco.

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: APROVADO/ATENÇÃO | justificativa curta.
Timing Técnico: APROVADO/ATENÇÃO | justificativa curta.
Diversificação: APROVADO/ATENÇÃO | justificativa curta.
Governança Quantitativa: APROVADO/ATENÇÃO | justificativa curta.
Controle de Risco: APROVADO/ATENÇÃO | justificativa curta.

PARECER FINAL:
Um único parágrafo, com no máximo 6 linhas. Não seja genérico. Foque em disciplina, risco, concentração, timing e coerência do processo.
"""


# ============================================================
# FALLBACK
# ============================================================

def gerar_auditoria_fallback(carteira, diversificada, portfolio_metrics, diversification_metrics, motivo):
    base = diversificada if not diversificada.empty else carteira
    metricas = calcular_metricas_carteira(base)
    p_metrics = primeira_linha_dict(portfolio_metrics)
    d_metrics = primeira_linha_dict(diversification_metrics)

    hhi = _fmt(d_metrics.get("hhi", 0), 4) if d_metrics else "N/A"
    num_efetivo = _fmt(d_metrics.get("numero_efetivo_ativos", 0), 2) if d_metrics else "N/A"
    score_div = _fmt(d_metrics.get("score_diversificacao", 0), 0) if d_metrics else "N/A"
    status_div = _txt(d_metrics.get("status_diversificacao", "N/A")) if d_metrics else "N/A"

    texto = f"""
NOTA GERAL: 7.0/10
Auditoria automática por IA não foi concluída. Motivo técnico: {motivo}

COMPOSIÇÃO DA NOTA:
Fundamentos: dados insuficientes — IA indisponível.
Técnico: dados insuficientes — IA indisponível.
Diversificação: 8/10 — HHI {hhi}, número efetivo de ativos {num_efetivo}, score de diversificação {score_div}/100, status {status_div}.
Governança: 7/10 — pipeline executou até a etapa de auditoria fallback e gerou métricas quantitativas.
Consistência: dados insuficientes — IA indisponível.

DIAGNÓSTICO EXECUTIVO:
A carteira foi gerada pelo pipeline, mas a auditoria IA não pôde ser completada. O relatório deve ser interpretado com base nos dados quantitativos disponíveis e revisado manualmente.

PONTOS FORTES:
- Pipeline gerou carteira final.
- Carteira contém {metricas['ativos']} ativos.
- Diversificação apresenta {metricas['setores']} setores.
- Métricas institucionais foram geradas.

PONTOS DE ATENÇÃO:
- Auditoria IA indisponível nesta execução.
- Revisão manual recomendada.
- Monitorar logs do GitHub Actions.

RISCOS PRIORIZADOS:
ALTO | Auditoria IA indisponível | O parecer qualitativo não foi gerado pelo modelo.
MÉDIO | Interpretação limitada | O PDF dependerá dos dados quantitativos disponíveis.
BAIXO | Continuidade operacional | O restante do pipeline pode continuar funcionando.

INTERPRETAÇÃO DA CONCENTRAÇÃO:
Maior setor: {metricas['maior_setor']} com {metricas['peso_maior_setor']:.2f}%. Peso Top 5: {metricas['peso_top5']:.2f}%. HHI: {hhi}. Número efetivo de ativos: {num_efetivo}. Sem auditoria IA, a leitura deve ser conservadora.

ATIVOS PRIORITÁRIOS:
- Dados insuficientes | Auditoria IA não concluída.

ATIVOS EM OBSERVAÇÃO:
- Dados insuficientes | Auditoria IA não concluída.

CHECKLIST INSTITUCIONAL:
Qualidade Fundamentalista: ATENÇÃO | IA indisponível para validação qualitativa.
Timing Técnico: ATENÇÃO | IA indisponível para validação qualitativa.
Diversificação: APROVADO | Métricas quantitativas disponíveis.
Governança Quantitativa: ATENÇÃO | Houve falha na auditoria IA.
Controle de Risco: ATENÇÃO | Revisão manual recomendada.

PARECER FINAL:
A carteira foi construída pelo processo quantitativo, mas a auditoria qualitativa por IA não foi concluída. Recomenda-se revisar os logs, validar os dados gerados e considerar esta execução como parcialmente auditada.
""".strip()

    return texto


# ============================================================
# EXECUÇÃO
# ============================================================

def gerar_auditoria_ia():
    OUTPUT_DIR.mkdir(exist_ok=True)

    carteira = carregar_csv(CARTEIRA_FILE)
    diversificada = carregar_csv(DIVERSIFICADA_FILE)
    portfolio_metrics = carregar_csv(PORTFOLIO_METRICS_FILE)
    diversification_metrics = carregar_csv(DIVERSIFICATION_METRICS_FILE)

    if carteira.empty:
        texto = "AUDITORIA IA NÃO GERADA: carteira_institucional.csv não encontrado ou vazio."
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print(texto)
        return texto

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        texto = gerar_auditoria_fallback(
            carteira,
            diversificada,
            portfolio_metrics,
            diversification_metrics,
            "OPENAI_API_KEY não configurada",
        )
        AUDITORIA_FILE.write_text(texto, encoding="utf-8")
        print(texto)
        return texto

    prompt = gerar_prompt(
        carteira,
        diversificada,
        portfolio_metrics,
        diversification_metrics,
    )

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
                        "Sua escrita é objetiva, conservadora e baseada apenas nos dados fornecidos. "
                        "Você avalia governança quantitativa do processo, não governança corporativa das empresas."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.10,
        )

        texto = resposta.choices[0].message.content.strip()

    except Exception as erro:
        texto = gerar_auditoria_fallback(
            carteira,
            diversificada,
            portfolio_metrics,
            diversification_metrics,
            str(erro),
        )

    AUDITORIA_FILE.write_text(texto, encoding="utf-8")

    print("=" * 70)
    print("AUDITORIA IA GERADA")
    print("=" * 70)
    print(texto)

    return texto


if __name__ == "__main__":
    gerar_auditoria_ia()
      
























