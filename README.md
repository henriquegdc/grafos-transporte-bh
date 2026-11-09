# Análise de redes de transporte público com grafos

Trabalho prático de Grafos (tema 5): uma ferramenta que lê os dados da rede de ônibus de Belo Horizonte no formato GTFS, monta grafos com estrutura e algoritmos próprios, sem bibliotecas prontas de grafo, e responde perguntas sobre trajetos, tempo de espera e eficiência da rede.

## 1. O problema

A ferramenta responde seis perguntas sobre a rede:

| Pergunta | Feature |
|---|---|
| Qual o trajeto mais rápido de A a B, somando caminhada, espera e viagem? | F-ROTA |
| Quanto tempo se espera, e como isso muda com o horário de saída? | F-ESPERA |
| Qual o trajeto com menos baldeações, e quanto tempo ele custa a mais? | F-BALD |
| Quais paradas são estruturalmente críticas para a rede? | F-MET |
| Quão eficiente é a rede, e quais regiões são mal atendidas? | F-EFI |
| O que acontece quando uma parada ou uma linha sai de operação? | F-RES |

A análise usa horários programados; não é navegação em tempo real. Detalhes em `docs/fontes/REQUISITOS.md`.

## 2. Os dados

GTFS dos ônibus de Belo Horizonte (BHTrans), do portal de dados abertos da PBH, com recorte por região ou por linhas. Uma rede de teste pequena, com respostas conhecidas, fica em `dados/rede-teste/`.

## 3. A modelagem

O mesmo dado vira visões de grafo diferentes, cada uma escolhida pela pergunta que responde:

| Visão | Vértices | Responde |
|---|---|---|
| G_P · paradas | Paradas | Centralidades, eficiência estrutural, falhas |
| G_E · parada × linha | Paradas e plataformas (parada, linha) | Trajeto mais rápido, espera, tempos origem-destino |
| G_L · linhas | Linhas | Mínimo de baldeações |
| G_T · dependente do horário | Paradas, com partidas por aresta | Simulação com quadro de horários |

Justificativa, parâmetros, algoritmos e complexidades em `docs/fontes/modelagem.md`; diagramas UML em `docs/diagramas/`.

## 4. Plano de desenvolvimento

Seis integrantes, cada um dono de uma frente de ponta a ponta. Divisão e tabela de features em `docs/plano-de-desenvolvimento/README.md`; método e calendário em `docs/fontes/plano-de-projeto.md`.

| Período | Datas |
|---|---|
| Fundação e Etapa 1 | 29/10 a 03/11 |
| Features essenciais | 04/11 a 11/11 |
| Features desejáveis; código congelado em 15/11 | 12/11 a 15/11 |
| Relatório, vídeo e entrega | 16/11 a 22/11 |

## 5. Como usar

Requer **Python 3.12** e Git. Comandos a partir da raiz do repositório.

**1. Instalar** (uma vez por clone):

```bash
git clone https://github.com/henriquegdc/grafos-transporte-bh.git
cd grafos-transporte-bh
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Windows (Git Bash):    source .venv/Scripts/activate
# Linux/macOS:           source .venv/bin/activate
pip install -r requirements.txt
```

**2. Ativar o hook de pre-commit** (uma vez por clone, obrigatório):

```bash
git config core.hooksPath .githooks
```

A cada `git commit`, o hook roda `scripts/verificar_imports.py`, que barra biblioteca de grafo
(networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx) e `heapq` em `src/`, e
o `ruff check`. Se algum falhar, o commit não acontece. O hook usa o Python do `.venv` quando
ele existe. Também dá para rodar o hook direto: `sh .githooks/pre-commit`.

**3. Rodar a interface:**

```bash
streamlit run src/transporte/interface/app.py
```

**4. Rodar os testes e o lint:**

```bash
pytest                              # todos os testes (o pyproject.toml já põe src/ no path)
pytest tests/grafo                  # só uma pasta
ruff check                          # lint
python scripts/verificar_imports.py # só a verificação de imports
```

Antes de abrir um PR: hook e `pytest` verdes, e o resumo da saída do pytest na descrição.
NetworkX só pode aparecer em `tests/`, para comparar resultados, e em `benchmarks/`.

## 6. Documentação

- `docs/GUIA.md`: como a ferramenta funciona e por quê, e o registro de decisões.
- `docs/fontes/`: requisitos, modelagem e plano de projeto.
- `docs/plano-de-desenvolvimento/features/`: um arquivo por feature, com estado e próximo passo.
