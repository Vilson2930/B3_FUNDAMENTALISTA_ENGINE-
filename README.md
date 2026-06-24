# B3 FUNDAMENTALISTA ENGINE

## Visão Geral

O B3 Fundamentalista Engine é um Stock Selection Engine quantitativo desenvolvido para analisar empresas da Bolsa Brasileira utilizando dados oficiais da CVM e dados de mercado.

O objetivo do projeto é identificar empresas com alta qualidade operacional, crescimento consistente e fundamentos sólidos através de um processo totalmente automatizado.

---

## Filosofia do Projeto

O sistema não tenta prever preços.

O foco é identificar empresas com:

* Rentabilidade elevada
* Crescimento sustentável
* Estrutura financeira saudável
* Liquidez adequada
* Relevância de mercado

A análise é baseada em dados públicos e auditáveis.

---

## Fontes de Dados

### CVM

Demonstrações Financeiras Padronizadas (DFP)

Utilizadas para extrair:

* Receita
* Lucro Líquido
* Ativo Total
* Patrimônio Líquido
* Passivos
* Caixa

### Mercado

Dados de mercado utilizados para:

* Market Cap
* Volume negociado
* Liquidez

---

## Indicadores Calculados

### Rentabilidade

* ROE
* ROA
* Margem Líquida

### Solidez Financeira

* Passivo Total
* Caixa
* Alavancagem Líquida
* Dívida sobre Patrimônio

### Crescimento

* Crescimento da Receita
* Crescimento do Lucro

### Mercado

* Market Cap
* Liquidez

---

## Rankings Gerados

### Ranking Qualidade

Prioriza:

* ROE
* ROA
* Margem
* Solidez Financeira

Objetivo:

Identificar empresas estruturalmente fortes.

---

### Ranking Crescimento

Prioriza:

* Crescimento da Receita
* Crescimento do Lucro

Objetivo:

Identificar empresas em aceleração operacional.

---

### Ranking Balanceado

Combina:

* Qualidade
* Crescimento
* Solidez
* Liquidez

Objetivo:

Selecionar empresas com equilíbrio entre qualidade e expansão.

---

## Estrutura do Projeto

```text
B3_FUNDAMENTALISTA_ENGINE/
│
├── main.py
├── requirements.txt
├── README.md
│
├── engine/
│   ├── cvm_data.py
│   ├── b3_data.py
│   ├── indicators.py
│   ├── scoring.py
│   └── report.py
│
└── .github/
    └── workflows/
        └── run_engine.yml
```

---

## Fluxo de Execução

1. Coleta de empresas da B3
2. Download das demonstrações da CVM
3. Consolidação dos fundamentos
4. Cálculo dos indicadores
5. Cálculo dos scores
6. Geração dos rankings
7. Emissão do relatório final

---

## Critérios Utilizados

### Qualidade

* ROE
* ROA
* Margem Líquida
* Alavancagem

### Crescimento

* Receita
* Lucro

### Mercado

* Market Cap
* Liquidez

---

## Objetivo Final

Criar um motor quantitativo profissional para seleção de ações da B3 utilizando exclusivamente dados públicos, auditáveis e reproduzíveis.

O projeto busca fornecer uma metodologia sistemática para identificar empresas de qualidade, crescimento e equilíbrio fundamentalista.
