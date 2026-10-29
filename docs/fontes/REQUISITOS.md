# REQUISITOS · Análise de redes de transporte público

**Versão:** 0.1, rascunho em revisão; baseline em 03/11/2026 · **Integrador:** Henrique

> Fonte de verdade sobre o que a ferramenta faz. Em conflito com qualquer outro documento, este vence.
> Depois da baseline, muda só por decisão registrada em `docs/GUIA.md` §8.
> A numeração das seções segue `docs/fontes/plano-de-projeto.md`, para que as referências cruzadas continuem válidas.

### 3.1 O problema

O tema 5 pede a "construção de grafos baseados em linhas de ônibus, metrô ou trem, com simulação de trajetos, tempo de espera e eficiência". As três expressões viram os blocos de requisitos: **trajetos** (F-ROTA e F-BALD), **tempo de espera** (F-ESPERA) e **eficiência** (F-EFI e F-RES). A análise estrutural da rede (F-MET) completa o que se espera de uma ferramenta de análise.

A ferramenta analisa e simula sobre horários programados. Não é um aplicativo de navegação em tempo real.

### 3.1.1 Perguntas que a ferramenta responde

| Pergunta que a ferramenta responde | Feature | Dono |
|---|---|---|
| Qual o trajeto mais rápido de A a B, somando caminhada, espera e viagem? | F-ROTA | Henrique |
| Quanto tempo se espera, e como isso muda com o horário de saída? | F-ESPERA | Miguel |
| Qual o trajeto com menos baldeações, e quanto tempo ele custa a mais? | F-BALD | Rafael |
| Quais paradas são estruturalmente críticas para a rede? | F-MET | Thiago |
| Quão eficiente é a rede, e quais regiões são mal atendidas? | F-EFI | Arthur |
| O que acontece quando uma parada ou uma linha sai de operação? | F-RES | Caio |

### 5.1 Requisitos funcionais

Prioridade: **E** essencial, **D** desejável, **O** opcional.

**Dados (DAD)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-DAD-01 | Ler um feed GTFS (paradas, linhas, viagens, horários, calendário) e convertê-lo no modelo normalizado | E | P0-DADOS |
| RF-DAD-02 | Validar o feed e relatar inconsistências (parada sem coordenada, horário inválido, viagem sem paradas) | E | P0-DADOS |
| RF-DAD-03 | Recortar a rede por região (retângulo de coordenadas) ou por conjunto de linhas | E | P0-DADOS |
| RF-DAD-04 | Fornecer uma rede de teste pequena, em formato GTFS, com respostas conhecidas | E | P0-DADOS |
| RF-DAD-05 | Gerar redes sintéticas de tamanho crescente para o estudo de escala | O | F-AVAL-OPC |

**Grafo e modelagem (GRF)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-GRF-01 | Estrutura própria de grafo dirigido e ponderado, com lista de adjacência | E | P0-GRAFO |
| RF-GRF-02 | BFS e Dijkstra genéricos, com reconstrução de caminho | E | P0-GRAFO |
| RF-GRF-03 | Desativar e reativar vértices e arestas sem reconstruir o grafo | E | P0-GRAFO |
| RF-GRF-04 | Construir a visão G_P (paradas) a partir do modelo normalizado | E | P0-MODELO |
| RF-GRF-05 | Construir a visão G_E (parada × linha) com arestas de embarque, viagem, desembarque e caminhada | E | P0-MODELO |
| RF-GRF-06 | Construir a visão G_L (linhas) | E | F-BALD |
| RF-GRF-07 | Salvar e carregar grafos construídos, para não reprocessar o GTFS a cada execução | D | P0-MODELO |
| RF-GRF-08 | Fila de prioridade própria (heap binário de mínimo) usada pelos algoritmos de caminho mínimo | E | P0-GRAFO |

**Trajetos (ROT)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-ROT-01 | Calcular o trajeto mais rápido entre duas paradas, somando caminhada, espera, viagem e baldeações | E | F-ROTA |
| RF-ROT-02 | Mostrar o trajeto no mapa, por trecho (a pé, espera, linha usada), com os tempos | E | F-ROTA |
| RF-ROT-03 | Escolher origem e destino no mapa ou por coordenadas, ligando cada ponto à parada mais próxima | D | F-ROTA-2 |
| RF-ROT-04 | Calcular o trajeto com A* e comparar com o Dijkstra (vértices expandidos e tempo) | D | F-ROTA-2 |
| RF-ROT-05 | Listar k trajetos alternativos (Yen) | O | F-ROTA-OPC |

**Espera (ESP)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-ESP-01 | Estimar o intervalo entre partidas de cada linha por faixa horária, a partir dos horários ou do `frequencies.txt` | E | F-ESPERA |
| RF-ESP-02 | Calcular a espera esperada de cada embarque e aplicá-la às arestas de embarque de G_E | E | F-ESPERA |
| RF-ESP-03 | Simular um trajeto para um horário de saída, decompondo o tempo total em caminhada, espera e viagem | E | F-ESPERA |
| RF-ESP-04 | Simular o trajeto com o quadro de horários (G_T, chegada mais cedo) | D | F-ESPERA-2 |
| RF-ESP-05 | Sortear horários de saída (Monte Carlo) e mostrar a distribuição do tempo total e da parcela de espera | D | F-ESPERA-2 |
| RF-ESP-06 | Alterar o intervalo de uma linha e mostrar o efeito na espera e nos trajetos | O | F-ESPERA-OPC |

**Baldeações (BAL)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-BAL-01 | Calcular o trajeto com o menor número de baldeações entre duas paradas | E | F-BALD |
| RF-BAL-02 | Mostrar a sequência de linhas e as paradas de troca no mapa | E | F-BALD |
| RF-BAL-03 | Comparar o trajeto de menos baldeações com o mais rápido: tempo a mais contra baldeações evitadas | D | F-BALD-2 |
| RF-BAL-04 | Listar os trajetos não dominados em tempo e baldeações | O | F-BALD-OPC |

**Centralidades (MET)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-MET-01 | Calcular o grau de entrada e de saída de cada parada e a distribuição de graus | E | F-MET |
| RF-MET-02 | Calcular a intermediação (Brandes) de cada parada | E | F-MET |
| RF-MET-03 | Mostrar o ranking das paradas mais centrais e um mapa de calor | E | F-MET |
| RF-MET-04 | Calcular a proximidade (closeness) de cada parada | D | F-MET-2 |
| RF-MET-05 | Calcular a intermediação por amostragem e medir o erro contra a exata | D | F-MET-2 |
| RF-MET-06 | Detectar comunidades por propagação de rótulos | O | F-MET-OPC |

**Eficiência (EFI)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-EFI-01 | Calcular a eficiência global da rede (média de 1/d entre pares) | E | F-EFI |
| RF-EFI-02 | Calcular o tempo médio de viagem entre pares origem-destino sorteados | E | F-EFI |
| RF-EFI-03 | Mostrar isócronas: paradas alcançáveis a partir de uma origem em até T minutos | D | F-EFI-2 |
| RF-EFI-04 | Calcular o índice de desvio de cada par (tempo ou distância na rede dividido pela distância em linha reta) | D | F-EFI-2 |
| RF-EFI-05 | Comparar os indicadores entre faixas horárias | O | F-EFI-OPC |

**Falhas (RES)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-RES-01 | Simular a remoção de uma parada, de um trecho ou de uma linha | E | F-RES |
| RF-RES-02 | Calcular as componentes fortemente conexas antes e depois da falha e listar as paradas isoladas | E | F-RES |
| RF-RES-03 | Calcular a perda de eficiência causada pela falha | E | F-RES |
| RF-RES-04 | Ordenar paradas e linhas pela perda de eficiência que causam | D | F-RES-2 |
| RF-RES-05 | Simular falhas múltiplas e em sequência | O | F-RES-OPC |

**Interface (UI)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-UI-01 | Aplicação gráfica com mapa da rede e navegação por páginas | E | P0-UI |
| RF-UI-02 | Carregar o conjunto de dados e mostrar o resumo da rede | E | P0-UI |
| RF-UI-03 | Componente de mapa reutilizável para paradas, caminhos e mapas de calor | E | P0-UI |

**Avaliação (AVA)**

| ID | Requisito | Pri | Feature |
|---|---|---|---|
| RF-AVA-01 | Função de medição de tempo (média e desvio de N execuções) usada por todas as features na rede real | E | P0-AVAL |
| RF-AVA-02 | Tabela consolidada com a complexidade teórica e o tempo medido de cada algoritmo, para o relatório | E | F-AVAL |
| RF-AVA-03 | Comparar o tempo dos nossos algoritmos com os equivalentes do NetworkX no mesmo grafo | O | F-AVAL-OPC |
| RF-AVA-04 | Gerar os gráficos de complexidade empírica (tempo × tamanho, log-log) | O | F-AVAL-OPC |
| RF-AVA-05 | Página "Desempenho" na interface | O | F-AVAL-OPC |

### 5.2 Requisitos não funcionais

| ID | Requisito | Como se verifica | Responsável |
|---|---|---|---|
| RNF-01 | Nenhum módulo em `src/` importa biblioteca de grafo (networkx, igraph, graph_tool, rustworkx, scipy.sparse.csgraph, osmnx) | Hook de pre-commit e revisão do PR; Caio roda o script de novo em cada fechamento | P0-REPO |
| RNF-02 | A `main` só recebe PR revisado e aprovado por outro integrante, com hook e pytest verdes | Proteção de branch no GitHub e template de PR | P0-REPO |
| RNF-03 | Todo algoritmo tem testes de corretude com gabarito à mão, inclusive casos de borda | Revisão do PR e DoD | Todas as features |
| RNF-04 | Toda função pública tem docstring com o que faz, entradas, saída, casos de borda e complexidade de tempo e de espaço | Revisão do PR | Todas as features |
| RNF-05 | A consulta de trajeto responde em até X segundos na rede escolhida; X fixado em 03/11, depois da primeira medição | Tempo medido | F-ROTA |
| RNF-06 | Métricas de todos os pares aceitam amostragem com tamanho configurável e informam o erro | Teste e tempo medido | F-MET, F-EFI |
| RNF-07 | Reprodutibilidade: versões fixadas, dataset com data e origem registradas, script de download, sementes fixas | README | P0-REPO, P0-DADOS |
| RNF-08 | A interface sobe com um único comando, descrito no README | Teste manual no fechamento | P0-UI |
| RNF-09 | Toda feature tem "Como funciona e por quê" e perguntas de verificação incorporadas ao `docs/GUIA.md` | Sessões de explicação cruzada | Todas as features; Caio integra |

**Fora de escopo:** dados em tempo real, demanda real de passageiros, capacidade dos veículos, roteamento por ruas (a caminhada é em linha reta), aplicativo móvel.

## Timeline

### Criação 29/10/2026: gerado a partir do plano de desenvolvimento aprovado pelo grupo.
